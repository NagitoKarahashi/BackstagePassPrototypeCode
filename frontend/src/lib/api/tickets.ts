'use client';

import { apiClient } from './client';
import type {
  TicketDetailResponse,
  TicketHistoryResponse,
  TicketMarketStatusResponse,
  TransferTicketPayload,
} from '@/lib/types';

export function getMyTickets(userId?: string | null) {
  const query =
    userId && userId.trim()
      ? { user_id: userId }
      : undefined;

  return apiClient.get<unknown>('/tickets/my', query);
}

export function getTicketById(ticketId: string) {
  return apiClient.get<TicketDetailResponse>(`/tickets/${ticketId}`);
}

export function getTicketQr(ticketId: string) {
  return apiClient.get<{ ticket_id: string; status: string; qr_payload?: string | null }>(
    `/tickets/${ticketId}/qr`
  );
}

export function getTicketHistory(ticketId: string) {
  return apiClient.get<TicketHistoryResponse>(`/tickets/${ticketId}/history`);
}

export function getTicketMarketStatus(ticketId: string) {
  return apiClient.get<TicketMarketStatusResponse>(`/tickets/${ticketId}/market-status`);
}

export function transferTicket(ticketId: string, payload: TransferTicketPayload) {
  return apiClient.post<Record<string, unknown>>(`/tickets/${ticketId}/transfer`, payload);
}

export function refundTicket(ticketId: string) {
  return apiClient.post<Record<string, unknown>>(`/tickets/${ticketId}/refund`, {});
}