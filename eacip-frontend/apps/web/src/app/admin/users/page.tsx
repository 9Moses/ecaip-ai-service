"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";

const ROLES = [
  "Super Admin",
  "Admin",
  "Claims Manager",
  "Underwriter",
  "Fraud Analyst",
  "BI Analyst",
  "Employee",
];

interface UserRow {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
}

function AdminUsersContent() {
  const queryClient = useQueryClient();

  const usersQuery = useQuery({
    queryKey: ["admin", "users"],
    queryFn: async () => {
      const { data } = await apiClient.get<UserRow[]>("/api/v1/users");
      return data;
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: async ({
      userId,
      roleName,
    }: {
      userId: string;
      roleName: string;
    }) => {
      const { data } = await apiClient.patch(`/api/v1/users/${userId}/role`, {
        role_name: roleName,
      });
      return data;
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  });

  return (
    <>
      <TopNav />
      <main className="mx-auto max-w-3xl p-6">
        <Card>
          <CardHeader>
            <CardTitle>User & Role Management</CardTitle>
          </CardHeader>
          <CardContent>
            {usersQuery.isLoading && (
              <p className="text-muted-foreground text-sm">Loading users…</p>
            )}
            <div className="flex flex-col divide-y">
              {usersQuery.data?.map((u) => (
                <div
                  key={u.id}
                  className="flex items-center justify-between py-3"
                >
                  <div>
                    <p className="text-sm font-medium">{u.email}</p>
                    <Badge variant="secondary" className="mt-1">
                      {u.role}
                    </Badge>
                  </div>
                  <select
                    className="rounded-md border px-2 py-1 text-sm"
                    value={u.role}
                    onChange={(e) =>
                      updateRoleMutation.mutate({
                        userId: u.id,
                        roleName: e.target.value,
                      })
                    }
                    disabled={updateRoleMutation.isPending}
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </>
  );
}

export default function AdminUsersPage() {
  return (
    <ProtectedRoute allowedRoles={["Admin", "Super Admin"]}>
      <AdminUsersContent />
    </ProtectedRoute>
  );
}
