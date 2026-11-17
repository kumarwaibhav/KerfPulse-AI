"""Measure actual concurrent replay via HTTP and SSE against an isolated local stack."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Barrier
import time

import httpx


def percentile(values, fraction):
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, int(len(ordered) * fraction))], 3) if ordered else None


def exercise(url, cookie, index, start_gate, end_time, results):
    with httpx.Client(base_url=url, cookies=cookie, timeout=httpx.Timeout(20)) as client:
        start_gate.wait(timeout=30)
        run = client.post("/api/runs", json={"tool_id": 2, "policy": "periodic", "speed_ms": 100}).raise_for_status().json()
        path = "/api/runs/" + run["id"]
        cursor = 0
        while time.monotonic() < end_time[0]:
            reading_cycles = []
            completed = False
            with client.stream("GET", path + "/events", headers={"Last-Event-ID": str(cursor)}) as stream:
                stream.raise_for_status()
                for line in stream.iter_lines():
                    if time.monotonic() > end_time[0] + 5:
                        break
                    if line.startswith("id: "):
                        cursor = int(line[4:])
                    if not line.startswith("data: "):
                        continue
                    message = json.loads(line[6:])
                    row = message["data"]
                    if row["generation"] != run["generation"]:
                        continue
                    if message["kind"] == "reading":
                        reading_cycles.append(row["cycle"])
                        now = datetime.now(timezone.utc)
                        generated = datetime.fromisoformat(row["replay_at"])
                        received = datetime.fromisoformat(row["received_at"])
                        if time.monotonic() <= end_time[0]:
                            results["event_times"].append(time.monotonic())
                            results["latencies_ms"].append((now - generated).total_seconds() * 1000)
                            results["ingest_ms"].append((received - generated).total_seconds() * 1000)
                    elif message["kind"] == "state" and row["state"] == "completed":
                        completed = True
                        break
            if reading_cycles != list(range(1, len(reading_cycles) + 1)) or completed and len(reading_cycles) != 50:
                results["failures"].append({"worker": index, "cycles": reading_cycles})
            if completed:
                results["completed"] += 1
            if time.monotonic() < end_time[0]:
                run = client.post(path + "/restart", json={}).raise_for_status().json()
    return results


def run(args):
    if not 1 <= args.workers <= 16:
        raise ValueError("Workers must be between 1 and 16")
    cookies = []
    for _ in range((args.workers + 2) // 3):
        with httpx.Client(base_url=args.url, timeout=10) as session:
            session.get("/api/session").raise_for_status()
            cookies.append(dict(session.cookies))
    end_time = [0.0]
    start_time = [0.0]

    def mark_start():
        start_time[0] = time.monotonic()
        end_time[0] = start_time[0] + args.seconds

    start_gate = Barrier(args.workers, action=mark_start)
    failures, latencies, ingest, event_times = [], [], [], []
    completed = 0
    all_results = [{"latencies_ms": [], "ingest_ms": [], "event_times": [], "completed": 0, "failures": []}
                   for _ in range(args.workers)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(exercise, args.url, cookies[index // 3], index, start_gate, end_time, all_results[index])
                   for index in range(args.workers)]
        for index, future in enumerate(futures):
            try:
                future.result()
            except Exception as error:
                failures.append({"worker": index, "error": str(error)})
            result = all_results[index]
            latencies.extend(result["latencies_ms"])
            ingest.extend(result["ingest_ms"])
            event_times.extend(result["event_times"])
            completed += result["completed"]
            failures.extend(result["failures"])
    windows = [sum(start_time[0] + offset <= value < start_time[0] + offset + 60 for value in event_times)
               for offset in range(0, args.seconds, 60)]
    report = {"measurement": "gateway creation through MQTT, PostgreSQL and HTTP SSE consumption",
              "seconds": args.seconds, "concurrent_replays": args.workers, "completed_generations": completed,
              "events": len(event_times), "events_per_second": len(event_times) / args.seconds,
              "events_per_minute_window": windows, "sse_ms": {f"p{p}": percentile(latencies, p / 100) for p in (50, 95, 99)},
              "ingest_p95_ms": percentile(ingest, .95), "failures": failures,
              "target_passed": args.seconds >= 600 and all(n >= 1200 for n in windows) and bool(latencies)
              and percentile(latencies, .95) < 2000 and not failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18087")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--output", type=Path, default=Path("artifacts/replay-stress.json"))
    run(parser.parse_args())
