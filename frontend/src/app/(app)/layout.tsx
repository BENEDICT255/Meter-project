import { ReactNode } from "react";

import { AuthGuard } from "@/components/auth-guard";
import { NavBar } from "@/components/nav-bar";
import { QueryProvider } from "@/lib/query-client";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <AuthGuard>
        <NavBar />
        <main className="mx-auto max-w-4xl p-6">{children}</main>
      </AuthGuard>
    </QueryProvider>
  );
}
