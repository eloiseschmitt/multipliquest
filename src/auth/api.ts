import type { ApiUser, AuthUser, UserResponse } from "./types";
import { apiUrl } from "../config";

const jsonHeaders = {
  "Content-Type": "application/json"
};

function readCookie(name: string): string {
  const cookies = document.cookie ? document.cookie.split("; ") : [];
  const match = cookies.find((cookie) => cookie.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=").slice(1).join("=")) : "";
}

function mapUser(user: ApiUser): AuthUser {
  return {
    id: user.id,
    username: user.username,
    displayName: user.display_name,
    role: user.role,
    currentLevel: user.current_level,
    totalXp: user.total_xp
  };
}

async function ensureCsrfCookie(): Promise<string> {
  const response = await fetch(apiUrl("/api/auth/csrf/"), {
    method: "GET",
    credentials: "include"
  });
  const data = (await response.json()) as { csrfToken?: string };
  return readCookie("csrftoken") || data.csrfToken || "";
}

async function requestJson<T>(input: RequestInfo | URL, init: RequestInit = {}): Promise<T> {
  const response = await fetch(input, {
    ...init,
    credentials: "include",
    headers: {
      ...jsonHeaders,
      ...init.headers
    }
  });

  if (response.status === 401 || response.status === 403) {
    throw new Error("SESSION_EXPIRED");
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(payload.detail ?? "Une erreur est survenue.");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function mutatingRequest<T>(input: RequestInfo | URL, init: RequestInit = {}): Promise<T> {
  const csrfToken = readCookie("csrftoken") || (await ensureCsrfCookie());
  return requestJson<T>(input, {
    ...init,
    headers: {
      "X-CSRFToken": csrfToken,
      ...init.headers
    }
  });
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const data = await requestJson<UserResponse>(apiUrl("/api/auth/me/"));
  return mapUser(data.user);
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const data = await mutatingRequest<UserResponse>(apiUrl("/api/auth/login/"), {
    method: "POST",
    body: JSON.stringify({ username, password })
  });
  return mapUser(data.user);
}

export async function logout(): Promise<void> {
  await mutatingRequest<void>(apiUrl("/api/auth/logout/"), {
    method: "POST",
    body: JSON.stringify({})
  }).catch((error: unknown) => {
    if (error instanceof Error && error.message === "SESSION_EXPIRED") {
      return;
    }
    throw error;
  });
}
