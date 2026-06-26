'use client';

import { getPrivyAccessToken } from '@/lib/auth/privy-token';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

type QueryValue = string | number | boolean | undefined | null;

function normalizeBaseUrl(base: string) {
  return base.endsWith('/') ? base.slice(0, -1) : base;
}

function normalizePath(path: string) {
  return path.startsWith('/') ? path : `/${path}`;
}

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  if (!API_BASE) {
    throw new Error('Missing NEXT_PUBLIC_API_BASE_URL');
  }

  const url = new URL(`${normalizeBaseUrl(API_BASE)}${normalizePath(path)}`);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

function stringifyDetail(value: unknown): string {
  if (typeof value === 'string') return value;
  if (value == null) return '';
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  query?: Record<string, QueryValue>,
  options?: { requireAuth?: boolean }
): Promise<T> {
  const requireAuth = options?.requireAuth ?? true;

  if (!API_BASE) {
    throw new Error('Missing NEXT_PUBLIC_API_BASE_URL');
  }

  const token = await getPrivyAccessToken();

  if (requireAuth && !token) {
    throw new Error('No Privy access token found. Please log in again.');
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    cache: 'no-store',
    credentials: 'include',
  });

  if (!res.ok) {
    let detail = `Request failed: ${res.status}`;

    try {
      const data = await res.json();
      detail =
        stringifyDetail(data?.detail) ||
        stringifyDetail(data?.message) ||
        stringifyDetail(data?.msg) ||
        stringifyDetail(data);
    } catch {
      try {
        detail = await res.text();
      } catch {}
    }

    throw new Error(detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(
    path: string,
    query?: Record<string, QueryValue>,
    options?: { requireAuth?: boolean }
  ) => request<T>('GET', path, undefined, query, options),

  post: <T>(
    path: string,
    body?: unknown,
    query?: Record<string, QueryValue>,
    options?: { requireAuth?: boolean }
  ) => request<T>('POST', path, body, query, options),

  patch: <T>(
    path: string,
    body?: unknown,
    query?: Record<string, QueryValue>,
    options?: { requireAuth?: boolean }
  ) => request<T>('PATCH', path, body, query, options),

  delete: <T>(
    path: string,
    query?: Record<string, QueryValue>,
    options?: { requireAuth?: boolean }
  ) => request<T>('DELETE', path, undefined, query, options),
};