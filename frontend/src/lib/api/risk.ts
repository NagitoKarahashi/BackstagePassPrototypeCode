'use client';

import { apiClient } from './client';

export function getMyRiskOverview() {
  return apiClient.get<Record<string, unknown>>('/risk/me');
}