import { useCallback, useEffect, useRef, useState } from 'react';
import { Activity, ArrowDownToLine, ArrowRight, ArrowUpRight, BarChart3, Bell, Check, CheckCircle2, ChevronDown, ChevronRight, CircleHelp, Clock3, Database, ExternalLink, FileCheck2, FlaskConical, Gauge, Layers3, LayoutDashboard, LoaderCircle, Moon, Pause, Play, Plus, RotateCcw, Settings2, ShieldCheck, Sun, Unplug, Waves, X, Zap } from 'lucide-react';
import { api, decisionNames, policyNames, type Evaluation, type Policy, type Reading, type Run, type RunAction, type Tool, type WorkOrder } from './api';
import { useRun } from './useRun';
import { RiskChart } from './Chart';
import { MachineStage } from './MachineStage';
import { Fresh } from './Fresh';
import { Operations } from './Operations';

type View = 'floor' | 'analytics' | 'evidence' | 'source' | 'fresh' | 'operations';
type Health = Awaited<ReturnType<typeof api.health>>;
const number = new Intl.NumberFormat('en-US');
const percent = (value: number | null | undefined) => typeof value === 'number' && Number.isFinite(value) ? Math.round(value * 100) + '%' : '—';
const bytes = (value: number) => value < 1024 ? value + ' B' : value < 1024 * 1024 ? (value / 1024).toFixed(1) + ' kB' : (value / (1024 * 1024)).toFixed(2) + ' MB';
const date = (value: string | null | undefined) => value ? new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—';
const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'This operation could not be completed.';

function Brand({ small = false }: { small?: boolean }) {
  return <div className={'brand' + (small ? ' compact' : '')}><span className="brand-mark"><Activity size={21} strokeWidth={2.4} /></span>{!small && <span>KerfPulse <b>AI</b></span>}</div>;
}

function Stat({ icon, label, value, detail, accent = false }: { icon: React.ReactNode; label: string; value: React.ReactNode; detail: string; accent?: boolean }) {
  return <div className={'stat' + (accent ? ' accent' : '')}><div className="stat-label">{icon}{label}</div><div className="stat-number">{value}</div><div className="stat-detail">{detail}</div></div>;
}

function Empty({ icon = <Activity size={23} />, title, children }: { icon?: React.ReactNode; title: string; children: React.ReactNode }) {
  return <div className="empty-state"><span>{icon}</span><strong>{title}</strong><p>{children}</p></div>;
}

function RunCard({ run, selected, onClick }: { run: Run; selected: boolean; onClick: () => void }) {
  return <button className={'run-card' + (selected ? ' selected' : '')} onClick={onClick}>
    <span className="run-card-icon"><CircuitIcon /></span>
    <span className="run-card-content"><strong>Cutter {String(run.tool_id).padStart(2, '0')}</strong><span>{policyNames[run.policy]}</span><small><i className={'small-dot ' + (run.state === 'running' ? 'green' : '')} />{run.state} <b>·</b> Cut {run.last_cycle ?? '—'}</small></span>
    <ChevronRight size={15} />
  </button>;
}

function CircuitIcon() {
  return <svg width="41" height="41" viewBox="0 0 41 41" fill="none" aria-hidden="true"><path d="m8 14 13-5 12 6-13 5z" fill="currentColor" opacity=".25" /><path d="m8 14 12 6v14L8 28z" fill="currentColor" opacity=".5" /><path d="m20 20 13-5v14l-13 5z" fill="currentColor" opacity=".35" /><path d="m11 18 6 3v7l-6-3z" stroke="currentColor" /><path d="m23 23 7-3v6l-7 3z" stroke="currentColor" /><path d="m11 13 9-3 9 4-9 4z" stroke="currentColor" strokeWidth=".7" /></svg>;
}

function OrderCard({ order, planner, onAction, busy }: { order: WorkOrder; planner: boolean; onAction: (order: WorkOrder, action: 'approve' | 'dismiss' | 'complete') => void; busy: boolean }) {
  return <article className="order-card">
    <div className="order-card-title"><span className={'order-icon ' + order.status}><FileCheck2 size={17} /></span><div><strong>Inspect cutter {order.tool_id}</strong><span>Created after cut {order.cycle}</span></div><span className={'status-tag ' + order.status}>{order.status}</span></div>
    <div className="order-slot"><Clock3 size={14} /> Planned break after cut <b>{order.slot}</b></div>
    <p>{order.reason || 'Review the recorded sensor evidence before the next production break.'}</p>
    {order.finding && <p className="order-finding"><b>Finding</b> {order.finding}</p>}
    {planner && order.status === 'draft' && <div className="order-actions"><button className="button small primary" disabled={busy} onClick={() => onAction(order, 'approve')}><Check size={13} />Approve</button><button className="button small ghost" disabled={busy} onClick={() => onAction(order, 'dismiss')}>Dismiss</button></div>}
    {planner && order.status === 'approved' && <button className="button small secondary full" disabled={busy} onClick={() => onAction(order, 'complete')}><CheckCircle2 size={14} />Record completion</button>}
  </article>;
}

function ConfigDialog({ tools, onClose, onStart, busy }: { tools: Tool[]; onClose: () => void; onStart: (tool: number, policy: Policy, compare: boolean, speed: number, slot: number) => Promise<void>; busy: boolean }) {
  const [toolId, setToolId] = useState(tools.find((tool) => tool.tool_id === 9)?.tool_id ?? tools[0]?.tool_id ?? 2);
  const [policy, setPolicy] = useState<Policy>('current');
  const [compare, setCompare] = useState(true);
  const [speed, setSpeed] = useState(350);
  const [slot, setSlot] = useState(3);
  const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    close.current?.focus();
    const keyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !busy) onClose();
      if (event.key !== 'Tab') return;
      const elements = [...document.querySelectorAll<HTMLElement>('.dialog button:not(:disabled), .dialog select, .dialog input')];
      const first = elements[0]; const last = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown', keyDown);
    return () => document.removeEventListener('keydown', keyDown);
  }, [onClose, busy]);
  return <div className="modal-backdrop" onClick={() => !busy && onClose()}>
    <section className="dialog" role="dialog" aria-modal="true" aria-labelledby="config-title" onClick={(event) => event.stopPropagation()}>
      <div className="dialog-heading"><span className="dialog-icon"><Settings2 size={23} /></span><button ref={close} onClick={onClose} className="icon-button" aria-label="Close replay settings" disabled={busy}><X size={19} /></button></div>
      <span className="eyebrow">RECORDED INDUSTRIAL MEASUREMENTS</span><h2 id="config-title">Start a cutter replay</h2><p>Follow one measured tool life through the inspection workflow. Every policy receives the same recorded cuts.</p>
      <form onSubmit={(event) => { event.preventDefault(); void onStart(toolId, policy, compare, speed, slot); }}>
        <label>Cutter life<select value={toolId} onChange={(event) => setToolId(Number(event.target.value))}>{tools.map((tool) => <option key={tool.tool_id} value={tool.tool_id}>Cutter {tool.tool_id} · {tool.cycles ?? '—'} recorded cuts</option>)}</select></label>
        <label>Evidence policy<select value={policy} onChange={(event) => setPolicy(event.target.value as Policy)}><option value="decision">Decision-aware vibration</option><option value="periodic">Periodic · every fourth cut</option><option value="current">Current only</option><option value="fused">Always fused · resource reference</option></select></label>
        <div className="form-row"><label>Replay pace<select value={speed} onChange={(event) => setSpeed(Number(event.target.value))}><option value={1000}>1 cut per second</option><option value={350}>~3 cuts per second</option><option value={100}>10 cuts per second</option></select></label><label>Inspection slots<select value={slot} onChange={(event) => setSlot(Number(event.target.value))}><option value={3}>Every 3 cycle positions</option><option value={2}>Every 2 cycle positions</option><option value={1}>Every cycle position</option></select></label></div>
        <label className="checkbox-label"><input type="checkbox" checked={compare} onChange={(event) => setCompare(event.target.checked)} /><span><strong>Run a paired comparison</strong><small>Launch {policy === 'periodic' ? 'decision-aware' : 'periodic'} replay alongside this policy.</small></span></label>
        <div className="dialog-note"><ShieldCheck size={17} /><span>Predictions follow completed cuts. Damage and future labels stay outside the prediction inputs.</span></div>
        <button className="button primary full" type="submit" disabled={busy || !tools.length}>{busy ? <LoaderCircle size={16} className="spin" /> : <Play size={15} fill="currentColor" />}{busy ? 'Starting replay…' : 'Start replay'}<ArrowRight size={16} /></button>
      </form>
    </section>
  </div>;
}

export default function App() {
  const [view, setView] = useState<View>(new URLSearchParams(window.location.search).get('workspace') === 'operations' ? 'operations' : 'floor');
  const [theme, setTheme] = useState<'light' | 'dark'>(() => localStorage.getItem('kerfpulse-theme') === 'dark' ? 'dark' : 'light');
  const [tools, setTools] = useState<Tool[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [compareId, setCompareId] = useState<string | null>(null);
  const [role, setRole] = useState<'planner' | 'viewer'>('viewer');
  const [health, setHealth] = useState<Health | null>(null);
  const [loading, setLoading] = useState(true);
  const demoStarted = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [filter, setFilter] = useState('all');
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [evaluationState, setEvaluationState] = useState<'loading' | 'available' | 'unavailable'>('loading');
  const [queueOpen, setQueueOpen] = useState(true);
  const [completion, setCompletion] = useState<WorkOrder | null>(null);
  const [finding, setFinding] = useState('');
  const selected = useRun(activeId);
  const comparison = useRun(compareId);
  const snapshot = selected.snapshot;
  const run = snapshot?.run ?? null;
  const readings = snapshot?.readings ?? [];
  const latest = readings.length ? readings[readings.length - 1] : null;
  const latestCut = [...readings].reverse().find((reading) => reading.event_type === 'cut') ?? null;
  const tool = tools.find((item) => item.tool_id === run?.tool_id);
  const eligible = Math.max(run?.eligible_count ?? 0, readings.filter((reading) => reading.event_type === 'cut' && reading.quality === 'ok').length);
  const released = Math.max(run?.vibration_count ?? 0, readings.filter((reading) => reading.vibration_released).length);
  const quota = Math.floor(eligible / 4);
  const model = latestCut?.decision?.model_version;
  const openOrders = snapshot?.work_orders.filter((order) => ['draft', 'approved'].includes(order.status)) ?? [];
  const planned = openOrders[0];
  const dark = theme === 'dark';
  const title = { floor: 'Shop floor', analytics: 'Performance', evidence: 'Evidence audit', source: 'Data & method', fresh: 'New cut assessment', operations: 'Operations' }[view];

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('kerfpulse-theme', theme);
  }, [theme]);

  const initialize = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const session = await api.session();
      setRole(session.role);
      const [toolList, runList, system] = await Promise.all([api.tools(), api.runs(), api.health()]);
      setTools(toolList); setRuns(runList); setHealth(system);
      const storedActive = sessionStorage.getItem('kerfpulse-active-run');
      const storedCompare = sessionStorage.getItem('kerfpulse-compare-run');
      const restored = runList.some((item) => item.id === storedActive) ? storedActive : runList[0]?.id ?? null;
      setActiveId(restored);
      setCompareId(runList.some((item) => item.id === storedCompare && item.id !== restored) ? storedCompare : null);
      void api.evaluation().then((result) => { setEvaluation(result); setEvaluationState('available'); }).catch(() => setEvaluationState('unavailable'));
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    if (view !== 'operations' && !demoStarted.current) {
      demoStarted.current = true;
      void initialize();
    }
  }, [initialize, view]);

  useEffect(() => {
    if (view === 'operations') return;
    const timer = window.setInterval(() => {
      void api.health().then(setHealth).catch(() => setHealth(null));
      void api.runs().then(setRuns).catch(() => {});
    }, 5000);
    return () => window.clearInterval(timer);
  }, [view]);
  useEffect(() => {
    if (loading) return;
    if (activeId) sessionStorage.setItem('kerfpulse-active-run', activeId);
    else sessionStorage.removeItem('kerfpulse-active-run');
    if (compareId) sessionStorage.setItem('kerfpulse-compare-run', compareId);
    else sessionStorage.removeItem('kerfpulse-compare-run');
  }, [activeId, compareId, loading]);

  async function start(toolId: number, policy: Policy, compare: boolean, speed: number, slot: number) {
    setBusy(true); setError(null);
    try {
      const created = await api.start({ tool_id: toolId, policy, speed_ms: speed, slot_interval: slot });
      setRuns((previous) => [created, ...previous]);
      setActiveId(created.id); setCompareId(null); setConfigOpen(false); setView('floor');
      if (compare) {
        const paired = await api.start({ tool_id: toolId, policy: policy === 'periodic' ? 'decision' : 'periodic', speed_ms: speed, slot_interval: slot });
        setRuns((previous) => [created, paired, ...previous.filter((item) => item.id !== created.id)]);
        setCompareId(paired.id);
      }
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }

  async function control(action: RunAction) {
    if (!run) return;
    setBusy(true); setError(null);
    try {
      await api.control(run.id, action);
      const pairedState = comparison.snapshot?.run.state;
      const shouldControlPair = action === 'restart' || action === 'pause' && pairedState === 'running' || action === 'resume' && pairedState === 'paused';
      if (compareId && shouldControlPair) await api.control(compareId, action);
      selected.refresh(); comparison.refresh();
      setRuns(await api.runs());
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }

  async function orderAction(order: WorkOrder, action: 'approve' | 'dismiss' | 'complete') {
    if (action === 'complete') { setCompletion(order); setFinding(''); return; }
    setBusy(true); setError(null);
    try { await api.workOrder(order.run_id, order.id, action); selected.refresh(); }
    catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }

  async function finishOrder(event: React.FormEvent) {
    event.preventDefault();
    if (!completion || !finding.trim()) return;
    setBusy(true); setError(null);
    try { await api.workOrder(completion.run_id, completion.id, 'complete', finding.trim()); setCompletion(null); selected.refresh(); }
    catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }

  const activeRuns = runs.map((item) => item.id === run?.id ? run : item);
  const totalBytes = run?.wire_bytes ?? 0;
  const visibleReadings = readings.filter((reading) => filter === 'all'
    || (filter === 'actionable' && reading.decision?.status === 'inspect')
    || (filter === 'deferred' && reading.decision?.status === 'deferred')
    || (filter === 'quality' && reading.quality !== 'ok')).slice().reverse();
  const streamLabel = selected.connection === 'connected' ? 'Stream connected' : selected.connection === 'reconnecting' ? 'Reconnecting' : run ? 'Connecting' : 'Ready to replay';
  const workerAt = health?.mqtt?.worker_at;
  const workerFresh = Boolean(workerAt && Date.now() - new Date(workerAt).getTime() < 30000);

  return <div className="app-shell">
    <aside className="icon-rail">
      <Brand small />
      <nav aria-label="Main navigation">
        {[{ id: 'floor', icon: <LayoutDashboard size={20} />, name: 'Shop floor' }, { id: 'analytics', icon: <BarChart3 size={20} />, name: 'Performance' }, { id: 'evidence', icon: <Waves size={20} />, name: 'Evidence audit' }, { id: 'source', icon: <Database size={20} />, name: 'Data and method' }].map((item) => <button key={item.id} className={'rail-button' + (view === item.id ? ' active' : '')} onClick={() => setView(item.id as View)} aria-label={item.name} aria-current={view === item.id ? 'page' : undefined} title={item.name}>{item.icon}</button>)}
      </nav>
      <div className="rail-bottom"><button className="rail-button" onClick={() => setView('source')} aria-label="Research provenance" title="Research provenance"><CircleHelp size={20} /></button><div className="avatar">KP</div></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><Brand /><span className="header-divider" /><span className="workspace-label">Machining intelligence <ChevronDown size={13} /></span><div className="topbar-actions"><div className="telemetry-label"><span className="small-dot orange" />{view === 'operations' ? 'Named operational access' : view === 'fresh' ? 'Completed-cut assessment' : 'Recorded telemetry replay'}</div><div className="theme-switch" aria-label="Color theme"><button className={!dark ? 'selected' : ''} onClick={() => setTheme('light')} aria-label="Light theme" aria-pressed={!dark}><Sun size={15} /></button><button className={dark ? 'selected' : ''} onClick={() => setTheme('dark')} aria-label="Dark theme" aria-pressed={dark}><Moon size={15} /></button></div><span className="role-badge">{view === 'operations' ? 'Named access' : role === 'planner' ? 'Planner' : 'Viewer'}</span></div></header>
      <main>
        <div className="page-heading"><div><div className="breadcrumb">Workspace <ChevronRight size={12} /> Steel machining <ChevronRight size={12} /><span>{title}</span></div><h1>{title}<span className="heading-dot">.</span></h1><p>{view === 'floor' ? 'Every cut. A clearer maintenance decision.' : view === 'analytics' ? 'Compare warning timing with evidence use and review workload.' : view === 'evidence' ? 'Trace each recommendation to its completed cut and model.' : view === 'fresh' ? 'New evidence. Traceable forecasts. Human decisions.' : view === 'operations' ? 'Assigned machines. Traceable source health. Named access.' : 'Measured tool lives. Explicit evaluation boundaries.'}</p></div><div className="heading-actions">{view !== 'operations' && <>{run && <a href={api.export(run.id)} download className="button secondary"><ArrowDownToLine size={15} /><span>Export run</span></a>}<button className="button primary" onClick={() => setConfigOpen(true)} disabled={loading || !tools.length || role !== 'planner'}><Plus size={16} />New replay</button></>}</div></div>
        {view !== 'operations' && (error || selected.error || comparison.error) && <div className="error-banner" role="alert"><Unplug size={17} /><span>{error || selected.error || comparison.error}</span><button onClick={() => { setError(null); selected.refresh(); if (!tools.length) void initialize(); }}>Retry</button><button className="tiny-icon" onClick={() => setError(null)} aria-label="Dismiss error"><X size={15} /></button></div>}
        {loading && view !== 'operations' && <div className="loading-banner"><LoaderCircle size={17} className="spin" />Connecting to the replay service…</div>}

        <button className="button primary" style={{ marginBottom: 20 }} disabled={loading && view !== 'operations'} onClick={() => setView('fresh')}>Score a New Cut</button>
        <button className="button secondary" style={{ marginBottom: 20, marginLeft: 12 }} onClick={() => setView('operations')}>Operations workspace</button>
        {view === 'operations' && <Operations />}
        {view === 'fresh' && !loading && <Fresh />}
        {view === 'floor' && <>
          <div className="run-toolbar"><div className="run-context"><span className={'status-indicator ' + (run?.state ?? 'ready')} /><strong>{run ? 'Cutter ' + String(run.tool_id).padStart(2, '0') : 'No active replay'}</strong><span className="toolbar-separator" /><span>{run ? policyNames[run.policy] : 'Haas VF-1 · 42CrMo4'}</span>{run && <span className={'status-tag ' + run.state}>{run.state}</span>}</div><div className="run-controls"><span className="connection-label"><span className={'small-dot ' + (selected.connection === 'connected' ? 'green' : '')} />{streamLabel}</span>{run && <><button className="icon-button" onClick={() => void control(run.state === 'running' ? 'pause' : 'resume')} disabled={busy || role !== 'planner' || run.state === 'completed'} aria-label={run.state === 'running' ? 'Pause replay' : 'Resume replay'} title={run.state === 'running' ? 'Pause replay' : 'Resume replay'}>{run.state === 'running' ? <Pause size={15} /> : <Play size={15} />}</button><button className="icon-button" onClick={() => void control('restart')} disabled={busy || role !== 'planner'} aria-label="Restart replay" title="Restart replay"><RotateCcw size={15} /></button></>}</div></div>
          <div className={'floor-grid' + (!queueOpen ? ' queue-collapsed' : '')}><MachineStage run={run} latest={latestCut} tool={tool} remainingBudget={Math.max(0, quota - released)} /><section className="queue-panel panel"><div className="panel-heading"><div><Bell size={17} /><h2>Inspection queue</h2><span className="count-badge">{openOrders.length}</span></div><button className="tiny-icon queue-collapse" onClick={() => setQueueOpen(!queueOpen)} aria-label={queueOpen ? 'Collapse inspection queue' : 'Expand inspection queue'}><ChevronRight size={17} /></button></div>{queueOpen && <div className="queue-body">{snapshot?.work_orders.length ? snapshot.work_orders.map((order) => <OrderCard key={order.id} order={order} planner={role === 'planner'} onAction={(item, action) => void orderAction(item, action)} busy={busy} />) : <Empty icon={<FileCheck2 size={25} />} title="No inspection requested">{run ? 'A draft appears when the model finds a feasible inspection window.' : 'Start a cutter replay to follow evidence into a planned inspection.'}</Empty>}<div className="queue-note"><Clock3 size={15} /><div><strong>{run ? 'Break every ' + run.slot_interval + ' cycle positions' : 'Production-aware planning'}</strong><p>Slots use the replay calendar. Planner approval is recorded.</p></div></div></div>}</section></div>
          <div className="asset-dock"><div className="dock-header"><span className="eyebrow">CUTTER REPLAYS</span><span>{activeRuns.length} in this session</span></div><div className="run-card-grid">{activeRuns.slice(0, 4).map((item) => <RunCard key={item.id} run={item} selected={activeId === item.id} onClick={() => { if (item.id === compareId) { setCompareId(activeId); } setActiveId(item.id); }} />)}{activeRuns.length < 4 && <button className="add-run-card" onClick={() => setConfigOpen(true)} disabled={!tools.length || role !== 'planner'}><Plus size={19} /><span>{activeRuns.length ? 'Add cutter replay' : 'Start your first replay'}</span><ArrowUpRight size={14} /></button>}</div></div>
          <div className="stats-grid"><Stat icon={<Gauge size={15} />} label="Next 5 cuts · benchmark risk" value={percent(latestCut?.decision?.risk)} detail={latestCut?.decision?.status ? decisionNames[latestCut.decision.status] : 'Awaiting a completed cut'} accent /><Stat icon={<Layers3 size={15} />} label="Vibration feature releases" value={<>{released}<small> / {quota}</small></>} detail={run?.policy === 'fused' ? 'Always-fused resource reference' : 'Allowance · floor(eligible cuts ÷ 4)'} /><Stat icon={<Clock3 size={15} />} label="Upcoming inspection" value={planned ? <>Cut {planned.slot}</> : '—'} detail={planned ? 'Planner status · ' + planned.status : 'No open inspection order'} /><Stat icon={<ArrowUpRight size={15} />} label="Measured telemetry payload" value={bytes(totalBytes)} detail={run ? eligible + ' eligible completed cuts' : 'Counted at the virtual gateway'} /></div>
          <section className="panel chart-panel"><div className="panel-heading"><div><Activity size={17} /><h2>Risk across completed cuts</h2></div><button className="text-button" onClick={() => setView('analytics')}>View performance <ArrowUpRight size={14} /></button></div><div className="chart-legend"><span><i className="line orange" />5-cut damage risk</span><span><i className="line green dashed" />Actionable risk</span>{compareId && <span><i className="line blue" />Paired policy</span>}<span><i className="diamond" />Vibration released</span><small>Cut ordinal →</small></div>{readings.length ? <RiskChart readings={readings} compareReadings={comparison.snapshot?.readings} dark={dark} compact /> : <Empty icon={<Activity size={24} />} title="The first cut starts the curve">Replay recorded measurements to inspect each forecast in sequence.</Empty>}</section>
        </>}

        {view === 'analytics' && <>
          <section className="panel analytics-controls"><div><h2>{run ? 'Cutter ' + run.tool_id + ' · ' + policyNames[run.policy] : 'Select a replay'}</h2><p>Results describe recorded warning and inspection timing.</p></div><div className="comparison-select"><label htmlFor="compare-run">Compare with</label><select id="compare-run" value={compareId ?? ''} onChange={(event) => setCompareId(event.target.value || null)}><option value="">No comparison</option>{activeRuns.filter((item) => item.id !== activeId).map((item) => <option key={item.id} value={item.id}>Cutter {item.tool_id} · {policyNames[item.policy]}</option>)}</select></div></section>
          <div className="stats-grid"><Stat icon={<Gauge size={15} />} label="Latest actionable risk" value={percent(latestCut?.decision?.actionable_risk)} detail="Within a feasible inspection horizon" accent /><Stat icon={<Waves size={15} />} label="Vibration release rate" value={eligible ? percent(released / eligible) : '—'} detail={released + ' releases / ' + eligible + ' eligible cuts'} /><Stat icon={<FileCheck2 size={15} />} label="Inspection drafts" value={snapshot?.work_orders.length ?? '—'} detail="Includes approved and dismissed drafts" /><Stat icon={<ArrowDownToLine size={15} />} label="Telemetry payload" value={bytes(totalBytes)} detail="Serialized observations received" /></div>
          <section className="panel chart-panel"><div className="panel-heading"><div><Activity size={17} /><h2>Risk and evidence release</h2></div><span className="panel-meta">Causal, cut-by-cut replay</span></div><div className="chart-legend"><span><i className="line orange" />Selected policy</span><span><i className="line green dashed" />Actionable risk</span>{compareId && <span><i className="line blue" />Paired policy</span>}<span><i className="diamond" />Vibration released</span></div>{readings.length ? <RiskChart readings={readings} compareReadings={comparison.snapshot?.readings} dark={dark} /> : <Empty title="Replay performance will appear here">Start a run to measure release usage and forecast progression.</Empty>}</section>
          <div className="two-column"><section className="panel"><div className="panel-heading"><div><FlaskConical size={17} /><h2>Paired policy outcomes</h2></div></div>{run ? <div className="comparison-table"><div className="comparison-row heading"><span>Measure</span><span>{policyNames[run.policy]}</span><span>{comparison.snapshot ? policyNames[comparison.snapshot.run.policy] : 'No comparison'}</span></div>{[['Completed source cycle', run.last_cycle ?? '—', comparison.snapshot?.run.last_cycle ?? '—'], ['Eligible cuts', eligible, comparison.snapshot?.run.eligible_count ?? '—'], ['Vibration releases', released, comparison.snapshot?.run.vibration_count ?? '—'], ['Telemetry payload', bytes(totalBytes), comparison.snapshot ? bytes(comparison.snapshot.run.wire_bytes) : '—'], ['Inspection drafts', snapshot?.work_orders.length ?? 0, comparison.snapshot?.work_orders.length ?? '—']].map(([label, first, second]) => <div className="comparison-row" key={String(label)}><span>{label}</span><strong>{first}</strong><strong>{second}</strong></div>)}<p className="table-note">{compareId && comparison.snapshot?.run.tool_id !== run.tool_id ? 'These runs use different cutters. Compare resource usage descriptively.' : 'The paired replay uses the same recorded cutter life. Measured damage remains in the archive after a recommendation.'}</p></div> : <Empty title="Choose a cutter replay">Run paired policies to compare their evidence and inspection workload.</Empty>}</section><section className="panel"><div className="panel-heading"><div><ShieldCheck size={17} /><h2>Held-out policy benchmark</h2></div></div><div className="evaluation-summary">{evaluationState === 'available' && evaluation ? <EvaluationPanel evaluation={evaluation} /> : <><span className="evaluation-symbol"><FlaskConical size={28} /></span><h3>{evaluationState === 'loading' ? 'Checking evaluation artifact' : 'Offline evaluation pending'}</h3><p>Whole-cutter holdout results appear once training and evaluation artifacts are present. Live replay values describe this selected run.</p></>}</div></section></div>
          <EvidenceTable readings={visibleReadings} filter={filter} setFilter={setFilter} />
        </>}

        {view === 'evidence' && <>
          <div className="evidence-summary"><div className="panel evidence-model"><span className="eyebrow">MODEL LINEAGE</span><h2>{model ?? 'Awaiting model evidence'}</h2><p>{latestCut?.source_version ?? 'Pinned Figshare v1'} · Generation {run?.generation ?? '—'}</p><span><ShieldCheck size={15} />Predictions use completed-cut inputs</span></div><div className="panel evidence-model"><span className="eyebrow">LATEST DECISION</span><h2>{latestCut?.decision?.status ? decisionNames[latestCut.decision.status] : 'Awaiting a completed cut'}</h2><p>{latestCut?.decision?.reason ?? 'Start a replay to inspect the decision trail.'}</p></div></div>
          <EvidenceTable readings={visibleReadings} filter={filter} setFilter={setFilter} />
          <div className="two-column"><FeaturePanel title="Current evidence" icon={<Zap size={17} />} features={latestCut?.features?.current} subtitle="500 Hz source · completed-cut summaries" /><FeaturePanel title="Vibration evidence" icon={<Waves size={17} />} features={latestCut?.features?.vibration} subtitle="25 kHz source · released when available" /></div>
        </>}

        {view === 'source' && <div className="source-content">
          <section className="panel source-hero"><span className="source-seal"><ShieldCheck size={28} /></span><div><span className="eyebrow">REPRODUCIBLE INDUSTRIAL DATA</span><h2>A measured foundation for every decision.</h2><p>KerfPulse AI replays cutter lives from a Haas VF-1 machining 42CrMo4 steel. Each forecast uses information available after the selected cut.</p><a className="text-button" target="_blank" rel="noreferrer" href="https://pmc.ncbi.nlm.nih.gov/articles/PMC12006439/">Read the dataset paper <ExternalLink size={14} /></a></div></section>
          <div className="source-grid"><section className="panel source-card"><Database size={23} /><h3>14 measured cutter lives</h3><p>968 recorded cycles, 120 signal features, and process metadata. The release covers controlled tests on one Haas VF-1.</p><dl><div><dt>Material</dt><dd>42CrMo4 steel</dd></div><div><dt>License</dt><dd>CC BY 4.0</dd></div><div><dt>Release</dt><dd>Figshare v1</dd></div></dl><a href="https://doi.org/10.6084/m9.figshare.28589216.v1" target="_blank" rel="noreferrer" className="text-button">Open pinned data <ArrowUpRight size={14} /></a></section><section className="panel source-card"><Waves size={23} /><h3>Two evidence paths</h3><p>Twelve current channels at 500 Hz and eight vibration channels at 25 kHz. Replays transmit aggregate features from completed cycles.</p><dl><div><dt>Current summaries</dt><dd>72 features</dd></div><div><dt>Vibration summaries</dt><dd>48 features</dd></div><div><dt>Budgeted release</dt><dd>floor(n ÷ 4)</dd></div></dl><span className="source-footnote">The budget controls optional feature transmission.</span></section><section className="panel source-card"><FileCheck2 size={23} /><h3>Explicit data quality</h3><p>Original cycle ordinals remain visible. Gaps, conflicting records, and insufficient evidence produce their own decision states.</p><dl><div><dt>Missing cycle positions</dt><dd>21</dd></div><div><dt>Conflicting cycle</dt><dd>Tool 2 · cut 34</dd></div><div><dt>First-cut damage</dt><dd>Tool 11</dd></div></dl><span className="source-footnote">Future outcomes stay outside prediction inputs.</span></section></div>
          <section className="panel method-panel"><div className="panel-heading"><div><FlaskConical size={17} /><h2>What the experiment measures</h2></div></div><div className="method-grid"><div><span className="method-icon"><Gauge size={19} /></span><h3>Useful warning</h3><p>Whether an inspection is proposed two to five cuts before observed damage and scheduled before that damage.</p></div><div><span className="method-icon"><Layers3 size={19} /></span><h3>Evidence under a cap</h3><p>Decision-aware and periodic policies share a prefix allowance of one vibration release per four eligible cuts.</p></div><div><span className="method-icon"><Clock3 size={19} /></span><h3>A feasible intervention</h3><p>The calendar defines available breaks. The planner records approval, dismissal, and an inspection finding.</p></div></div></section>
          <section className="panel source-credits"><h3>Dataset attribution</h3><p>Grzegorz Piecuch and Tomasz Żabiński, <em>A new open dataset from a milling process – data for classification and estimation of tool life</em>, Scientific Data 12, 650 (2025). Adaptations include parsing, feature selection, duplicate quarantine, and replay. Dataset © its creators under <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a>.</p><p>Model estimates describe this benchmark. The showcase records inspection decisions against archived outcomes. Field validation and customer-specific commissioning remain deployment milestones.</p></section>
        </div>}

        <footer><span>Precision in every signal. Certainty in every shift.</span><div><span className={'small-dot ' + (view !== 'operations' && workerFresh ? 'green' : '')} />{view === 'operations' ? 'Source status shown per assigned machine' : workerFresh ? 'MQTT worker online' : health ? 'Service online' : 'Service unavailable'}<span>·</span><span>CC BY 4.0 source data</span></div></footer>
      </main>
    </div>
    {configOpen && <ConfigDialog tools={tools} onClose={() => setConfigOpen(false)} onStart={start} busy={busy} />}
    {completion && <div className="modal-backdrop"><form className="dialog" onSubmit={(event) => void finishOrder(event)} role="dialog" aria-modal="true" aria-labelledby="complete-title"><div className="dialog-heading"><span className="dialog-icon"><CheckCircle2 size={23} /></span><button type="button" className="icon-button" aria-label="Close completion form" onClick={() => setCompletion(null)}><X size={19} /></button></div><h2 id="complete-title">Record inspection completion</h2><p>Cutter {completion.tool_id} · Planned break after cut {completion.slot}. Record the actual finding and its source.</p><label>Inspection finding<textarea value={finding} onChange={(event) => setFinding(event.target.value)} required maxLength={2000} autoFocus placeholder="Describe the finding and whether this is a replay exercise or observed inspection." /></label><button className="button primary full" type="submit" disabled={busy || !finding.trim()}>{busy ? <LoaderCircle size={16} className="spin" /> : <CheckCircle2 size={16} />}Save completion</button></form></div>}
  </div>;
}

function EvidenceTable({ readings, filter, setFilter }: { readings: Reading[]; filter: string; setFilter: (filter: string) => void }) {
  return <section className="panel evidence-table"><div className="panel-heading"><div><Waves size={17} /><h2>Decision evidence</h2></div><span className="panel-meta">{readings.length} records</span></div><div className="table-filters" aria-label="Filter evidence">{[['all', 'All cuts'], ['actionable', 'Inspection'], ['deferred', 'Budget deferred'], ['quality', 'Data quality']].map(([value, label]) => <button key={value} className={filter === value ? 'active' : ''} onClick={() => setFilter(value)}>{label}</button>)}</div>{readings.length ? <div className="table-scroll"><table><thead><tr><th>Cut</th><th>Benchmark risk</th><th>Evidence</th><th>Decision</th><th>Planned break</th><th>Replay time</th></tr></thead><tbody>{readings.slice(0, 100).map((reading) => <tr key={reading.generation + '-' + reading.cycle + '-' + reading.event_type}><td className="mono">#{String(reading.cycle).padStart(3, '0')}<small>{reading.quality !== 'ok' ? reading.quality : reading.event_type === 'damage' ? 'Observed damage' : ''}</small></td><td className="mono">{percent(reading.decision?.risk)}</td><td><span className={'evidence-pill ' + (reading.vibration_released ? 'vibration' : '')}>{reading.vibration_released ? <><Waves size={12} />Current + vibration</> : reading.event_type === 'cut' ? <><Zap size={12} />Current</> : 'Quality event'}</span></td><td><span className={'decision-status ' + (reading.decision?.status ?? reading.event_type)}><i />{reading.decision?.status ? decisionNames[reading.decision.status] : reading.event_type === 'damage' ? 'Damage observed' : 'Data quality'}</span>{reading.decision?.reason && <small className="decision-reason">{reading.decision.reason}</small>}</td><td className="mono">{reading.decision?.slot ? 'Cut ' + reading.decision.slot : '—'}</td><td className="mono muted">{date(reading.replay_at)}</td></tr>)}</tbody></table>{readings.length > 100 && <div className="table-note">Showing the latest 100 matching records. Export the run for its full history.</div>}</div> : <Empty title="No matching evidence">{filter === 'all' ? 'Accepted cut records will appear as the replay progresses.' : 'No records match this filter in the selected replay.'}</Empty>}</section>;
}

function FeaturePanel({ title, icon, features, subtitle }: { title: string; icon: React.ReactNode; features?: Record<string, unknown>; subtitle: string }) {
  const entries = Object.entries(features ?? {}).filter(([, value]) => typeof value === 'number');
  return <section className="panel feature-panel"><div className="panel-heading"><div>{icon}<h2>{title}</h2></div></div><p className="feature-subtitle">{subtitle}</p>{entries.length ? <dl className="feature-list">{entries.slice(0, 10).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{number.format(Number(Number(value).toFixed(4)))}</dd></div>)}</dl> : <Empty icon={icon} title="No released feature values">This panel updates when the selected cut carries these features.</Empty>}</section>;
}

function EvaluationPanel({ evaluation }: { evaluation: Evaluation }) {
  const { policy, report } = evaluation;
  const total = policy.all_tools || 14;
  const summary = policy.summary ?? {};
  const policies: Policy[] = ['current', 'periodic', 'decision', 'fused'];
  const best = policies.reduce((selected, name) =>
    (summary[name]?.timely ?? 0) > (summary[selected]?.timely ?? 0) ? name : selected, 'current' as Policy);
  const paired = policy.paired_tool_bootstrap;
  return <>
    <div className="benchmark-headline"><strong>{summary[best]?.timely ?? 0}<small> / {total}</small></strong><span>timely scheduled inspections<br /><b>{policyNames[best]} · strongest observed coverage</b></span></div>
    <div className="benchmark-legend"><span><i className="green" />Timely</span><span><i className="amber" />Premature</span><span><i className="red" />Late</span><span><i />No inspection</span></div>
    <div className="benchmark-bars">{policies.map((name) => <div className="benchmark-row" key={name}><div><span>{policyNames[name]}</span><b>{summary[name]?.timely ?? 0}/{total}</b></div><div className="benchmark-track" aria-label={policyNames[name] + ': ' + (summary[name]?.timely ?? 0) + ' timely of ' + total + ' cutters'}>{(['timely', 'premature', 'late', 'no_inspection'] as const).map((status) => <i key={status} className={status} style={{ width: ((summary[name]?.[status] ?? 0) / total * 100) + '%' }} title={status.replace('_', ' ') + ': ' + (summary[name]?.[status] ?? 0)} />)}</div></div>)}</div>
    <div className="benchmark-details"><span><ShieldCheck size={13} />{policy.prefix_violations} prefix quota violations</span><span>{policy.observable_tools} observable cutter lives · {total} total events</span></div>
    {paired && <p className="table-note">Decision-aware minus periodic coverage {Math.round(paired.difference * 100)} percentage points. Cutter bootstrap 95% interval {paired.percentile_95_interval.map((value) => Math.round(value * 100)).join(' to ')} points.</p>}
    {report.metrics && <div className="benchmark-models"><div className="benchmark-model-row heading"><span>Prediction head</span><span>AP</span><span>Brier</span></div>{Object.entries(report.metrics).map(([head, metrics]) => <div className="benchmark-model-row" key={head}><span>{head === 'age' ? 'Age + recipe' : head === 'current' ? 'Current + context' : 'Fused + context'}</span><b>{metrics.average_precision.toFixed(3)}</b><b>{metrics.brier.toFixed(3)}</b></div>)}</div>}
    <p className="benchmark-caveat">{report.protocol === 'workpiece' ? 'Tool and shared-workpiece groups held out.' : 'Held-out predictions.'} These are recorded scheduling scenarios. Prevented damage is unobserved.</p>
  </>;
}
