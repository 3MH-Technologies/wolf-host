"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  useEffect(() => {
    const token = localStorage.getItem("wolfhost_access_token");
    router.push(token ? "/dashboard" : "/login");
  }, [router]);
  return null;
}
