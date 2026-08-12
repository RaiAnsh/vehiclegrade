"use client";

import { FormEvent, useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { Table, Tbody, Td, Th, Thead, Tr } from "@/components/ui/Table";
import { useToast } from "@/components/ui/Toast";
import { RequirePermission } from "@/components/admin/RequirePermission";
import { useAdminAuth } from "@/hooks/useAdminAuth";
import { createUser, deactivateUser, listUsers } from "@/lib/adminApi";
import { AdminRole, AdminUser } from "@/lib/adminTypes";

const ROLES: AdminRole[] = ["admin", "reviewer", "analyst"];

export default function UsersPage() {
  const { accessToken, user: currentUser } = useAdminAuth();
  const { showToast } = useToast();
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<AdminRole>("analyst");
  const [creating, setCreating] = useState(false);
  const [pendingDeactivation, setPendingDeactivation] = useState<AdminUser | null>(null);
  const [deactivating, setDeactivating] = useState(false);

  function load() {
    if (!accessToken) return;
    listUsers(accessToken)
      .then((res) => setUsers(res.users))
      .catch((err) => showToast(err.message, "error"));
  }

  useEffect(load, [accessToken]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) return;
    setCreating(true);
    try {
      await createUser(accessToken, { email, password, role });
      showToast(`Created ${email}`, "success");
      setEmail("");
      setPassword("");
      setRole("analyst");
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Couldn't create user", "error");
    } finally {
      setCreating(false);
    }
  }

  async function handleDeactivate() {
    if (!accessToken || !pendingDeactivation) return;
    setDeactivating(true);
    try {
      await deactivateUser(accessToken, pendingDeactivation.id);
      showToast("Deactivated", "success");
      setPendingDeactivation(null);
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Couldn't deactivate user", "error");
    } finally {
      setDeactivating(false);
    }
  }

  return (
    <RequirePermission permission="manage_users">
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Admin users</h1>
      <p className="mt-1 text-sm text-muted">
        Roles: <span className="text-foreground">admin</span> (everything), <span className="text-foreground">reviewer</span> (ingest +
        review), <span className="text-foreground">analyst</span> (read-only).
      </p>

      <Card className="mt-6 p-6">
        <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-4 sm:items-end">
          <div className="sm:col-span-2">
            <label className="mb-1.5 block text-xs font-medium text-muted">Email</label>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted">Password (12+ chars)</label>
            <Input type="password" required minLength={12} value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted">Role</label>
            <Select value={role} onChange={(e) => setRole(e.target.value as AdminRole)}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </Select>
          </div>
          <div className="sm:col-span-4">
            <Button type="submit" disabled={creating}>
              {creating ? "Creating…" : "Create user"}
            </Button>
          </div>
        </form>
      </Card>

      {users && (
        <div className="mt-6">
          <Table>
            <Thead>
              <Tr>
                <Th>Email</Th>
                <Th>Role</Th>
                <Th>Status</Th>
                <Th></Th>
              </Tr>
            </Thead>
            <Tbody>
              {users.map((u) => (
                <Tr key={u.id}>
                  <Td>{u.email}</Td>
                  <Td className="capitalize">{u.role}</Td>
                  <Td>{u.is_active ? "Active" : "Deactivated"}</Td>
                  <Td>
                    {u.is_active && u.id !== currentUser?.id && (
                      <button onClick={() => setPendingDeactivation(u)} className="text-xs text-[var(--avoid)] hover:underline">
                        Deactivate
                      </button>
                    )}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </div>
      )}

      <Modal open={pendingDeactivation !== null} onClose={() => setPendingDeactivation(null)}>
        <h2 className="text-lg font-semibold">Deactivate {pendingDeactivation?.email}?</h2>
        <p className="mt-2 text-sm text-muted">They will no longer be able to sign in. This can be reversed later by re-creating the account.</p>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setPendingDeactivation(null)} disabled={deactivating}>
            Cancel
          </Button>
          <Button variant="secondary" onClick={handleDeactivate} disabled={deactivating}>
            {deactivating ? "Deactivating…" : "Deactivate"}
          </Button>
        </div>
      </Modal>
    </div>
    </RequirePermission>
  );
}
