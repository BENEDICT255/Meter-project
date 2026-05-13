"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

import { getAccessToken } from "@/lib/auth";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (getAccessToken()) {
      setReady(true);
    } else {
      router.replace("/login");
    }
  }, [router]);

  if (!ready) return null;
  return <>{children}</>;
}
