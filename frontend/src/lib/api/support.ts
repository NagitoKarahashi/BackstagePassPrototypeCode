'use client';

import { apiClient } from './client';

export type SupportEnquiryPayload = {
  category: 'general' | 'refund' | 'transfer' | 'ticket' | 'event' | 'risk' | 'account' | 'technical';
  subject: string;
  message: string;
  order_id?: string | null;
  event_uuid?: string | null;
  ticket_id?: string | null;
  source?: 'manual' | 'chatbot' | 'refund_flow' | 'transfer_flow' | 'risk_flow';
};

export function createSupportEnquiry(payload: SupportEnquiryPayload) {
  return apiClient.post<Record<string, unknown>>('/support-enquiries', payload);
}

export function getMySupportEnquiries(limit = 20, offset = 0) {
  return apiClient.get<Record<string, unknown>>(`/support-enquiries?limit=${limit}&offset=${offset}`);
}