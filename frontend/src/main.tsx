import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  const [url, setUrl] = useState('');
  const [message, setMessage] = useState('');
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setMessage('Submitting…');
    try {
      const response = await fetch('/api/reviews', { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify({url}) });
      const data = await response.json();
      setMessage(response.ok ? `Review ${data.id} queued` : data.error?.message ?? 'Unable to submit review');
    } catch { setMessage('API unavailable. Start the backend and try again.'); }
  };
  return <main><nav><span className="mark">PRISM</span><span className="muted">Pull Request Intelligence</span></nav><section className="hero"><p className="eyebrow">EVIDENCE-FIRST CODE REVIEW</p><h1>Ship changes with<br/><em>confidence.</em></h1><p className="lede">PRISM turns a GitHub pull request into a traceable review: changed code, supporting evidence, and findings a human can verify.</p><form onSubmit={submit}><input aria-label="GitHub pull request URL" value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://github.com/org/repo/pull/42" required/><button>Analyze pull request →</button></form><p className="status" aria-live="polite">{message}</p></section><section className="grid"><article><strong>01</strong><h2>Commit-pinned</h2><p>Every review is tied to the exact revision that was inspected.</p></article><article><strong>02</strong><h2>Evidence-backed</h2><p>Unsupported model suggestions are withheld instead of promoted as defects.</p></article><article><strong>03</strong><h2>Human-approved</h2><p>Reviewers stay in control before anything is published back to GitHub.</p></article></section></main>
}
createRoot(document.getElementById('root')!).render(<App />);
