"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { apiClient } from "@/lib/api-client";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "@/lib/auth/token-storages";

export interface CurrentUser {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
}

async function fetchCurrentUser(): Promise<CurrentUser> {
  const { data } = await apiClient.get<CurrentUser>("/api/v1/auth/me");
  return data;
}

export function useAuth() {
  const queryClient = useQueryClient();
  const router = useRouter();

  const userQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: fetchCurrentUser,
    enabled: !!getAccessToken(),
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const { data } = await apiClient.post("/api/v1/auth/login", payload);
      return data as { access_token: string; refresh_token: string };
    },
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      router.push("/");
    },
  });

  const registerMutation = useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const { data } = await apiClient.post("/api/v1/auth/register", payload);
      return data;
    },
  });

  const logout = async () => {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      await apiClient
        .post("/api/v1/auth/logout", { refresh_token: refreshToken })
        .catch(() => {});
    }
    clearTokens();
    queryClient.setQueryData(["auth", "me"], null);
    router.push("/login");
  };

  return {
    user: userQuery.data,
    isLoading: userQuery.isLoading,
    isAuthenticated: !!userQuery.data,
    login: loginMutation.mutateAsync,
    loginError: loginMutation.error,
    isLoggingIn: loginMutation.isPending,
    register: registerMutation.mutateAsync,
    registerError: registerMutation.error,
    isRegistering: registerMutation.isPending,
    logout,
  };
}
