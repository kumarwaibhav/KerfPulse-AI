"""Durable operational receipt consumer; inference and outbox commit atomically."""
import logging
import signal
import threading
import time
from pdm.store import Store, utcnow
from pdm.device_ingest import DeviceIngest
from pdm.operational_processing import OperationalProcessing


def main():
    logging.basicConfig(level=logging.INFO)
    stop=threading.Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set())
    signal.signal(signal.SIGINT,lambda *_:stop.set())
    store=Store();store.initialize();DeviceIngest(store).initialize()
    processor=OperationalProcessing(store)
    heartbeat=0.
    try:
        while not stop.is_set():
            try:
                if time.monotonic()>=heartbeat:
                    store.status('assessment_worker_at',utcnow())
                    heartbeat=time.monotonic()+10
                if processor.process_one() is None: stop.wait(1)
            except Exception as error:
                logging.error('Assessment transaction failed; retained for retry; type=%s',type(error).__name__)
                stop.wait(2)
    finally:store.close()


if __name__=='__main__':main()
