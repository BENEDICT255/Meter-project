"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getAccessToken } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();
  useEffect(() => {
    if (getAccessToken()) {
      router.replace("/buy");
    } else {
      router.replace("/login");
    }
  }, [router]);
  return null;
}
