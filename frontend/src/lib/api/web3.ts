'use client';

import { apiClient } from './client';

export function mintTicket(ticketId: string) {
  return apiClient.post(`/web3/tickets/${ticketId}/mint`, {});
}

export function getWeb3TicketHistory(ticketId: string) {
  return apiClient.get(`/web3/tickets/${ticketId}/history`);
}