import CryptoJS from "crypto-js";

const ACCESS_TOKEN_KEY = "eacip_access_token";
const REFRESH_TOKEN_KEY = "eacip_refresh_token";
const ENCRYPTION_KEY =
  process.env.NEXT_PUBLIC_ENCRYPTION_KEY || "eacip_default_secret_key";

function encryptToken(text: string): string {
  return CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString();
}

function decryptToken(cipherText: string): string | null {
  try {
    const bytes = CryptoJS.AES.decrypt(cipherText, ENCRYPTION_KEY);
    const originalText = bytes.toString(CryptoJS.enc.Utf8);
    return originalText || null;
  } catch (error) {
    console.error("Error decrypting token", error);
    return null;
  }
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  const encrypted = localStorage.getItem(ACCESS_TOKEN_KEY);
  return encrypted ? decryptToken(encrypted) : null;
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  const encrypted = localStorage.getItem(REFRESH_TOKEN_KEY);
  return encrypted ? decryptToken(encrypted) : null;
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, encryptToken(accessToken));
  localStorage.setItem(REFRESH_TOKEN_KEY, encryptToken(refreshToken));
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}
