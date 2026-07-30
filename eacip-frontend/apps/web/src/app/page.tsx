"use client";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/use-auth";

function HomeContent() {
  const { user, logout } = useAuth();

  return (
    <>
      <TopNav />
      <main className="flex min-h-[calc(100vh-73px)] items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Welcome to EACIP</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">
              Signed in as <span className="font-medium">{user?.email}</span> —
              role: <span className="font-medium">{user?.role}</span>
            </p>
            <Button variant="outline" onClick={logout}>
              Log out
            </Button>
          </CardContent>
        </Card>
      </main>
    </>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <HomeContent />
    </ProtectedRoute>
  );
}
