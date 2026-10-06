"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

import { Button } from "@/components/ui/Button";
import { useAdminAuth } from "@/hooks/useAdminAuth";

const NAV_LINKS = [
  { href: "/admin", label: "Overview", exact: true },
  { href: "/admin/import", label: "New Import", permission: "ingest" as const },
  { href: "/admin/batches", label: "Batches" },
  { href: "/admin/market", label: "Market Data" },
  { href: "/admin/users", label: "Users", permission: "manage_users" as const },
];

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, logout, hasPermission } = useAdminAuth();

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8 lg:flex-row">
      <aside className="lg:w-56 lg:shrink-0">
        <div className="flex items-center justify-between lg:block">
          <Link href="/admin" className="text-lg font-semibold tracking-tight">
            VehicleGrade <span className="text-muted font-normal">Admin</span>
          </Link>
        </div>

        <nav className="mt-8 flex gap-1 overflow-x-auto lg:mt-8 lg:flex-col lg:overflow-visible">
          {NAV_LINKS.filter((link) => !link.permission || hasPermission(link.permission)).map((link) => {
            const isActive = link.exact ? pathname === link.href : pathname?.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  "whitespace-nowrap rounded-xl px-4 py-2.5 text-sm font-medium transition-colors",
                  isActive ? "bg-[var(--accent)]/15 text-[var(--accent)]" : "text-muted hover:bg-white/[0.04] hover:text-foreground"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-8 hidden glass-card rounded-xl p-4 text-sm lg:block">
          <p className="font-medium">{user?.email}</p>
          <p className="mt-1 text-xs text-muted capitalize">{user?.role}</p>
          <Button variant="ghost" className="mt-3 !px-0 text-xs" onClick={() => logout()}>
            Log out
          </Button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
