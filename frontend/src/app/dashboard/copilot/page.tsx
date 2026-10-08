'use client';

import { useState, type FormEvent } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { apiPost, type ApiMeta } from '@/lib/api-client';
import { DataStatus } from '@/components/DataStatus';

type Reply = { answer: string; citations: string[]; mode: string; can_trigger_operations: boolean };
type Message = { role: 'user' | 'assistant'; text: string; citations?: string[]; meta?: ApiMeta };

export default function CopilotPage() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = question.trim();
    if (text.length < 3 || busy) return;
    setQuestion(''); setError(''); setBusy(true);
    setMessages((previous) => [...previous, { role: 'user', text }]);
    try {
      const response = await apiPost<Reply>('/assistant/query', { question: text, region_id: 'tn-coimbatore' });
      setMessages((previous) => [...previous, { role: 'assistant', text: response.data.answer, citations: response.data.citations, meta: response.meta }]);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Query failed'); }
    finally { setBusy(false); }
  }
  return <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-4xl flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
    <div className="border-b border-slate-100 bg-slate-50 p-4"><div className="flex items-center gap-3"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-blue"><Sparkles className="h-4 w-4 text-white" /></div><div><h1 className="font-semibold text-slate-900">NeroSentinel Evidence Assistant</h1><p className="text-xs text-slate-500">Deterministic backend explanations · no external LLM or operational actions</p></div></div></div>
    <div className="flex-1 space-y-5 overflow-y-auto p-6">{messages.length === 0 && <div className="max-w-xl rounded-xl bg-slate-50 p-5 text-sm leading-6 text-slate-600">Ask why the synthetic drought screen is elevated, what makes a scenario uncertain, or how to compare interventions. Answers come from the backend&apos;s bounded demo rules and cited artifacts.</div>}{messages.map((message, index) => <div key={index} className={`max-w-[85%] rounded-xl p-4 text-sm ${message.role === 'user' ? 'ml-auto bg-brand-blue text-white' : 'bg-slate-100 text-slate-800'}`}><p>{message.text}</p>{message.citations && message.citations.length > 0 && <p className="mt-3 border-t border-slate-200 pt-2 text-xs text-slate-500">Evidence: {message.citations.join(', ')}</p>}{message.meta && <DataStatus meta={message.meta} className="mt-3" />}</div>)}{busy && <p className="text-sm text-slate-500">Consulting backend rules…</p>}{error && <p role="alert" className="text-sm text-red-700">{error}</p>}</div>
    <form onSubmit={submit} className="flex gap-3 border-t border-slate-100 p-4"><input value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={1000} aria-label="Ask the evidence assistant" placeholder="Ask about drought drivers or uncertainty…" className="min-w-0 flex-1 rounded-full border border-slate-200 px-4 py-3 text-sm focus:border-brand-blue focus:outline-none" /><button type="submit" disabled={busy || question.trim().length < 3} className="rounded-full bg-brand-blue p-3 text-white disabled:opacity-50" aria-label="Send question"><Send className="h-4 w-4" /></button></form>
  </div>;
}
