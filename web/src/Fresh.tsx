import { useEffect, useState } from 'react';
import { importCuts, cutTemplate, downloadEvidence } from './freshImport';

async function call(path: string, body?: unknown) {
  const response = await fetch('/api/fresh/' + path, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail || 'Request failed'));
  return result;
}

type Assessment = { id: string; asset_id: string; tool_life_id: string; applicability: string; action: string;
  source_mode: string; cutoff: string; model_version: string; five_cut_score: number | null;
  actionable_score: number | null; inspection_slot: number | null; reason_codes: string[];
  review: { status: string; version: number; history: { action: string; at: string; finding?: string }[] } };

export function Fresh() {
  const [input, setInput] = useState('');
  const [schema, setSchema] = useState<any>(null);
  const [history, setHistory] = useState<Assessment[]>([]);
  const [conflicts, setConflicts] = useState<{id: string; event_id: string; arrived_at: string}[]>([]);
  const [errors, setErrors] = useState('');
  const [busy, setBusy] = useState(false);
  const [finding, setFinding] = useState('');
  async function refresh() {
    const [assessments, quarantine] = await Promise.all([call('assessments'), call('conflicts')]);
    setHistory(assessments); setConflicts(quarantine);
  }
  useEffect(() => { call('schema').then(setSchema).catch(e => setErrors(e.message)); refresh().catch(e => setErrors(e.message)); }, []);
  async function sample(unsupported = false) {
    try { const s = await call('schema'); setSchema(s); setInput(JSON.stringify({ events: [s.examples[unsupported ? 'unsupported' : 'supported']] }, null, 2)); setErrors(''); }
    catch (e) { setErrors(String(e)); }
  }
  async function score() {
    setBusy(true); setErrors('');
    try {
      const body = JSON.parse(input);
      const result = await call('assessments', Array.isArray(body) ? { events: body } : body.events ? body : { events: [body] });
      setErrors(result.results.flatMap((row: any) => (row.errors || []).map((e: any) => `Row ${row.row} · ${e.field} · ${e.message}`)).join('\n'));
      await refresh();
    } catch(e) { setErrors(String(e)); } finally { setBusy(false); }
  }
  async function review(a: Assessment, action: string) {
    setBusy(true); setErrors('');
    try { await call(`assessments/${a.id}/review`, { action, expected_version: a.review.version, finding: finding || null }); await refresh(); }
    catch(e) { setErrors(String(e)); } finally { setBusy(false); }
  }
  return <section className="fresh-workspace">
    <div className="panel" style={{ padding: 24, marginBottom: 20 }}>
      <span className="eyebrow">MEASURED EVIDENCE → MODEL → HUMAN REVIEW</span>
      <h2>Score a New Cut</h2><p>Submit compatible completed-cut summaries for a new tool identity. Future damage labels are excluded from the input.</p>
      <p>Live physical source · <strong>Unconfigured — commissioning pending</strong></p>
      <p>Engineering profile supports the published Haas summary contract. New plant mappings receive an unsupported-domain assessment until qualified.</p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, margin: '18px 0' }}>
        <button className="button secondary" onClick={() => sample()}>Load measured example</button>
        <button className="button secondary" onClick={() => sample(true)}>Load unsupported example</button>
        <button className="button secondary" disabled={!schema} onClick={() => downloadEvidence('kerfpulse-cut-template.csv', cutTemplate(schema, 'csv'), 'text/csv')}>Download CSV template</button>
        <button className="button secondary" disabled={!schema} onClick={() => downloadEvidence('kerfpulse-cut-template.json', cutTemplate(schema, 'json'), 'application/json')}>Download JSON template</button>
        <label className="button secondary">Open measurement file<input className="fresh-file" aria-label="Upload measured file" type="file" accept=".json,.csv" disabled={!schema} onChange={async e => {
          const f = e.target.files?.[0]; if (!f) return;
          if (f.size > 60000) { setErrors('Upload is limited to 60 kB.'); return; }
          try { setInput(JSON.stringify({ events: importCuts(await f.text(), f.name, schema) }, null, 2)); setErrors(''); }
          catch (error) { setErrors(String(error)); }
        }} /></label>
      </div>
      {schema && <p>Example uses measured source tool 2, cut {schema.example_provenance.cut}. Tools 2 and 4 were excluded from this release’s training. Demonstration timestamp is explicit. Historical benchmark remains 2/14 timely for current-only.</p>}
      <label htmlFor="fresh-input">Completed-cut JSON</label>
      <textarea id="fresh-input" value={input} placeholder="Load measured example or open a completed-cut CSV/JSON file. Review evidence here before scoring." onChange={e => setInput(e.target.value)} spellCheck={false}
        style={{ width: '100%', minHeight: 260, fontFamily: 'monospace', margin: '10px 0', padding: 14 }} />
      <button className="button primary" disabled={busy || !input} onClick={score}>{busy ? 'Processing…' : 'Validate and score'}</button>
      {errors && <pre role="alert" style={{ whiteSpace: 'pre-wrap', marginTop: 16 }}>{errors}</pre>}
    </div>
    <section className="panel" style={{ padding: 24 }}><h2>Saved assessments and inspections</h2>
      <label>Inspection finding and source<input aria-label="Fresh inspection finding" value={finding} maxLength={2000} onChange={e => setFinding(e.target.value)} style={{ width: '100%', margin: '12px 0', padding: 12 }} /></label>
      {!history.length && <p>No assessments yet. Submit a measured example or compatible file.</p>}
      {history.map(a => <article key={a.id} style={{ borderTop: '1px solid var(--border-subtle)', padding: '20px 0' }}>
        <h3>{a.asset_id} · {a.tool_life_id}</h3>
        <p><strong>{a.applicability.replaceAll('_', ' ')}</strong> · {a.action.replaceAll('_', ' ')} · {a.source_mode}</p>
        <div className="stats-grid"><div className="stat"><div>Benchmark score · next five cuts</div><div className="stat-number">{a.five_cut_score === null ? 'Unavailable' : (a.five_cut_score * 100).toFixed(1) + '%'}</div></div>
          <div className="stat"><div>Actionable window</div><div className="stat-number">{a.actionable_score === null ? 'Unavailable' : (a.actionable_score * 100).toFixed(1) + '%'}</div></div>
          <div className="stat"><div>Inspection break after cut</div><div className="stat-number">{a.inspection_slot ?? '—'}</div></div></div>
        <p>Evidence cutoff {a.cutoff} · Model {a.model_version || 'Unavailable'}</p>
        <p>{a.reason_codes.join(' · ')}. Scores are benchmark estimates. Monitor is not safety clearance.</p>
        <p>Review · {a.review.status}</p>
        <div style={{ display: 'flex', gap: 12 }}>
          {a.review.status === 'draft' && <><button className="button primary" disabled={busy} onClick={() => review(a, 'approve')}>Approve inspection</button><button className="button secondary" disabled={busy} onClick={() => review(a, 'dismiss')}>Dismiss inspection</button></>}
          {a.review.status === 'approved' && <button className="button primary" disabled={busy || !finding.trim()} onClick={() => review(a, 'complete')}>Complete inspection</button>}
          <a className="button secondary" href={`/api/fresh/assessments/${a.id}/export`} target="_blank" rel="noreferrer">Export assessment</a>
        </div>
        {a.review.history.map((h, i) => <p key={i}>{h.at} · {h.action} · {h.finding}</p>)}
      </article>)}
      {conflicts.length > 0 && <section aria-label="Conflicting deliveries"><h3>Quarantined deliveries · {conflicts.length}</h3>
        <p>Conflicting event IDs never replace the accepted evidence. These deliveries require review.</p>
        {conflicts.map(c => <p key={c.id}>{c.event_id} · {c.arrived_at}</p>)}
        <a href="/api/fresh/conflicts" target="_blank" rel="noreferrer">Open quarantined evidence</a>
      </section>}
    </section>
  </section>;
}
