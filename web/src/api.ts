export type Policy = 'decision' | 'periodic' | 'current' | 'fused';
export type RunState = 'running' | 'paused' | 'completed';
export type DecisionStatus = 'monitor' | 'inspect' | 'insufficient_evidence' | 'no_feasible_slot' | 'deferred';
export type OrderStatus = 'draft' | 'approved' | 'dismissed' | 'completed';
export type RunAction = 'pause' | 'resume' | 'restart';
export type OrderAction = 'approve' | 'dismiss' | 'complete';

export interface Tool {
  tool_id: number;
  cycles?: number;
  recipe?: Record<string, string | number | null>;
  [key: string]: unknown;
}

export interface Run {
  id: string;
  tool_id: number;
  policy: Policy;
  speed_ms: number;
  slot_interval: number;
  state: RunState;
  generation: number;
  last_cycle: number | null;
  eligible_count: number;
  vibration_count: number;
  wire_bytes: number;
  created_at: string;
  updated_at: string;
}

export interface RunInput {
  tool_id: number;
  policy: Policy;
  speed_ms: number;
  slot_interval: number;
}

export interface Decision {
  risk?: number | null;
  actionable_risk?: number | null;
  status: DecisionStatus;
  slot?: number | null;
  reason?: string | null;
  model_version?: string | null;
  threshold?: number | null;
}

export interface Reading {
  schema_version: string | number;
  run_id: string;
  generation: number;
  source_version: string;
  tool_id: number;
  cycle: number;
  replay_at: string;
  received_at?: string;
  event_type: 'cut' | 'gap' | 'damage';
  quality: 'ok' | 'gap' | 'conflict' | 'unsupported' | 'missing';
  decision?: Decision | null;
  features?: { current?: Record<string, unknown>; vibration?: Record<string, unknown> };
  vibration_released?: boolean;
  wire_bytes?: number;
}

export interface WorkOrder {
  id: string;
  run_id: string;
  generation: number;
  tool_id: number;
  cycle: number;
  slot: number;
  status: OrderStatus;
  reason: string | null;
  model_version: string | null;
  finding: string | null;
  created_at: string;
  updated_at: string;
}

export interface Snapshot {
  run: Run;
  readings: Reading[];
  work_orders: WorkOrder[];
  cursor: string | number;
}

export interface Evaluation {
  report: {
    protocol?: string;
    metrics?: Record<string, { n: number; positive_cuts: number; average_precision: number; brier: number }>;
    source?: string;
    source_sha256?: string;
    selection?: string;
    model_artifact_sha256?: string;
  };
  policy: {
    all_tools: number;
    observable_tools: number;
    prefix_violations: number;
    summary: Record<Policy, Record<string, number>>;
    results: { tool_id: number; policy: Policy; first_slot: number | null; damage_cycle: number; eligible_cuts: number; releases: number; outcome: string }[];
    paired_tool_bootstrap?: { difference: number; percentile_95_interval: number[] };
    interpretation?: string;
  };
  source?: Record<string, unknown>;
}

export type FreshEvent = Record<string, unknown>;

export interface FreshSchema {
  feature_schema_version: string;
  sensor_profile_version?: string;
  context_fields: string[];
  feature_fields: string[];
  example?: FreshEvent;
  examples?: { supported?: FreshEvent; unsupported?: FreshEvent };
  live_connection?: { status: string; label: string };
}

export interface FreshReviewEntry {
  action?: string;
  status?: string;
  actor?: string;
  at?: string;
  created_at?: string;
  finding?: string | null;
  reason?: string | null;
}

export interface FreshAssessment {
  id: string;
  event_id: string;
  asset_id: string;
  tool_life_id: string;
  sequence_number: number;
  source_mode: string;
  cutoff: string;
  arrived_at: string;
  clock_basis?: string;
  data_origin?: string;
  applicability: string;
  reason_codes: string[];
  five_cut_score: number | null;
  actionable_score: number | null;
  action: string;
  inspection_slot: number | null;
  model_version: string | null;
  feature_schema_version: string;
  sensor_profile_version?: string;
  policy_version: string;
  evidence_digest: string;
  review: { status: string; version: number; history: FreshReviewEntry[]; finding?: string | null };
}

export interface FreshBatchRow {
  row: number;
  assessment?: FreshAssessment;
  errors?: { field: string; message: string }[];
}

export type Update =
  | { kind: 'state'; data: Run }
  | { kind: 'reading'; data: Reading }
  | { kind: 'work_order'; data: WorkOrder };

export const policyNames: Record<Policy, string> = {
  decision: 'Decision-aware',
  periodic: 'Periodic vibration',
  current: 'Current only',
  fused: 'Always fused',
};

export const decisionNames: Record<DecisionStatus, string> = {
  monitor: 'Monitoring',
  inspect: 'Inspection recommended',
  insufficient_evidence: 'Insufficient evidence',
  no_feasible_slot: 'No feasible slot',
  deferred: 'Evidence deferred',
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: 'same-origin',
    ...options,
    headers: { accept: 'application/json', ...options?.headers },
  });
  if (!response.ok) {
    let message = 'Request failed (' + response.status + ')';
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // The service may be temporarily unavailable before its first start.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

function post<T>(path: string, body: object = {}): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function runPath(id: string) {
  return '/api/runs/' + encodeURIComponent(id);
}

function assessmentPath(id: string) {
  return '/api/fresh/assessments/' + encodeURIComponent(id);
}

export const api = {
  session: () => request<{ role: 'planner' | 'viewer' }>('/api/session'),
  tools: () => request<Tool[]>('/api/tools'),
  runs: () => request<Run[]>('/api/runs'),
  start: (input: RunInput) => post<Run>('/api/runs', input),
  snapshot: (id: string, signal?: AbortSignal) => request<Snapshot>(runPath(id), { signal }),
  control: (id: string, action: RunAction) => post<Run>(runPath(id) + '/' + action),
  events: (id: string, cursor: Snapshot['cursor']) => runPath(id) + '/events?after=' + encodeURIComponent(cursor),
  export: (id: string) => runPath(id) + '/export',
  workOrder: (id: string, orderId: string, action: OrderAction, finding?: string) =>
    post<WorkOrder>(
      runPath(id) + '/work-orders/' + encodeURIComponent(orderId) + '/' + action,
      finding === undefined ? {} : { finding },
    ),
  health: () => request<{ status: string; database: string; mqtt?: { worker_at?: string | null; last_ingest_at?: string | null }; dataset: boolean; model: boolean }>('/healthz'),
  evaluation: () => request<Evaluation>('/api/evaluation'),
  freshSchema: () => request<FreshSchema>('/api/fresh/schema'),
  freshAssessments: () => request<FreshAssessment[]>('/api/fresh/assessments'),
  freshAssessment: (id: string) => request<FreshAssessment>(assessmentPath(id)),
  scoreCuts: (events: FreshEvent[]) => post<{ results: FreshBatchRow[] }>('/api/fresh/assessments', { events }),
  reviewCut: (id: string, action: OrderAction, expectedVersion: number, finding?: string) =>
    post<FreshAssessment>(assessmentPath(id) + '/review', { action, expected_version: expectedVersion, finding }),
};
