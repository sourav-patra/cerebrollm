"""Pace Ollama embed calls so Windows does not run out of ephemeral TCP ports.

On this machine Ollama opens about 3.4 TCP connections per embedded text to its model runner (measured:
10 requests of 16 texts left 537 sockets in TIME_WAIT). Windows holds a closed socket 120 s and offers
16,384 ports, so an unpaced bge-m3 index run exhausted the range ("Only one usage of each socket address",
HTTP 400) and would fail other agents' calls too. MAX_TEXTS_PER_SECOND keeps the steady state near 10,000
sockets. A call that still hits the error waits BACKOFF_SECONDS (ports free after 120 s) and retries.
"""
import time

MAX_TEXTS_PER_SECOND = 25      # 1,500 chunks/min, the ceiling every model shares in this study
BACKOFF_SECONDS = 130
ERROR_TEXT = 'Only one usage of each socket address'
backoff_total = 0.0            # seconds spent in backoff; reports subtract it from active time
_next = 0.0


def _is_port_error(e):
    body = getattr(getattr(e, 'response', None), 'text', '')
    return ERROR_TEXT in str(e) or ERROR_TEXT in body


def paced(call, n_texts):
    """Run call() after waiting for the pace slot of n_texts; retry after the port-exhaustion error."""
    global _next, backoff_total
    for _ in range(6):
        now = time.monotonic()
        if _next > now:
            time.sleep(_next - now)
        _next = max(now, _next) + n_texts / MAX_TEXTS_PER_SECOND
        try:
            return call()
        except Exception as e:
            if not _is_port_error(e):
                raise
            time.sleep(BACKOFF_SECONDS)
            backoff_total += BACKOFF_SECONDS
    raise RuntimeError('embed call failed 6 times with port exhaustion')
