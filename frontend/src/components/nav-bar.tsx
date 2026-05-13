"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useLogout, useMe } from "@/hooks/use-auth";

export function NavBar() {
  const me = useMe();
  const logout = useLogout();

  return (
    <header className="border-b">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
        <Link href="/buy" className="font-semibold">
          Daraja Water
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/buy" className="hover:underline">
            Buy
          </Link>
          <Link href="/meters" className="hover:underline">
            Meters
          </Link>
          <Link href="/transactions" className="hover:underline">
            History
          </Link>
          <span className="text-muted-foreground">{me.data?.phone_number ?? ""}</span>
          <Button
            variant="outline"
            size="sm"
            disabled={logout.isPending}
            onClick={() => logout.mutate()}
          >
            Sign out
          </Button>
        </nav>
      </div>
    </header>
  );
}
