"use client";

import { Droplet, Droplets, Gauge, Receipt } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { useLogout, useMe } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/buy", label: "Buy", icon: Droplet },
  { href: "/meters", label: "Meters", icon: Gauge },
  { href: "/transactions", label: "History", icon: Receipt },
] as const;

function isActive(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  if (pathname === href) return true;
  return href !== "/buy" && pathname.startsWith(href);
}

function TopBar() {
  const me = useMe();
  const logout = useLogout();
  const initials = me.data?.phone_number?.slice(-2) ?? "··";

  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 md:px-8 md:py-4">
        <Link href="/buy" className="flex items-center gap-2">
          <Droplets className="size-6 text-primary" />
          <span className="text-lg font-semibold tracking-tight">Daraja Water</span>
        </Link>
        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 sm:flex">
            <div className="flex size-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              {initials}
            </div>
            <span className="text-sm text-muted-foreground">
              {me.data?.phone_number ?? ""}
            </span>
          </div>
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
    </header>
  );
}

function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-56 shrink-0 md:block">
      <nav className="space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="mx-auto flex w-full max-w-7xl gap-1 border-b bg-white px-4 pb-2 pt-1 md:hidden">
      {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      <TopBar />
      <MobileNav />
      <div className="mx-auto flex w-full max-w-7xl gap-8 px-4 py-6 md:px-8 md:py-8">
        <Sidebar />
        <main className="min-h-[calc(100vh-12rem)] flex-1 rounded-2xl bg-muted/40 p-6 md:p-10">
          {children}
        </main>
      </div>
    </div>
  );
}
