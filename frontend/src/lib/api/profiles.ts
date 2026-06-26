'use client';

import { apiClient } from './client';
import type { Profile } from '@/lib/types';

export function getMyProfile() {
  return apiClient.get<Profile>('/profiles/me');
}

export function updateMyProfile(payload: Partial<Profile>) {
  return apiClient.patch<Profile>('/profiles/me', payload);
}

export function updateMyWalletAddress(walletAddress: string) {
  return apiClient.patch('/profiles/me/wallet', {
    wallet_address: walletAddress,
  });
}