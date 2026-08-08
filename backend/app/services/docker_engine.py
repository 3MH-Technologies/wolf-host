import docker
from docker.errors import NotFound, APIError
from docker.types import Ulimit
import asyncio
from functools import partial

from app.core.config import settings


class DockerEngineError(Exception):
    pass


class DockerEngine:
    def __init__(self) -> None:
        self._client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
        self._ensure_network()

    def _ensure_network(self) -> None:
        try:
            self._client.networks.get(settings.DOCKER_NETWORK_NAME)
        except NotFound:
            self._client.networks.create(
                settings.DOCKER_NETWORK_NAME,
                driver="bridge",
                internal=False,
                options={"com.docker.network.bridge.enable_icc": "true"},
            )

    async def _run_sync(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    def _build_container_config(
        self,
        container_name: str,
        host_bot_path: str,
        entrypoint: str,
        env_vars: dict,
        cpu_limit: float,
        ram_limit_mb: int,
        disk_limit_mb: int,
        process_limit: int,
        network_access: bool,
    ) -> dict:
        return dict(
            image=settings.DOCKER_IMAGE_PYTHON,
            name=container_name,
            command=self._build_command(entrypoint),
            working_dir="/app",
            volumes={host_bot_path: {"bind": "/app", "mode": "rw"}},
            environment={**env_vars, "PYTHONUNBUFFERED": "1"},
            detach=True,
            network=settings.DOCKER_NETWORK_NAME if network_access else "none",
            mem_limit=f"{ram_limit_mb}m",
            memswap_limit=f"{ram_limit_mb}m",
            nano_cpus=int(cpu_limit * 1_000_000_000),
            pids_limit=process_limit,
            storage_opt={"size": f"{disk_limit_mb}m"} if self._supports_storage_opt() else None,
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],
            privileged=False,
            read_only=False,
            user="1000:1000",
            restart_policy={"Name": "unless-stopped"},
            ulimits=[Ulimit(name="nproc", soft=process_limit, hard=process_limit)],
            labels={"managed-by": "wolfhost", "type": "bot"},
        )

    def _supports_storage_opt(self) -> bool:
        try:
            info = self._client.info()
            return info.get("Driver") == "overlay2"
        except Exception:
            return False

    def _build_command(self, entrypoint: str) -> list[str]:
        return [
            "sh",
            "-c",
            (
                "pip install --no-cache-dir --user -r requirements.txt >/proc/1/fd/1 2>/proc/1/fd/2 "
                "|| true; "
                f"python {entrypoint}"
            ),
        ]

    async def create_and_start(
        self,
        container_name: str,
        host_bot_path: str,
        entrypoint: str,
        env_vars: dict,
        cpu_limit: float,
        ram_limit_mb: int,
        disk_limit_mb: int,
        process_limit: int,
        network_access: bool = True,
    ) -> str:
        await self.remove_if_exists(container_name)
        config = self._build_container_config(
            container_name,
            host_bot_path,
            entrypoint,
            env_vars,
            cpu_limit,
            ram_limit_mb,
            disk_limit_mb,
            process_limit,
            network_access,
        )
        config = {k: v for k, v in config.items() if v is not None}
        try:
            container = await self._run_sync(self._client.containers.run, **config)
            return container.id
        except APIError as exc:
            raise DockerEngineError(str(exc)) from exc

    async def stop(self, container_name: str, timeout: int = 10) -> None:
        try:
            container = await self._run_sync(self._client.containers.get, container_name)
            await self._run_sync(container.stop, timeout=timeout)
        except NotFound:
            pass

    async def start(self, container_name: str) -> None:
        try:
            container = await self._run_sync(self._client.containers.get, container_name)
            await self._run_sync(container.start)
        except NotFound as exc:
            raise DockerEngineError("container_not_found") from exc

    async def restart(self, container_name: str, timeout: int = 10) -> None:
        try:
            container = await self._run_sync(self._client.containers.get, container_name)
            await self._run_sync(container.restart, timeout=timeout)
        except NotFound as exc:
            raise DockerEngineError("container_not_found") from exc

    async def remove_if_exists(self, container_name: str) -> None:
        try:
            container = await self._run_sync(self._client.containers.get, container_name)
            await self._run_sync(container.remove, force=True)
        except NotFound:
            pass

    async def get_status(self, container_name: str) -> str:
        try:
            container = await self._run_sync(self._client.containers.get, container_name)
            container.reload()
            return container.status
        except NotFound:
            return "not_found"

    async def get_stats(self, container_name: str) -> dict:
        try:
            container = await self._run_sync(self._client.containers.get, container_name)
            stats = await self._run_sync(container.stats, stream=False)
            return self._parse_stats(stats)
        except NotFound:
            return {}

    def _parse_stats(self, stats: dict) -> dict:
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"].get("system_cpu_usage", 0)
        cpu_percent = 0.0
        if system_delta > 0 and cpu_delta > 0:
            cpu_count = stats["cpu_stats"].get("online_cpus", 1)
            cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
        mem_usage = stats["memory_stats"].get("usage", 0)
        mem_limit = stats["memory_stats"].get("limit", 1)
        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_mb": round(mem_usage / 1024 / 1024, 2),
            "memory_limit_mb": round(mem_limit / 1024 / 1024, 2),
            "memory_percent": round((mem_usage / mem_limit) * 100, 2) if mem_limit else 0,
            "network_rx_bytes": sum(v.get("rx_bytes", 0) for v in stats.get("networks", {}).values()),
            "network_tx_bytes": sum(v.get("tx_bytes", 0) for v in stats.get("networks", {}).values()),
        }

    async def stream_logs(self, container_name: str, tail: int = 200):
        container = await self._run_sync(self._client.containers.get, container_name)
        loop = asyncio.get_running_loop()

        def _generator():
            return container.logs(stream=True, follow=True, tail=tail, timestamps=True)

        gen = await loop.run_in_executor(None, _generator)
        for line in gen:
            yield line.decode(errors="replace")

    async def get_logs(self, container_name: str, tail: int = 500) -> str:
        try:
            container = await self._run_sync(self._client.containers.get, container_name)
            logs = await self._run_sync(container.logs, tail=tail, timestamps=True)
            return logs.decode(errors="replace")
        except NotFound:
            return ""

    async def exec_command(self, container_name: str, command: list[str]) -> dict:
        container = await self._run_sync(self._client.containers.get, container_name)
        result = await self._run_sync(container.exec_run, command, user="1000:1000", demux=True)
        stdout, stderr = result.output
        return {
            "exit_code": result.exit_code,
            "stdout": (stdout or b"").decode(errors="replace"),
            "stderr": (stderr or b"").decode(errors="replace"),
        }


docker_engine = DockerEngine()
