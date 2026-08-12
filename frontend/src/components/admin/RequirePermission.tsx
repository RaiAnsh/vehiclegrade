"use client";

import { ReactNode } from "react";

import { Card } from "@/components/ui/Card";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { AdminPermission } from "@/lib/adminTypes";

// Belt-and-suspenders for pages reachable by direct URL/bookmark even when
// hidden from nav (see AdminShell's NAV_LINKS filtering). The backend
// already 403s the actual mutation regardless - this exists purely so a
// role without the permission sees an explanation instead of a form that
// looks usable but silently fails on submit.
export function RequirePermission({ permission, children }: { permission: AdminPermission; children: ReactNode }) {
  const { hasPermission } = useAdminAuth();

  if (!hasPermission(permission)) {
    return (
      <Card className="p-8 text-center">
        <p className="text-sm font-medium">You don&apos;t have access to this page</p>
        <p className="mt-1 text-sm text-muted">This requires the &ldquo;{permission}&rdquo; permission.</p>
      </Card>
    );
  }

  return <>{children}</>;
}
