'use client';

import { apiClient } from '@/lib/api/client';

export async function bootstrapProfile() {
  return apiClient.post('/profiles/bootstrap');
}
