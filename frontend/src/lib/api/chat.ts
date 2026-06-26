'use client';

import { apiClient } from './client';

export function listMyChatRooms() {
  return apiClient.get<Record<string, unknown> | Record<string, unknown>[]>('/chat/my-rooms');
}

export function getEventChatRoom(eventUuid: string) {
  return apiClient.get<Record<string, unknown>>(`/chat/events/${eventUuid}/room`);
}

export function getEventMessages(eventUuid: string) {
  return apiClient.get<Record<string, unknown> | Record<string, unknown>[]>(`/chat/events/${eventUuid}/messages`);
}

export type PostEventMessagePayload = {
  content: string;
};

export function postEventMessage(eventUuid: string, payload: PostEventMessagePayload) {
  return apiClient.post(`/chat/events/${eventUuid}/messages`, payload);
}