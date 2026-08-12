"use client";

import { ReactNode, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAdminAuth } from "@/hooks/useAdminAuth";
import { AdminShell } from "./AdminShell";

const LOGIN_PATH = "/admin/login";

// Route guard for everything under /admin. Session state is in-memory only
// (see useAdminAuth) so there's no async "check for an existing session" -
// status is synchronously known on first render, which is what lets this
// redirect on mount without a loading flash of protected content.
export function AdminGate({ children }: { children: ReactNode }) {
  const { status } = useAdminAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (status !== "authenticated" && pathname !== LOGIN_PATH) {
      router.replace(LOGIN_PATH);
    } else if (status === "authenticated" && pathname === LOGIN_PATH) {
      router.replace("/admin");
    }
  }, [status, pathname, router]);

  if (pathname === LOGIN_PATH) return <>{children}</>;

  if (status !== "authenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-muted">Redirecting to sign in&hellip;</p>
      </div>
    );
  }

  return <AdminShell>{children}</AdminShell>;
}
