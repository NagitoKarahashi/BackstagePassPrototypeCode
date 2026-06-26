'use client';

import { apiClient } from './client';
import type { EventItem } from '@/lib/types';

export function listEvents(params?: Record<string, string | number | boolean | undefined | null>) {
  return apiClient.get<{ items: EventItem[]; total: number; limit: number; offset: number }>('/events', params);
}

export function getEventById(eventId: string) {
  return apiClient.get<EventItem>(`/events/${eventId}`);
}

export function getHotNearYou(city?: string) {
  return apiClient.get<EventItem[]>('/events/hot-near-you', { city, limit: 6 });
}

export function getRecommended(userId: string) {
  return apiClient.get<EventItem[]>('/events/recommended', { user_id: userId, limit: 6 });
}
