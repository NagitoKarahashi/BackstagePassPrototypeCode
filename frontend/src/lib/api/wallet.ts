'use client';

import { apiClient } from './client';

export function getWalletMe() {
  return apiClient.get('/wallet/me');
}

export function getWalletTickets() {
  return apiClient.get('/wallet/tickets');
}

export function getWalletTicketDetail(ticketId: string) {
  return apiClient.get(`/wallet/tickets/${ticketId}`);
}