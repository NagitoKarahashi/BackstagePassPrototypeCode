'use client';

import { apiClient } from './client';

export function getMeOverview() {
  return apiClient.get<{
    profile: Record<string, unknown>;
    stats: Record<string, number>;
    recent_orders: Record<string, unknown>[];
    recent_tickets: Record<string, unknown>[];
    badges: Record<string, unknown>[];
  }>('/me/overview');
}

export function getMeHistory() {
  return apiClient.get<{ orders: Record<string, unknown>[]; tickets: Record<string, unknown>[] }>('/me/history');
}
