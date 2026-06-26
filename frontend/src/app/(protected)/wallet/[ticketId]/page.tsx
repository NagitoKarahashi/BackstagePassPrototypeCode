'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { QRCodeSVG } from 'qrcode.react';
import { PageHeader } from '@/components/common/PageHeader';
import {
  getTicketById,
  getTicketQr,
  refundTicket,
  transferTicket,
  getTicketHistory,
  getTicketMarketStatus,
} from '@/lib/api/tickets';
import { cancelListing } from '@/lib/api/marketplace';
import { getWeb3TicketHistory, mintTicket } from '@/lib/api/web3';
import { ListForSaleModal } from '@/components/wallet/ListForSaleModal';
import type { TicketHistoryItem } from '@/lib/types';

type TicketDetailResponse = {
  ticket?: {
    id: string;
    user_id?: string;
    order_id?: string;
    event_id?: string;
    event_uuid?: string;
    token_id?: string;
    contract_address?: string;
    chain?: string;
    metadata?: Record<string, unknown>;
    metadata_uri?: string;
    qr_payload?: string;
    status?: string;
    created_at?: string;
    is_listed?: boolean;
    transfer_locked?: boolean;
    resale_allowed?: boolean;
    last_transfer_at?: string;
    owner_wallet?: string;
    mint_status?: string;
    minted_at?: string;
    tx_hash?: string;
  };
  event?: {
    id?: string;
    event_code?: string;
    title?: string;
    artist?: string;
    genre?: string;
    city?: string;
    start_time?: string;
    poster_url?: string;
  };
};

type TicketQrResponse = {
  ticket_id?: string;
  status?: string;
  qr_payload?: string | null;
};

type MarketStatusResponse = {
  ticket_id?: string;
  ticket_status?: string;
  is_listed?: boolean;
  transfer_locked?: boolean;
  resale_allowed?: boolean;
  owner_wallet?: string | null;
  mint_status?: string | null;
  token_id?: string | null;
  contract_address?: string | null;
  chain?: string | null;
  tx_hash?: string | null;
  listing?: {
    id?: string;
    status?: string;
    listing_price?: number;
    currency?: string;
    seller_wallet?: string | null;
    buyer_wallet?: string | null;
    tx_hash?: string | null;
    created_at?: string | null;
    sold_at?: string | null;
    cancelled_at?: string | null;
  } | null;
};

type Web3HistoryItem = {
  id: string;
  ticket_id: string;
  from_user_id?: string | null;
  to_user_id?: string | null;
  from_wallet?: string | null;
  to_wallet?: string | null;
  action: string;
  tx_hash?: string | null;
  note?: string | null;
  created_at?: string | null;
};

function getDecision(data: Record<string, unknown> | null): string {
  if (!data) return '';
  const risk =
    typeof data.risk === 'object' && data.risk ? (data.risk as Record<string, unknown>) : null;
  const value =
    data.decision ||
    data.status ||
    data.action ||
    data.result ||
    risk?.decision ||
    risk?.status ||
    risk?.action;

  return typeof value === 'string' ? value.toLowerCase() : '';
}

function getRiskLabel(data: Record<string, unknown> | null): string {
  if (!data) return '';
  const risk =
    typeof data.risk === 'object' && data.risk ? (data.risk as Record<string, unknown>) : null;
  const value = data.risk_level || data.level || risk?.risk_level || risk?.level || risk?.label;
  return typeof value === 'string' ? value : '';
}

function getMessage(data: Record<string, unknown> | null): string {
  if (!data) return '';
  const risk =
    typeof data.risk === 'object' && data.risk ? (data.risk as Record<string, unknown>) : null;

  const candidates = [
    data.message,
    data.detail,
    data.reason,
    risk?.message,
    risk?.detail,
    risk?.reason,
  ];

  for (const item of candidates) {
    if (typeof item === 'string' && item.trim()) return item;
    if (item && typeof item === 'object') {
      try {
        return JSON.stringify(item);
      } catch {
        return String(item);
      }
    }
  }

  return '';
}

function InfoRow({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 13, opacity: 0.65, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 500, wordBreak: 'break-word' }}>
        {value || '—'}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status?: string }) {
  const normalized = (status || 'unknown').toLowerCase();

  let bg = 'rgba(255,255,255,0.08)';
  let color = '#fff';

  if (normalized === 'active') {
    bg = 'rgba(66, 184, 131, 0.18)';
    color = '#7CFFB2';
  } else if (normalized === 'used') {
    bg = 'rgba(255, 184, 77, 0.18)';
    color = '#FFD27C';
  } else if (normalized === 'expired') {
    bg = 'rgba(255, 99, 99, 0.18)';
    color = '#FF9A9A';
  } else if (normalized === 'refunded') {
    bg = 'rgba(160, 160, 160, 0.18)';
    color = '#D8D8D8';
  }

  return (
    <span
      style={{
        padding: '6px 10px',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 700,
        background: bg,
        color,
        textTransform: 'uppercase',
        letterSpacing: 0.4,
      }}
    >
      {normalized}
    </span>
  );
}

function SmallTag({
  label,
  tone = 'gray',
}: {
  label: string;
  tone?: 'gray' | 'blue' | 'gold' | 'green';
}) {
  let bg = 'rgba(255,255,255,0.08)';
  let color = '#E8E8E8';

  if (tone === 'blue') {
    bg = 'rgba(125,180,255,0.16)';
    color = '#BBD3FF';
  } else if (tone === 'gold') {
    bg = 'rgba(255,204,102,0.16)';
    color = '#FFD27C';
  } else if (tone === 'green') {
    bg = 'rgba(66,184,131,0.18)';
    color = '#A9FFCB';
  }

  return (
    <span
      style={{
        padding: '4px 8px',
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 700,
        background: bg,
        color,
      }}
    >
      {label}
    </span>
  );
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function shortAddr(value?: string | null) {
  if (!value) return '—';
  if (value.length <= 18) return value;
  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

function buildSupportHref(params: {
  category: 'refund' | 'transfer' | 'risk' | 'ticket' | 'general';
  subject: string;
  ticketId?: string;
  eventUuid?: string;
  source?: string;
}) {
  const search = new URLSearchParams();
  search.set('category', params.category);
  search.set('subject', params.subject);

  if (params.ticketId) search.set('ticket_id', params.ticketId);
  if (params.eventUuid) search.set('event_uuid', params.eventUuid);
  if (params.source) search.set('source', params.source);

  return `/support/enquiry?${search.toString()}`;
}

function ResultBanner({
  title,
  data,
}: {
  title: string;
  data: Record<string, unknown> | null;
}) {
  if (!data) return null;

  const decision = getDecision(data);
  const message = getMessage(data);
  const riskLabel = getRiskLabel(data);

  let border = '1px solid rgba(66,184,131,0.35)';
  let background = 'rgba(66,184,131,0.08)';
  let summary = 'Request processed successfully.';

  if (title.toLowerCase().includes('refund')) {
    if (decision === 'requested') {
      summary = 'Refund request submitted successfully. This ticket has entered the refund flow.';
    } else if (decision === 'review_required') {
      border = '1px solid rgba(255,184,77,0.35)';
      background = 'rgba(255,184,77,0.08)';
      summary = 'Refund request submitted, but it requires manual review before completion.';
    } else if (decision === 'blocked') {
      border = '1px solid rgba(255,80,80,0.35)';
      background = 'rgba(255,80,80,0.08)';
      summary = 'Refund request was blocked by the current risk or policy checks.';
    } else if (decision === 'error') {
      border = '1px solid rgba(255,80,80,0.35)';
      background = 'rgba(255,80,80,0.08)';
      summary = 'Refund request failed before completion.';
    }
  }

  if (title.toLowerCase().includes('transfer')) {
    if (decision === 'requested' || decision === 'success' || decision === 'completed') {
      summary = 'Ticket transfer request was accepted successfully.';
    } else if (decision === 'review_required') {
      border = '1px solid rgba(255,184,77,0.35)';
      background = 'rgba(255,184,77,0.08)';
      summary = 'Transfer request was submitted, but requires additional review.';
    } else if (decision === 'blocked') {
      border = '1px solid rgba(255,80,80,0.35)';
      background = 'rgba(255,80,80,0.08)';
      summary = 'Transfer request was blocked by the current risk controls.';
    } else if (decision === 'error') {
      border = '1px solid rgba(255,80,80,0.35)';
      background = 'rgba(255,80,80,0.08)';
      summary = 'Transfer request failed before completion.';
    }
  }

  return (
    <div className="card" style={{ border, background }}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>{title}</div>
      <div style={{ marginBottom: 10, lineHeight: 1.6 }}>{summary}</div>
      <div className="small">Decision: {decision || 'unknown'}</div>
      <div className="small">Risk: {riskLabel || 'n/a'}</div>
      {message ? (
        <div className="small" style={{ marginTop: 6, whiteSpace: 'pre-wrap' }}>
          Details: {message}
        </div>
      ) : null}
    </div>
  );
}

export default function TicketDetailPage() {
  const params = useParams<{ ticketId: string }>();

  const [detail, setDetail] = useState<TicketDetailResponse | null>(null);
  const [qr, setQr] = useState<TicketQrResponse | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatusResponse | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  const [refundLoading, setRefundLoading] = useState(false);
  const [transferLoading, setTransferLoading] = useState(false);
  const [listingCancelLoading, setListingCancelLoading] = useState(false);
  const [minting, setMinting] = useState(false);

  const [refundResult, setRefundResult] = useState<Record<string, unknown> | null>(null);
  const [transferResult, setTransferResult] = useState<Record<string, unknown> | null>(null);
  const [transferTarget, setTransferTarget] = useState('');

  const [history, setHistory] = useState<TicketHistoryItem[]>([]);
  const [web3History, setWeb3History] = useState<Web3HistoryItem[]>([]);
  const [listingOpen, setListingOpen] = useState(false);

  async function refreshAll() {
    if (!params.ticketId) return;

    const results = await Promise.allSettled([
      getTicketById(params.ticketId),
      getTicketQr(params.ticketId),
      getTicketHistory(params.ticketId),
      getWeb3TicketHistory(params.ticketId),
      getTicketMarketStatus(params.ticketId),
    ]);

    const [detailRes, qrRes, historyRes, web3HistoryRes, marketRes] = results;

    if (detailRes.status === 'rejected') {
      setDetail(null);
      throw new Error(
        detailRes.reason instanceof Error
          ? detailRes.reason.message
          : 'Failed to load ticket detail'
      );
    }

    setDetail(detailRes.value as TicketDetailResponse);

    if (qrRes.status === 'fulfilled') {
      setQr(qrRes.value as TicketQrResponse);
    } else {
      setQr(null);
    }

    if (historyRes.status === 'fulfilled') {
      const opsHistory =
        ((historyRes.value as { items?: TicketHistoryItem[] } | null)?.items || []);
      setHistory(opsHistory);
    } else {
      setHistory([]);
    }

    if (web3HistoryRes.status === 'fulfilled') {
      const web3Items =
        ((web3HistoryRes.value as { items?: Web3HistoryItem[] } | null)?.items || []);
      setWeb3History(web3Items);
    } else {
      setWeb3History([]);
    }

    if (marketRes.status === 'fulfilled') {
      setMarketStatus(marketRes.value as MarketStatusResponse);
    } else {
      setMarketStatus(null);
    }
  }

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        setError('');
        await refreshAll();
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load ticket detail');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [params.ticketId]);

  const ticket = detail?.ticket;
  const event = detail?.event;

  const qrStatus = qr?.status || ticket?.status || '';
  const qrPayload = qrStatus === 'active' ? (qr?.qr_payload || '') : '';
  const showQr = qrStatus === 'active' && !!qrPayload;

  const shortTicketId = useMemo(() => {
    if (!ticket?.id) return '';
    return ticket.id.slice(0, 8);
  }, [ticket?.id]);

  const eventStarted = useMemo(() => {
    if (!event?.start_time) return false;
    const start = new Date(event.start_time);
    if (Number.isNaN(start.getTime())) return false;
    return start.getTime() <= Date.now();
  }, [event?.start_time]);

  const effectiveIsListed = marketStatus?.is_listed ?? ticket?.is_listed ?? false;
  const effectiveTransferLocked =
    marketStatus?.transfer_locked ?? ticket?.transfer_locked ?? false;
  const effectiveResaleAllowed =
    marketStatus?.resale_allowed ?? ticket?.resale_allowed ?? true;
  const activeListing =
    marketStatus?.listing && marketStatus.listing.status === 'active'
      ? marketStatus.listing
      : null;

  const refundEligible = useMemo(() => {
    const status = (ticket?.status || '').toLowerCase();
    return status === 'active' && !eventStarted && !effectiveIsListed && !effectiveTransferLocked;
  }, [ticket?.status, eventStarted, effectiveIsListed, effectiveTransferLocked]);

  const chatEligible = useMemo(() => {
    const status = (ticket?.status || '').toLowerCase();
    return status === 'active' || status === 'used';
  }, [ticket?.status]);

  const canList = useMemo(() => {
    const status = (ticket?.status || '').toLowerCase();
    return status === 'active' && !effectiveTransferLocked && !effectiveIsListed && effectiveResaleAllowed !== false;
  }, [ticket?.status, effectiveTransferLocked, effectiveIsListed, effectiveResaleAllowed]);

  const canCancelListing = useMemo(() => {
    return !!activeListing;
  }, [activeListing]);

  const mintStatus = (ticket?.mint_status || marketStatus?.mint_status || 'not_minted').toLowerCase();
  const canMint = (ticket?.status || '').toLowerCase() === 'active' && mintStatus !== 'minted';

  async function copyPayload() {
    try {
      if (!showQr || !qrPayload) return;
      await navigator.clipboard.writeText(qrPayload);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  async function handleMint() {
    try {
      setMinting(true);
      setError('');
      if (!ticket?.id) throw new Error('Missing ticket id');
      await mintTicket(ticket.id);
      await refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Mint failed');
    } finally {
      setMinting(false);
    }
  }

  async function handleRefund() {
    try {
      setRefundLoading(true);
      setRefundResult(null);
      setError('');

      if (!ticket?.id) throw new Error('Missing ticket id');

      const result = await refundTicket(ticket.id);
      setRefundResult(result as Record<string, unknown>);
      await refreshAll();
    } catch (e) {
      setRefundResult({
        decision: 'error',
        message: e instanceof Error ? e.message : 'Refund failed',
      });
    } finally {
      setRefundLoading(false);
    }
  }

  async function handleTransfer() {
    try {
      setTransferLoading(true);
      setTransferResult(null);
      setError('');

      if (!ticket?.id) throw new Error('Missing ticket id');
      if (!transferTarget.trim()) throw new Error('Please enter a target user id');

      const result = await transferTicket(ticket.id, {
        to_user_id: transferTarget.trim(),
        device_id: 'web-demo',
        ip_address: '127.0.0.1',
      });
      setTransferResult(result as Record<string, unknown>);
      await refreshAll();
    } catch (e) {
      setTransferResult({
        decision: 'error',
        message: e instanceof Error ? e.message : 'Transfer failed',
      });
    } finally {
      setTransferLoading(false);
    }
  }

  async function handleCancelListing() {
    try {
      setListingCancelLoading(true);
      setError('');

      const listingId = activeListing?.id;
      if (!listingId) throw new Error('No active listing found');

      await cancelListing(listingId);
      await refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to cancel listing');
    } finally {
      setListingCancelLoading(false);
    }
  }

  if (loading) {
    return <div className="card">Loading ticket detail...</div>;
  }

  if (error) {
    return (
      <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load ticket detail</div>
        <div style={{ opacity: 0.8 }}>{error}</div>
      </div>
    );
  }

  if (!ticket) {
    return <div className="card">Ticket not found.</div>;
  }

  return (
    <div>
      <PageHeader
        title={`Ticket #${shortTicketId || 'Detail'}`}
        subtitle="Ticket detail + refund / transfer + risk-aware action states + Web3 ownership metadata."
      />

      <div className="grid grid-2" style={{ alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 16 }}>
          <div className="card">
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 12,
                marginBottom: 18,
              }}
            >
              <div>
                <div style={{ fontSize: 28, fontWeight: 800, marginBottom: 6 }}>
                  {event?.title || 'Event Ticket'}
                </div>
                <div style={{ opacity: 0.75 }}>
                  {event?.artist || 'Unknown artist'} {event?.city ? `· ${event.city}` : ''}
                </div>
              </div>
              <StatusBadge status={ticket.status} />
            </div>

            <div className="grid" style={{ gap: 8 }}>
              <InfoRow label="Ticket ID" value={ticket.id} />
              <InfoRow label="Order ID" value={ticket.order_id} />
              <InfoRow label="Event Code" value={ticket.event_id} />
              <InfoRow label="Event UUID" value={ticket.event_uuid} />
              <InfoRow label="Token ID" value={ticket.token_id || marketStatus?.token_id} />
              <InfoRow label="Chain" value={ticket.chain || marketStatus?.chain} />
              <InfoRow label="Contract Address" value={ticket.contract_address || marketStatus?.contract_address} />
              <InfoRow label="Start Time" value={formatDate(event?.start_time)} />
              <InfoRow label="Created At" value={formatDate(ticket.created_at)} />
            </div>

            <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <SmallTag
                label={mintStatus === 'minted' ? 'Minted' : 'Not Minted'}
                tone={mintStatus === 'minted' ? 'blue' : 'gray'}
              />
              {effectiveIsListed ? <SmallTag label="Listed" tone="gold" /> : null}
            </div>

            <div style={{ marginTop: 18, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button className="btn" onClick={handleMint} disabled={!canMint || minting}>
                {minting ? 'Minting...' : mintStatus === 'minted' ? 'Already Minted' : 'Mint NFT'}
              </button>

              {ticket.event_uuid ? (
                <>
                  {chatEligible ? (
                    <Link href={`/chat/${ticket.event_uuid}`} className="btn secondary">
                      Open Event Chat
                    </Link>
                  ) : null}
                  <Link href={`/events/${ticket.event_uuid}`} className="btn ghost">
                    Back to Event
                  </Link>
                  <Link href="/risk" className="btn ghost">
                    Risk Overview
                  </Link>
                </>
              ) : null}
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 10 }}>Refund</div>

            <InfoRow
              label="Refund Eligibility"
              value={refundEligible ? 'Eligible for refund request' : 'Not currently eligible'}
            />

            <div style={{ opacity: 0.76, lineHeight: 1.7, marginBottom: 14 }}>
              Refund is allowed only for active tickets before the event starts, and is blocked if
              the ticket is already listed or transfer locked.
            </div>

            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button className="btn" onClick={handleRefund} disabled={!refundEligible || refundLoading}>
                {refundLoading ? 'Submitting...' : 'Request Refund'}
              </button>

              <Link
                href={buildSupportHref({
                  category: 'refund',
                  subject: `Refund issue for ticket ${ticket.id}`,
                  ticketId: ticket.id,
                  eventUuid: ticket.event_uuid,
                  source: 'ticket_detail_refund',
                })}
                className="btn ghost"
              >
                Contact Support
              </Link>
            </div>

            <div style={{ marginTop: 14 }}>
              <ResultBanner title="Refund Result" data={refundResult} />
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 10 }}>Transfer</div>

            <InfoRow
              label="Transfer Lock"
              value={effectiveTransferLocked ? 'Locked' : 'Not locked'}
            />
            <InfoRow
              label="Resale Allowed"
              value={effectiveResaleAllowed === false ? 'No' : 'Yes'}
            />
            <InfoRow label="Last Transfer At" value={formatDate(ticket.last_transfer_at)} />

            <div style={{ opacity: 0.76, lineHeight: 1.7, marginBottom: 14 }}>
              Transfer requires a valid target user id and may be blocked or reviewed depending on
              risk checks.
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 13, opacity: 0.65, marginBottom: 6 }}>Target User ID</div>
              <input
                value={transferTarget}
                onChange={(e) => setTransferTarget(e.target.value)}
                placeholder="Enter target user id"
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: 12,
                  border: '1px solid rgba(255,255,255,0.12)',
                  background: 'rgba(255,255,255,0.04)',
                  color: '#fff',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button className="btn" onClick={handleTransfer} disabled={transferLoading || !transferTarget.trim()}>
                {transferLoading ? 'Submitting...' : 'Transfer Ticket'}
              </button>

              <Link
                href={buildSupportHref({
                  category: 'transfer',
                  subject: `Transfer issue for ticket ${ticket.id}`,
                  ticketId: ticket.id,
                  eventUuid: ticket.event_uuid,
                  source: 'ticket_detail_transfer',
                })}
                className="btn ghost"
              >
                Contact Support
              </Link>
            </div>

            <div style={{ marginTop: 14 }}>
              <ResultBanner title="Transfer Result" data={transferResult} />
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 10 }}>
              Marketplace
            </div>

            <InfoRow label="Listing Status" value={effectiveIsListed ? 'Currently listed' : 'Not listed'} />
            <InfoRow label="Transfer Lock" value={effectiveTransferLocked ? 'Locked while listed' : 'Not locked'} />
            <InfoRow label="Resale Allowed" value={effectiveResaleAllowed === false ? 'No' : 'Yes'} />
            <InfoRow
              label="Active Listing"
              value={
                activeListing
                  ? `${activeListing.listing_price || 0} ${activeListing.currency || 'USD'}`
                  : 'No active listing'
              }
            />
            <InfoRow label="Listing Seller Wallet" value={shortAddr(activeListing?.seller_wallet)} />
            <InfoRow label="Listing Buyer Wallet" value={shortAddr(activeListing?.buyer_wallet)} />
            <InfoRow label="Listing Tx Hash" value={activeListing?.tx_hash || marketStatus?.tx_hash} />

            <div style={{ marginTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {canList ? (
                <button className="btn" onClick={() => setListingOpen(true)}>
                  List For Sale
                </button>
              ) : null}

              {canCancelListing ? (
                <button className="btn secondary" onClick={handleCancelListing} disabled={listingCancelLoading}>
                  {listingCancelLoading ? 'Cancelling...' : 'Cancel Listing'}
                </button>
              ) : null}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gap: 16 }}>
          <div className="card">
            <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 10 }}>QR Access</div>
            <div style={{ opacity: 0.76, lineHeight: 1.7, marginBottom: 16 }}>
              This QR is generated directly from the backend QR payload and can be used for ticket
              verification and check-in demo flow.
            </div>

            <div
              style={{
                background: 'rgba(255,255,255,0.04)',
                borderRadius: 20,
                padding: 28,
                display: 'grid',
                placeItems: 'center',
                marginBottom: 16,
                minHeight: 260,
              }}
            >
              {showQr ? (
                <QRCodeSVG
                  value={qrPayload}
                  size={220}
                  bgColor="#ffffff"
                  fgColor="#111111"
                  level="M"
                  includeMargin
                />
              ) : (
                <div
                  style={{
                    width: 220,
                    height: 220,
                    display: 'grid',
                    placeItems: 'center',
                    color: '#111',
                    fontWeight: 700,
                    textAlign: 'center',
                    padding: 16,
                    background: '#fff',
                    borderRadius: 12,
                  }}
                >
                  QR unavailable for tickets in status: {(qrStatus || 'unknown').toUpperCase()}
                </div>
              )}
            </div>

            <InfoRow label="QR Ticket Status" value={qrStatus || 'unknown'} />
            <InfoRow label="QR Endpoint Ticket ID" value={qr?.ticket_id} />
            <InfoRow label="QR Payload" value={showQr ? qrPayload : 'No QR payload available'} />

            <div style={{ marginTop: 14 }}>
              <button className="btn" onClick={copyPayload} disabled={!showQr}>
                {copied ? 'Copied' : 'Copy QR Payload'}
              </button>
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 12 }}>NFT Info</div>
            <InfoRow label="Mint Status" value={marketStatus?.mint_status || ticket.mint_status || 'not_minted'} />
            <InfoRow label="Token ID" value={marketStatus?.token_id || ticket.token_id} />
            <InfoRow label="Contract Address" value={marketStatus?.contract_address || ticket.contract_address} />
            <InfoRow label="Chain" value={marketStatus?.chain || ticket.chain || 'Off-chain mock'} />
            <InfoRow label="Owner Wallet" value={shortAddr(marketStatus?.owner_wallet || ticket.owner_wallet)} />
            <InfoRow label="Minted At" value={formatDate(ticket.minted_at)} />
            <InfoRow label="Tx Hash" value={marketStatus?.tx_hash || ticket.tx_hash} />
            <InfoRow label="Metadata URI" value={ticket.metadata_uri} />
          </div>

          <div className="card">
            <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 12 }}>Ownership History</div>

            {history.length > 0 || web3History.length > 0 ? (
              <div style={{ display: 'grid', gap: 12 }}>
                {web3History.map((item) => (
                  <div
                    key={`web3-${item.id}`}
                    style={{
                      padding: 14,
                      borderRadius: 14,
                      background: 'rgba(125,180,255,0.08)',
                    }}
                  >
                    <div style={{ fontWeight: 700, marginBottom: 6 }}>
                      {item.action || 'web3'} · on-chain style
                    </div>
                    <div className="small">From Wallet: {shortAddr(item.from_wallet)}</div>
                    <div className="small">To Wallet: {shortAddr(item.to_wallet)}</div>
                    <div className="small">Tx: {item.tx_hash || '—'}</div>
                    <div className="small">At: {formatDate(item.created_at)}</div>
                    {item.note ? <div className="small">Note: {item.note}</div> : null}
                  </div>
                ))}

                {history.map((item) => (
                  <div
                    key={`ops-${item.id}`}
                    style={{
                      padding: 14,
                      borderRadius: 14,
                      background: 'rgba(255,255,255,0.04)',
                    }}
                  >
                    <div style={{ fontWeight: 700, marginBottom: 6 }}>
                      {item.transfer_type || 'transfer'} · {item.transfer_status || 'unknown'}
                    </div>
                    <div className="small">From: {item.from_user_id || '—'}</div>
                    <div className="small">To: {item.to_user_id || '—'}</div>
                    <div className="small">At: {formatDate(item.created_at)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ opacity: 0.72 }}>No transfer history found.</div>
            )}
          </div>
        </div>
      </div>

      <ListForSaleModal
        open={listingOpen}
        onClose={() => setListingOpen(false)}
        ticketId={ticket.id}
        onSuccess={async () => {
          setListingOpen(false);
          await refreshAll();
        }}
      />
    </div>
  );
}