'use client';

import { apiClient } from './client';

export type CreateOrderPayload = {
  event_id: string;
  quantity: number;
};

export type OrderResponse = {
  order_id?: string;
  id?: string;
  user_id?: string;
  event_id?: string;
  event_uuid?: string;
  qty?: number;
  total_amount?: number;
  status?: string;
  risk?: {
    risk_score?: number;
    risk_level?: string;
    risk_type?: string;
    reasons?: string[];
    recommended_action?: string;
    review_required?: boolean;
  };
  [key: string]: unknown;
};

export function createOrder(payload: CreateOrderPayload) {
  return apiClient.post<OrderResponse>('/orders/create', payload);
}

export function payOrder(orderId: string) {
  return apiClient.post<OrderResponse>(`/orders/${orderId}/pay`, {});
}

export function cancelOrder(orderId: string) {
  return apiClient.post<OrderResponse>(`/orders/${orderId}/cancel`, {});
}