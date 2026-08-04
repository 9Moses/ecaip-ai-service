import axios from "axios";

import { env } from "@/lib/env";
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "@/lib/auth/token-storages";

export const apiClient = axios.create({
  baseURL: env.NEXT_PUBLIC_API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and it's not a retry, try to refresh token
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== "/api/v1/auth/refresh" &&
      originalRequest.url !== "/api/v1/auth/login"
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        isRefreshing = false;
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        // Must use raw axios to avoid infinite loops with interceptors
        const { data } = await axios.post(
          `${env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/refresh`,
          {
            refresh_token: refreshToken,
          }
        );

        const newAccessToken = data.access_token;
        const newRefreshToken = data.refresh_token;

        setTokens(newAccessToken, newRefreshToken);
        processQueue(null, newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (err) {
        processQueue(err, null);
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
