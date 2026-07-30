'use client';

import Link from 'next/link';
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react';
import { usePathname } from 'next/navigation';
import {
  askAssistant,
  confirmAssistantPurchase,
  type AskAssistantResponse,
  type AssistantEvent,
  type PurchaseConfirmationAction,
} from '@/lib/api/ask';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  response?: AskAssistantResponse;
  error?: boolean;
};

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function getEvents(response?: AskAssistantResponse): AssistantEvent[] {
  if (!response) return [];
  if (response.events?.length) return response.events;
  return response.event ? [response.event] : [];
}

function getOrderId(response?: AskAssistantResponse): string {
  const order = response?.order;
  if (!order) return '';
  const value = order.order_id || order.id;
  return typeof value === 'string' ? value : '';
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—';
  return String(value);
}

function formatDate(value?: string | null): string {
  if (!value) return 'TBA';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function EventResultCard({
  event,
  selectionQuantity,
  onSelect,
}: {
  event: AssistantEvent;
  selectionQuantity?: number;
  onSelect: (event: AssistantEvent, quantity: number) => void;
}) {
  const location = [event.venue_name, event.city].filter(Boolean).join(' · ');

  return (
    <div
      style={{
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 16,
        overflow: 'hidden',
        background: 'rgba(255,255,255,0.035)',
      }}
    >
      {event.poster_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={event.poster_url}
          alt={event.title}
          style={{
            width: '100%',
            height: 120,
            objectFit: 'cover',
            display: 'block',
          }}
        />
      ) : null}

      <div style={{ padding: 12 }}>
        <div style={{ fontWeight: 800, lineHeight: 1.35 }}>{event.title}</div>
        <div className="small" style={{ opacity: 0.72, marginTop: 5 }}>
          {[event.artist, event.genre].filter(Boolean).join(' · ') || 'Artist TBA'}
        </div>
        <div className="small" style={{ opacity: 0.72, marginTop: 4 }}>
          {formatDate(event.start_time)}
        </div>
        <div className="small" style={{ opacity: 0.72, marginTop: 4 }}>
          {location || 'Venue TBA'}
        </div>
        <div
          className="small"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: 12,
            marginTop: 8,
          }}
        >
          <span>Price: {formatValue(event.price)}</span>
          <span>Left: {formatValue(event.stock_left)}</span>
        </div>

        {event.description ? (
          <div
            className="small"
            style={{
              opacity: 0.82,
              lineHeight: 1.55,
              marginTop: 9,
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {event.description}
          </div>
        ) : null}

        <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
          <Link
            className="btn ghost"
            href={`/events/${event.id}`}
            style={{ padding: '7px 10px', minWidth: 'unset' }}
          >
            View
          </Link>
          {event.artist ? (
            <Link
              className="btn ghost"
              href={`/artists/${encodeURIComponent(event.artist)}`}
              style={{ padding: '7px 10px', minWidth: 'unset' }}
            >
              Artist
            </Link>
          ) : null}
          {selectionQuantity ? (
            <button
              type="button"
              className="btn secondary"
              onClick={() => onSelect(event, selectionQuantity)}
              style={{ padding: '7px 10px', minWidth: 'unset' }}
            >
              Choose
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function PurchaseConfirmation({
  action,
  lang,
  busy,
  completed,
  onConfirm,
}: {
  action: PurchaseConfirmationAction;
  lang: 'en' | 'zh';
  busy: boolean;
  completed: boolean;
  onConfirm: (action: PurchaseConfirmationAction) => void;
}) {
  const isZh = lang === 'zh';
  return (
    <div
      style={{
        marginTop: 10,
        border: '1px solid rgba(120,160,255,0.42)',
        background: 'rgba(80,110,255,0.1)',
        borderRadius: 16,
        padding: 12,
      }}
    >
      <div style={{ fontWeight: 800 }}>
        {isZh ? '模拟购票确认' : 'Mock purchase confirmation'}
      </div>
      <div className="small" style={{ lineHeight: 1.65, marginTop: 7 }}>
        <div>{isZh ? '活动' : 'Event'}: {action.event_title}</div>
        <div>{isZh ? '数量' : 'Quantity'}: {action.quantity}</div>
        <div>{isZh ? '单价' : 'Unit price'}: {formatValue(action.unit_price)}</div>
        <div>{isZh ? '预计总价' : 'Estimated total'}: {formatValue(action.estimated_total)}</div>
      </div>
      <div className="small" style={{ opacity: 0.7, lineHeight: 1.5, marginTop: 8 }}>
        {isZh
          ? '这里调用原型系统的模拟支付 API，不会向外部支付渠道扣款，但会在 Supabase 中创建订单和演示票券记录。'
          : 'This uses the prototype payment API. No external payment provider is charged, but an order and demo ticket records are created in Supabase.'}
      </div>
      <button
        type="button"
        className="btn"
        disabled={busy || completed}
        onClick={() => onConfirm(action)}
        style={{ width: '100%', marginTop: 10 }}
      >
        {completed
          ? isZh
            ? '购票请求已提交'
            : 'Purchase already submitted'
          : busy
          ? isZh
            ? '正在创建订单…'
            : 'Creating order...'
          : action.label || 'Confirm mock purchase'}
      </button>
    </div>
  );
}

export default function AskPanel() {
  const pathname = usePathname();
  const eventId = useMemo(() => {
    const match = pathname.match(/^\/events\/([^/]+)$/);
    return match?.[1] ? decodeURIComponent(match[1]) : '';
  }, [pathname]);

  const [collapsed, setCollapsed] = useState(
    pathname.startsWith('/chat') || pathname.startsWith('/risk')
  );
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'assistant-welcome',
      role: 'assistant',
      text:
        'I can search live events, introduce artists from current event records, explain ticket policies, and guide a mock ticket purchase.',
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [busyActionId, setBusyActionId] = useState('');
  const [completedActionIds, setCompletedActionIds] = useState<Set<string>>(
    () => new Set()
  );
  const messageListRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!collapsed && messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages, collapsed, loading]);

  const quickPrompts = eventId
    ? [
        'Tell me about this event',
        'Tell me about this artist',
        'Buy 1 ticket for this event',
      ]
    : [
        'Show upcoming events',
        'Any events in Hong Kong?',
        'Introduce Luna Echo',
      ];

  function appendMessage(message: ChatMessage) {
    setMessages((previous) => [...previous, message]);
  }

  async function sendQuestion(value?: string) {
    const text = (value ?? question).trim();
    if (!text || loading) return;

    appendMessage({
      id: makeId('user'),
      role: 'user',
      text,
    });
    setQuestion('');
    setLoading(true);

    try {
      const context: Record<string, unknown> = {
        current_path: pathname,
      };
      if (eventId) context.current_event_id = eventId;

      const response = await askAssistant(text, context);
      appendMessage({
        id: makeId('assistant'),
        role: 'assistant',
        text: response.answer,
        response,
      });
    } catch (error) {
      appendMessage({
        id: makeId('assistant-error'),
        role: 'assistant',
        text: error instanceof Error ? error.message : 'Assistant request failed',
        error: true,
      });
    } finally {
      setLoading(false);
    }
  }

  function handleTextareaKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendQuestion();
    }
  }

  function handleSelectEvent(
    event: AssistantEvent,
    quantity: number,
    lang: 'en' | 'zh'
  ) {
    const estimatedTotal =
      typeof event.price === 'number' ? event.price * quantity : null;
    const isZh = lang === 'zh';
    const response: AskAssistantResponse = {
      answer: isZh
        ? `你选择了“${event.title}”。请在提交模拟购票前核对下面的信息。`
        : `You selected “${event.title}”. Check the details below before submitting the mock purchase.`,
      answer_mode: 'purchase_confirmation',
      intent: 'purchase',
      lang,
      events: [event],
      action: {
        type: 'purchase_confirmation',
        requires_confirmation: true,
        event_id: event.id,
        event_title: event.title,
        quantity,
        unit_price: event.price,
        estimated_total: estimatedTotal,
        payment_mode: 'mock',
        label: isZh ? '确认模拟购票' : 'Confirm mock purchase',
      },
    };

    appendMessage({
      id: makeId('assistant-selection'),
      role: 'assistant',
      text: response.answer,
      response,
    });
  }

  async function handleConfirmPurchase(
    messageId: string,
    action: PurchaseConfirmationAction,
    lang: 'en' | 'zh'
  ) {
    if (busyActionId || completedActionIds.has(messageId)) return;
    setBusyActionId(messageId);

    try {
      const response = await confirmAssistantPurchase({
        event_id: action.event_id,
        quantity: action.quantity,
        lang,
      });
      setCompletedActionIds((previous) => {
        const next = new Set(previous);
        next.add(messageId);
        return next;
      });
      appendMessage({
        id: makeId('assistant-purchase-result'),
        role: 'assistant',
        text: response.answer,
        response,
      });
    } catch (error) {
      appendMessage({
        id: makeId('assistant-purchase-error'),
        role: 'assistant',
        text: error instanceof Error ? error.message : 'Mock purchase failed',
        error: true,
      });
    } finally {
      setBusyActionId('');
    }
  }

  const latestResponse = [...messages]
    .reverse()
    .find((message) => message.response)?.response;
  const enquiryCategory =
    latestResponse?.intent === 'refund' || latestResponse?.intent === 'transfer'
      ? latestResponse.intent
      : latestResponse?.risk_level
      ? 'risk'
      : 'general';
  const enquiryHref = `/support/enquiry?${new URLSearchParams({
    category: enquiryCategory,
    source: 'chatbot',
  }).toString()}`;

  return (
    <div
      className="card"
      style={{
        position: 'fixed',
        right: 16,
        bottom: 16,
        width: collapsed ? 220 : 'min(420px, calc(100vw - 24px))',
        zIndex: 40,
        padding: 14,
        display: 'flex',
        flexDirection: 'column',
        maxHeight: collapsed ? undefined : 'min(82vh, 760px)',
        overflow: 'hidden',
        boxShadow: '0 24px 70px rgba(0,0,0,0.38)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 12,
          marginBottom: collapsed ? 0 : 10,
          flexShrink: 0,
        }}
      >
        <div>
          <div style={{ fontSize: 17, fontWeight: 900 }}>Backstage Assistant</div>
          {!collapsed ? (
            <div className="small" style={{ opacity: 0.62, marginTop: 2 }}>
              Live events · artists · policies · mock purchase
            </div>
          ) : null}
        </div>
        <button
          type="button"
          className="btn ghost"
          onClick={() => setCollapsed((value) => !value)}
          style={{ padding: '6px 10px', minWidth: 'unset' }}
        >
          {collapsed ? 'Open' : 'Hide'}
        </button>
      </div>

      {!collapsed ? (
        <>
          <div
            ref={messageListRef}
            style={{
              minHeight: 160,
              flex: 1,
              overflowY: 'auto',
              paddingRight: 4,
              display: 'grid',
              alignContent: 'start',
              gap: 10,
            }}
          >
            {messages.map((message) => {
              const response = message.response;
              const events = getEvents(response);
              const selectionQuantity =
                response?.action?.type === 'purchase_selection'
                  ? response.action.quantity
                  : undefined;
              const confirmationAction =
                response?.action?.type === 'purchase_confirmation'
                  ? response.action
                  : null;
              const orderId = getOrderId(response);

              return (
                <div
                  key={message.id}
                  style={{
                    justifySelf: message.role === 'user' ? 'end' : 'stretch',
                    width: message.role === 'user' ? '86%' : '100%',
                    borderRadius: 16,
                    padding: message.role === 'user' ? '10px 12px' : 12,
                    background:
                      message.role === 'user'
                        ? 'rgba(110,125,255,0.22)'
                        : message.error
                        ? 'rgba(255,80,80,0.09)'
                        : 'rgba(255,255,255,0.055)',
                    border: message.error
                      ? '1px solid rgba(255,80,80,0.32)'
                      : '1px solid rgba(255,255,255,0.07)',
                  }}
                >
                  <div
                    className="small"
                    style={{
                      opacity: 0.55,
                      fontWeight: 700,
                      marginBottom: 5,
                    }}
                  >
                    {message.role === 'user' ? 'You' : 'Assistant'}
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.58 }}>
                    {message.text}
                  </div>

                  {events.length ? (
                    <div style={{ display: 'grid', gap: 9, marginTop: 10 }}>
                      {events.map((event) => (
                        <EventResultCard
                          key={event.id}
                          event={event}
                          selectionQuantity={selectionQuantity}
                          onSelect={(selectedEvent, quantity) =>
                            handleSelectEvent(
                              selectedEvent,
                              quantity,
                              response?.lang || 'en'
                            )
                          }
                        />
                      ))}
                    </div>
                  ) : null}

                  {confirmationAction ? (
                    <PurchaseConfirmation
                      action={confirmationAction}
                      lang={response?.lang || 'en'}
                      busy={busyActionId === message.id}
                      completed={completedActionIds.has(message.id)}
                      onConfirm={(action) =>
                        void handleConfirmPurchase(
                          message.id,
                          action,
                          response?.lang || 'en'
                        )
                      }
                    />
                  ) : null}

                  {response?.answer_mode === 'purchase_completed' ? (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                      <Link
                        className="btn secondary"
                        href="/wallet"
                        style={{ padding: '7px 10px', minWidth: 'unset' }}
                      >
                        Open wallet
                      </Link>
                      {events[0]?.id ? (
                        <Link
                          className="btn ghost"
                          href={`/chat/${events[0].id}`}
                          style={{ padding: '7px 10px', minWidth: 'unset' }}
                        >
                          Event chat
                        </Link>
                      ) : null}
                    </div>
                  ) : null}

                  {orderId ? (
                    <div className="small" style={{ opacity: 0.68, marginTop: 9 }}>
                      Order: {orderId}
                    </div>
                  ) : null}

                  {response?.risk_level &&
                  response.risk_level !== 'low' ? (
                    <div
                      className="small"
                      style={{
                        color: '#ffd38a',
                        marginTop: 9,
                        lineHeight: 1.5,
                      }}
                    >
                      Risk check: {response.risk_level}
                    </div>
                  ) : null}

                  {response?.citations?.length ? (
                    <details className="small" style={{ marginTop: 9, opacity: 0.7 }}>
                      <summary style={{ cursor: 'pointer' }}>Sources</summary>
                      <div style={{ marginTop: 5 }}>
                        {response.citations.join(' · ')}
                      </div>
                    </details>
                  ) : null}
                </div>
              );
            })}

            {loading ? (
              <div
                className="small"
                style={{
                  padding: '10px 12px',
                  borderRadius: 16,
                  background: 'rgba(255,255,255,0.055)',
                  opacity: 0.72,
                }}
              >
                Searching the current data…
              </div>
            ) : null}
          </div>

          <div
            style={{
              display: 'flex',
              gap: 7,
              overflowX: 'auto',
              padding: '10px 0 8px',
              flexShrink: 0,
            }}
          >
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="btn ghost"
                disabled={loading}
                onClick={() => void sendQuestion(prompt)}
                style={{
                  padding: '6px 9px',
                  minWidth: 'max-content',
                  fontSize: 12,
                }}
              >
                {prompt}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <textarea
              className="textarea"
              rows={2}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleTextareaKeyDown}
              placeholder={
                eventId
                  ? 'Ask about this event or buy a ticket…'
                  : 'Search events or ask a ticket question…'
              }
              style={{ resize: 'none', minHeight: 66, maxHeight: 110 }}
            />
            <button
              type="button"
              className="btn"
              onClick={() => void sendQuestion()}
              disabled={loading || !question.trim()}
              style={{ minWidth: 72 }}
            >
              Send
            </button>
          </div>

          <div
            className="small"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: 10,
              alignItems: 'center',
              marginTop: 9,
              opacity: 0.72,
              flexShrink: 0,
            }}
          >
            <span>Enter to send · Shift+Enter for a new line</span>
            <Link href={enquiryHref}>Support</Link>
          </div>
        </>
      ) : null}
    </div>
  );
}
