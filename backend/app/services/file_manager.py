import os
import shutil
import zipfile
import aiofiles
from pathlib import Path

from app.core.config import settings

DANGEROUS_EXTENSIONS = {".so", ".dll", ".exe", ".sh", ".bin"}


class FileManagerError(Exception):
    pass


class FileManager:
    def __init__(self, bot_storage_path: str) -> None:
        self.root = Path(bot_storage_path).resolve()

    def _resolve(self, relative_path: str) -> Path:
        target = (self.root / relative_path.lstrip("/")).resolve()
        if self.root not in target.parents and target != self.root:
            raise FileManagerError("path_traversal_denied")
        return target

    def ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, relative_path: str, content: bytes) -> Path:
        target = self._resolve(relative_path)
        if target.suffix.lower() in DANGEROUS_EXTENSIONS:
            raise FileManagerError("extension_not_allowed")
        target.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(target, "wb") as f:
            await f.write(content)
        return target

    def extract_zip(self, zip_path: Path) -> None:
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.namelist():
                member_path = (self.root / member).resolve()
                if self.root not in member_path.parents and member_path != self.root:
                    raise FileManagerError("zip_path_traversal_denied")
            archive.extractall(self.root)
        zip_path.unlink(missing_ok=True)

    def list_dir(self, relative_path: str = "") -> list[dict]:
        target = self._resolve(relative_path)
        if not target.exists():
            return []
        items = []
        for entry in sorted(target.iterdir()):
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size": entry.stat().st_size if entry.is_file() else 0,
                "modified_at": entry.stat().st_mtime,
            })
        return items

    def read_text_file(self, relative_path: str, max_bytes: int = 2_000_000) -> str:
        target = self._resolve(relative_path)
        if target.stat().st_size > max_bytes:
            raise FileManagerError("file_too_large")
        return target.read_text(errors="replace")

    async def write_text_file(self, relative_path: str, content: str) -> None:
        target = self._resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(target, "w") as f:
            await f.write(content)

    def delete(self, relative_path: str) -> None:
        target = self._resolve(relative_path)
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()

    def rename(self, relative_path: str, new_name: str) -> None:
        target = self._resolve(relative_path)
        if "/" in new_name or ".." in new_name:
            raise FileManagerError("invalid_name")
        target.rename(target.parent / new_name)

    def move(self, relative_path: str, new_relative_path: str) -> None:
        source = self._resolve(relative_path)
        destination = self._resolve(new_relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    def copy(self, relative_path: str, new_relative_path: str) -> None:
        source = self._resolve(relative_path)
        destination = self._resolve(new_relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    def get_total_size_mb(self) -> float:
        total = sum(f.stat().st_size for f in self.root.rglob("*") if f.is_file())
        return round(total / 1024 / 1024, 2)

    def detect_requirements(self) -> list[str]:
        req_file = self.root / "requirements.txt"
        if req_file.exists():
            return [line.strip() for line in req_file.read_text().splitlines() if line.strip() and not line.startswith("#")]
        return self._infer_from_imports()

    def _infer_from_imports(self) -> list[str]:
        stdlib_ignore = {"os", "sys", "json", "time", "re", "math", "random", "logging", "asyncio", "typing", "datetime", "pathlib"}
        found = set()
        for py_file in self.root.rglob("*.py"):
            try:
                content = py_file.read_text(errors="ignore")
            except Exception:
                continue
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("import "):
                    module = line.replace("import ", "").split(".")[0].split(" as ")[0].split(",")[0].strip()
                    if module and module not in stdlib_ignore:
                        found.add(module)
                elif line.startswith("from "):
                    module = line.replace("from ", "").split(".")[0].split(" ")[0].strip()
                    if module and module not in stdlib_ignore:
                        found.add(module)
        return sorted(found)
