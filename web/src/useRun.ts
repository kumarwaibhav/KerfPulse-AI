import { useCallback, useEffect, useState } from 'react';
import { api, type Run, type Reading, type Snapshot, type Update, type WorkOrder } from './api';

function replaceById<T extends { id: string }>(items: T[], item: T): T[] {
  const found = items.findIndex((entry) => entry.id === item.id);
  if (found === -1) return [...items, item];
  return items.map((entry) => entry.id === item.id ? item : entry);
}

export function useRun(runId: string | null) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [connection, setConnection] = useState<'idle' | 'connecting' | 'connected' | 'reconnecting'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);

  useEffect(() => {
    setSnapshot(null);
    setError(null);
    if (!runId) {
      setConnection('idle');
      return;
    }
    let source: EventSource | null = null;
    let cancelled = false;
    const abort = new AbortController();
    setConnection('connecting');

    api.snapshot(runId, abort.signal).then((initial) => {
      if (cancelled) return;
      setSnapshot(initial);
      source = new EventSource(api.events(runId, initial.cursor));
      source.onopen = () => { setConnection('connected'); setError(null); };
      source.onerror = () => setConnection('reconnecting');
      source.addEventListener('update', (event) => {
        if (cancelled) return;
        let update: Update;
        try {
          update = JSON.parse((event as MessageEvent<string>).data) as Update;
        } catch {
          setError('An unreadable update was received. Reload this run to recover.');
          return;
        }
        setSnapshot((previous) => {
          if (!previous) return previous;
          if (update.kind === 'state') {
            const run = update.data as Run;
            if (run.generation < previous.run.generation) return previous;
            if (run.generation > previous.run.generation) {
              return { ...previous, run, readings: [], work_orders: [] };
            }
            return { ...previous, run };
          }
          if (update.data.generation !== previous.run.generation) return previous;
          if (update.kind === 'work_order') {
            return { ...previous, work_orders: replaceById(previous.work_orders, update.data as WorkOrder) };
          }
          const reading = update.data as Reading;
          const alreadyReceived = previous.readings.some((item) =>
            item.cycle === reading.cycle && item.event_type === reading.event_type
          );
          const readings = alreadyReceived
            ? previous.readings
            : [...previous.readings, reading].sort((first, second) => first.cycle - second.cycle);
          return {
            ...previous,
            readings,
            run: {
              ...previous.run,
              last_cycle: reading.cycle,
              updated_at: reading.received_at || reading.replay_at,
            },
          };
        });
      });
    }).catch((failure: unknown) => {
      if (cancelled || abort.signal.aborted) return;
      setError(failure instanceof Error ? failure.message : 'This run could not be loaded.');
      setConnection('reconnecting');
    });

    return () => {
      cancelled = true;
      abort.abort();
      source?.close();
    };
  }, [runId, revision]);

  return { snapshot, connection, error, refresh };
}
