'use client';

import { apiClient } from './client';

export const rewardsApi = {
  overview: () => apiClient.get<Record<string, unknown>>('/rewards/overview'),
  checkinStatus: () => apiClient.get<Record<string, unknown>>('/rewards/checkin-status'),
  checkin: () => apiClient.post<Record<string, unknown>>('/rewards/checkin'),
  missions: () => apiClient.get<{ items: Record<string, unknown>[] }>('/rewards/missions'),
  startMission: (missionId: string) => apiClient.post<Record<string, unknown>>(`/rewards/missions/${missionId}/start`),
  claimMission: (missionId: string) => apiClient.post<Record<string, unknown>>(`/rewards/missions/${missionId}/claim`),
  summary: () => apiClient.get<Record<string, unknown>>('/rewards/summary'),
  ledger: () => apiClient.get<{ items: Record<string, unknown>[] }>('/rewards/ledger'),
  badges: () => apiClient.get<{ items: Record<string, unknown>[] }>('/rewards/badges'),
  leaderboard: () => apiClient.get<{ items: Record<string, unknown>[] }>('/rewards/leaderboard'),
  catalog: () => apiClient.get<{ items: Record<string, unknown>[] }>('/rewards/catalog'),
  redeem: (rewardId: string) => apiClient.post<Record<string, unknown>>(`/rewards/redeem/${rewardId}`),
  myRedemptions: () => apiClient.get<{ items: Record<string, unknown>[] }>('/rewards/my-redemptions'),
};
