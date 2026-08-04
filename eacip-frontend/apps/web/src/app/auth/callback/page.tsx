"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, Suspense } from "react";

import { setTokens } from "@/lib/auth/token-storages";

function OAuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");

    if (accessToken && refreshToken) {
      setTokens(accessToken, refreshToken);
      router.replace("/");
    } else {
      router.replace("/login?error=oauth_failed");
    }
  }, [searchParams, router]);

  return (
    <main className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Signing you in…</p>
    </main>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center">
          <p className="text-muted-foreground">Loading…</p>
        </main>
      }
    >
      <OAuthCallbackContent />
    </Suspense>
  );
}
