'use client';

import { apiClient } from './client';
import type {
  CreateListingPayload,
  MarketplaceListing,
  MarketplaceListingListResponse,
} from '@/lib/types';

export function getMarketplaceListings() {
  return apiClient.get<MarketplaceListingListResponse>('/market/listings');
}

export function getMyMarketplaceListings() {
  return apiClient.get<MarketplaceListingListResponse>('/market/my-listings');
}

export function getMarketplaceListingById(listingId: string) {
  return apiClient.get<{ listing: MarketplaceListing }>(`/market/listings/${listingId}`);
}

export function createListing(payload: CreateListingPayload) {
  return apiClient.post<{
    status: string;
    listing?: MarketplaceListing;
    risk?: Record<string, unknown>;
  }>('/market/listings', payload);
}

export function buyListing(listingId: string) {
  return apiClient.post(`/market/listings/${listingId}/buy`, {});
}

export function cancelListing(listingId: string) {
  return apiClient.post(`/market/listings/${listingId}/cancel`, {});
}