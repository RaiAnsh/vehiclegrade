import { ReactNode } from "react";

import { AdminAuthProvider } from "@/hooks/useAdminAuth";
import { ToastProvider } from "@/components/ui/Toast";
import { AdminGate } from "@/components/admin/AdminGate";

export const metadata = {
  title: "Admin — VehicleGrade",
  robots: { index: false, follow: false },
};

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminAuthProvider>
      <ToastProvider>
        <AdminGate>{children}</AdminGate>
      </ToastProvider>
    </AdminAuthProvider>
  );
}
