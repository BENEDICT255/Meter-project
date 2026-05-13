"use client";

import { Droplets } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { useLogout, useMe } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/buy", label: "Buy" },
  { href: "/meters", label: "Meters" },
  { href: "/transactions", label: "History" },
] as const;

export function NavBar() {
  const me = useMe();
  const logout = useLogout();
  const pathname = usePathname();

  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/buy" className="flex items-center gap-2">
          <Droplets className="size-6 text-primary" />
          <span className="text-lg font-semibold tracking-tight">Daraja Water</span>
        </Link>
        <nav className="hidden items-center gap-1 md:flex">
          {LINKS.map((link) => {
            const active =
              pathname === link.href ||
              (link.href !== "/buy" && pathname?.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-muted-foreground sm:inline">
            {me.data?.phone_number ?? ""}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={logout.isPending}
            onClick={() => logout.mutate()}
          >
            Sign out
          </Button>
        </div>
      </div>
      <nav className="flex items-center gap-1 border-t px-6 py-2 md:hidden">
        {LINKS.map((link) => {
          const active =
            pathname === link.href ||
            (link.href !== "/buy" && pathname?.startsWith(link.href));
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
