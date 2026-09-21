import signal
import time

import structlog

from app.core.events.dispatcher import dispatch_once
from app.core.logging import configure_logging

configure_logging()
log = structlog.get_logger("worker.outbox")

INTERVAL_SECONDS = 1.0
_running = True


def _stop(*_):
    global _running
    _running = False


def main() -> None:
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    log.info("outbox_worker_started")
    while _running:
        try:
            n = dispatch_once()
            if n == 0:
                time.sleep(INTERVAL_SECONDS)
        except Exception as e:
            log.exception("outbox_worker_error", error=str(e))
            time.sleep(INTERVAL_SECONDS)
    log.info("outbox_worker_stopped")


if __name__ == "__main__":
    main()