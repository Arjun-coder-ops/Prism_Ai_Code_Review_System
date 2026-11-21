import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

type Finding = { path: string; start_line: number; end_line: number; severity: string; category: string; title: string; explanation: string; evidence: { line?: string; source?: string }; verification_state: string };
type Review = { id: string; url: string; status: string; head_sha: string | null; findings: Finding[]; error_message: string | null };

const api = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(path, init);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error?.message ?? 'The PRISM API returned an error.');
  return payload as T;
};

function App() {
  const [url, setUrl] = useState('');
  const [review, setReview] = useState<Review | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!review || ['completed', 'failed', 'canceled'].includes(review.status)) return;
    const timer = window.setTimeout(async () => {
      try { setReview(await api<Review>(`/api/reviews/${review.id}`)); }
      catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to refresh review.'); }
    }, 1200);
    return () => window.clearTimeout(timer);
  }, [review]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setMessage(''); setReview(null);
    try {
      const created = await api<Review>('/api/reviews', { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify({url}) });
      setReview(created);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to submit review.'); }
    finally { setBusy(false); }
  };

  return <main><nav><span className="mark">PRISM</span><span className="muted">Pull Request Intelligence</span><span className="nav-state"><i /> evidence pipeline online</span></nav><section className="hero"><p className="eyebrow">EVIDENCE-FIRST CODE REVIEW</p><h1>Ship changes with<br/><em>confidence.</em></h1><p className="lede">PRISM turns a GitHub pull request into a traceable review: changed code, supporting evidence, and findings a human can verify.</p><form onSubmit={submit}><label className="sr-only" htmlFor="pr-url">GitHub pull request URL</label><input id="pr-url" value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://github.com/org/repo/pull/42" required/><button disabled={busy}>{busy ? 'Queueing…' : 'Analyze pull request →'}</button></form><p className="status" aria-live="polite">{message}</p></section>{review && <ReviewPanel review={review} />}{!review && <section className="grid"><article><strong>01</strong><h2>Commit-pinned</h2><p>Every review is tied to the exact revision that was inspected.</p></article><article><strong>02</strong><h2>Evidence-backed</h2><p>Unsupported model suggestions are withheld instead of promoted as defects.</p></article><article><strong>03</strong><h2>Human-approved</h2><p>Reviewers stay in control before anything is published back to GitHub.</p></article></section>}</main>
}

function ReviewPanel({ review }: { review: Review }) {
  const active = !['completed', 'failed', 'canceled'].includes(review.status);
  return <section className="workspace" aria-live="polite"><div className="workspace-head"><div><p className="eyebrow">REVIEW RUN</p><h2>{review.url}</h2></div><span className={`pill ${review.status}`}>{review.status}</span></div>{active && <div className="progress"><span /><b>Fetching revision and verifying changed lines…</b></div>}{review.error_message && <p className="error">{review.error_message}</p>}{review.status === 'completed' && review.findings.length === 0 && <div className="empty"><strong>No sufficiently supported issues were found.</strong><span>PRISM abstained rather than promote unsupported warnings.</span></div>}{review.findings.length > 0 && <div className="findings">{review.findings.map((finding, index) => <article className="finding" key={`${finding.path}-${finding.start_line}-${index}`}><div className="finding-meta"><span className={`severity ${finding.severity}`}>{finding.severity}</span><code>{finding.path}:{finding.start_line}</code><span className="verified">✓ {finding.verification_state}</span></div><h3>{finding.title}</h3><p>{finding.explanation}</p><pre>{finding.evidence.line}</pre></article>)}</div>}{review.head_sha && <small className="sha">Inspected commit <code>{review.head_sha.slice(0, 12)}</code></small>}</section>;
}

createRoot(document.getElementById('root')!).render(<App />);
