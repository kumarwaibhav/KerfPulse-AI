import { useEffect, useState } from 'react';

type Source = { device_id: string; asset_id: string; site_id: string; health: string; reason_codes: string[];
  qualification: { id: string | null; state: string; revision: number; reason: string; valid_until?: string };
  physical_connection: string; last_received_at: string | null; evidence_cutoff: string | null;
  processing: { state: string; assessment?: { five_cut_score: number | null; action: string; reason_codes: string[]; model_version: string | null } } | null };
type Health = { workspace_id: string; sources: Source[]; access: string };
const words = (value: string) => value.replaceAll('_', ' ');

export function SourceHealth() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  async function refresh() {
    setBusy(true);
    try {
      const response = await fetch('/api/fresh/source-health');
      if (!response.ok) throw new Error('Source health unavailable. Retry when service recovers.');
      setHealth(await response.json()); setError('');
    } catch (e) { setError(String(e)); }
    finally { setBusy(false); }
  }
  useEffect(() => { void refresh(); const interval = window.setInterval(() => void refresh(), 15000); return () => window.clearInterval(interval); }, []);
  return <section className="panel source-health" aria-label="Source qualification and health" style={{ padding: 24, marginBottom: 20 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
      <div><span className="eyebrow">SOURCE TRUST · MODEL COMPATIBILITY</span><h2>Source qualification &amp; health</h2></div>
      <button className="button secondary" onClick={() => void refresh()} disabled={busy}>{busy ? 'Checking sources…' : 'Refresh source health'}</button>
    </div>
    <p>Transport connectivity, measurement freshness and model qualification are separate checks. Shadow scores do not authorize maintenance action.</p>
    {error && <p role="alert">{error} Previously displayed status may be outdated.</p>}
    {!health && !error && <p role="status">Loading source access…</p>}
    {health && !health.sources.length && <p>No sources assigned to this workspace. Physical commissioning pending; no live factory connection is established.</p>}
    {health && <details><summary>Local evaluation source access</summary><p>Ask local administrator to grant sources to this workspace. This identifier grants no login access by itself. Customer identity integration remains pending.</p>
      <code style={{ overflowWrap: 'anywhere' }}>{health.workspace_id}</code>
      <button className="button secondary" onClick={async () => { try { await navigator.clipboard.writeText(health.workspace_id); setCopied(true); } catch { setError('Copy unavailable. Select workspace identifier above.'); } }}>{copied ? 'Workspace ID copied' : 'Copy workspace ID'}</button>
    </details>}
    {health?.sources.map(source => <article key={source.device_id} style={{ borderTop: '1px solid var(--border-subtle)', marginTop: 20, paddingTop: 16 }}>
      <h3>{source.asset_id} · {source.site_id}</h3>
      <p><strong>{words(source.qualification.state)}</strong> · Revision {source.qualification.revision} · {words(source.health)}</p>
      <p>Physical connection: {words(source.physical_connection)}. Source: device-uploaded measurements.</p>
      <p>Evidence cutoff: {source.evidence_cutoff ?? 'No observations'} · Last receipt: {source.last_received_at ?? 'None'}</p>
      <p>Qualification: {words(source.qualification.reason)}{source.qualification.valid_until ? ` · Expires ${source.qualification.valid_until}` : ''}</p>
      {source.reason_codes.length > 0 && <ul>{source.reason_codes.map(reason => <li key={reason}>{words(reason)}</li>)}</ul>}
      <p>Processing: {source.processing ? words(source.processing.state) : 'Awaiting assessment'}</p>
      {source.processing?.assessment && <><p>Stored assessment score: {source.processing.assessment.five_cut_score === null ? 'Unavailable' : `${(source.processing.assessment.five_cut_score * 100).toFixed(1)}% · shadow evaluation only`}</p>
        <p>Model: {source.processing.assessment.model_version ?? 'Unavailable'} · {words(source.processing.assessment.action)}</p>
        <p>{source.processing.assessment.reason_codes.map(words).join(' · ')}</p></>}
    </article>)}
  </section>;
}
