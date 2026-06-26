'use client';

import { useState } from 'react';

export function MessageComposer({ onSend }: { onSend: (content: string) => Promise<void> }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!content.trim()) return;
    setLoading(true);
    try {
      await onSend(content);
      setContent('');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <textarea className="textarea" rows={4} value={content} onChange={(e) => setContent(e.target.value)} placeholder="Send a message to the fan chat..." />
      <div className="space" />
      <button className="btn" onClick={submit} disabled={loading}>{loading ? 'Sending...' : 'Send message'}</button>
    </div>
  );
}
