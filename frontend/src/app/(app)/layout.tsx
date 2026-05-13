import { ReactNode } from "react";

import { AuthGuard } from "@/components/auth-guard";
import { NavBar } from "@/components/nav-bar";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <NavBar />
      <main className="mx-auto max-w-4xl p-6">{children}</main>
    </AuthGuard>
  );
}
