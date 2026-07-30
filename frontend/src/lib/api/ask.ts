'use client';

import { apiClient } from './client';

export type AssistantEvent = {
  id: string;
  event_code?: string | null;
  title: string;
  artist?: string | null;
  genre?: string | null;
  city?: string | null;
  country?: string | null;
  venue_name?: string | null;
  description?: string | null;
  price?: number | null;
  stock_left?: number | null;
  start_time?: string | null;
  poster_url?: string | null;
  status?: string | null;
};

export type PurchaseConfirmationAction = {
  type: 'purchase_confirmation';
  requires_confirmation: true;
  event_id: string;
  event_title: string;
  quantity: number;
  unit_price?: number | null;
  estimated_total?: number | null;
  payment_mode: 'mock';
  label?: string;
};

export type PurchaseSelectionAction = {
  type: 'purchase_selection';
  requires_confirmation: true;
  quantity: number;
  event_ids: string[];
  payment_mode: 'mock';
  label?: string;
};

export type AssistantAction =
  | PurchaseConfirmationAction
  | PurchaseSelectionAction;

export type AskAssistantResponse = {
  answer: string;
  citations?: string[];
  scores?: number[];
  intent: string;
  lang: 'en' | 'zh';
  risk_level?: string | null;
  risk_score?: number | null;
  risk_type?: string | null;
  risk_reasons?: string[];
  recommended_action?: string | null;
  answer_mode?: string;
  events?: AssistantEvent[];
  event?: AssistantEvent;
  action?: AssistantAction | null;
  order?: Record<string, unknown> | null;
  payment?: unknown;
  next_actions?: string[];
};

export function askAssistant(
  question: string,
  context?: Record<string, unknown>
) {
  return apiClient.post<AskAssistantResponse>('/ask', {
    question,
    context,
  });
}

export function confirmAssistantPurchase(payload: {
  event_id: string;
  quantity: number;
  lang: 'en' | 'zh';
}) {
  return apiClient.post<AskAssistantResponse>(
    '/ask/purchase/confirm',
    payload
  );
}
