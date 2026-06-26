'use client';

import { apiClient } from './client';

export function getFollowedArtists() {
  return apiClient.get('/artists/follows');
}

export function followArtist(artistId: string) {
  return apiClient.post(`/artists/${artistId}/follow`);
}

export function unfollowArtist(artistId: string) {
  return apiClient.delete(`/artists/${artistId}/follow`);
}