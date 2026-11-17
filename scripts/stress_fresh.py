"""Open-loop HTTP load using repeated measured features, never simulated sensors.

This checks synchronous assessment throughput, not fresh physical ingestion or SSE.
Every event declares a demonstration clock and publisher benchmark origin.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import http.cookiejar
import json
from pathlib import Path
import statistics
import time
import urllib.request
import uuid


def client(base):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    with opener.open(base + '/api/session', timeout=30) as response:
        response.read()
    with opener.open(base + '/api/fresh/schema', timeout=30) as response:
        example = json.load(response)['example']
    return opener, example


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--rate', type=int, default=10)
    parser.add_argument('--output', default='artifacts/fresh-http-load.json')
    args = parser.parse_args()
    total = args.seconds * args.rate
    if not 1 <= total <= 1200 or not 1 <= args.rate <= 100:
        parser.error('Use 1..1200 events and 1..100 events/second')
    owners = [client(args.url) for _ in range(4)]
    started = time.perf_counter()

    def submit(index, due):
        opener, example = owners[index % len(owners)]
        event = {**example, 'event_id': str(uuid.uuid4()), 'tool_life_id': 'load-' + uuid.uuid4().hex,
                 'cut_completed_at': datetime.now(timezone.utc).isoformat()}
        request = urllib.request.Request(args.url + '/api/fresh/assessments', data=json.dumps({'events': [event]}).encode(),
                                         headers={'Content-Type': 'application/json'})
        began = time.perf_counter()
        try:
            with opener.open(request, timeout=30) as response:
                result = json.load(response)['results'][0]
            if 'errors' in result:
                return {'error': result['errors'], 'seconds': time.perf_counter()-began}
            return {'id': result['assessment']['id'], 'seconds': time.perf_counter()-began,
                    'scheduled_seconds': time.perf_counter()-due}
        except Exception as error:
            return {'error': str(error), 'seconds': time.perf_counter()-began}

    with ThreadPoolExecutor(max_workers=32) as pool:
        futures = []
        for index in range(total):
            due = started + index / args.rate
            time.sleep(max(0, due - time.perf_counter()))
            futures.append(pool.submit(submit, index, due))
        results = [future.result() for future in as_completed(futures)]
    elapsed = time.perf_counter()-started
    successful = [row for row in results if 'id' in row]
    stored = 0
    for opener, _ in owners:
        with opener.open(args.url+'/api/fresh/assessments', timeout=30) as response:
            stored += len(json.load(response))

    def distribution(field):
        values = sorted(row[field] for row in successful)
        return {'p50_ms': statistics.median(values)*1000, 'p95_ms': values[max(0, int(len(values)*.95+.999)-1)]*1000,
                'max_ms': max(values)*1000} if values else None

    report = {'at': datetime.now(timezone.utc).isoformat(), 'workload': 'Repeated real publisher feature vector; new event/tool identities; demonstration clock. Not physical telemetry.',
              'path': 'HTTP -> release inference -> PostgreSQL assessment commit -> HTTP response',
              'offered_rate_per_second': args.rate, 'offered_events': total, 'schedule_seconds': args.seconds,
              'elapsed_seconds': elapsed, 'successful_events': len(successful), 'error_count': len(results)-len(successful),
              'unique_assessments': len({row['id'] for row in successful}), 'stored_assessments': stored,
              'completed_per_second': len(successful)/elapsed, 'request_latency': distribution('seconds'),
              'scheduled_to_response': distribution('scheduled_seconds'), 'errors': [row['error'] for row in results if 'error' in row],
              'limits': 'Short bounded HTTP test. No sustained 600-second or event-to-SSE capacity claim. Four demo session owners, 32 clients maximum.'}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
