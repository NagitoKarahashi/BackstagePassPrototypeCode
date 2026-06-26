'use client';

import { apiClient } from './client';

export function getMyNotifications() {
  return apiClient.get<{ items: Record<string, unknown>[] }>('/notifications/my');
}