"""Bounded asynchronous queues with idempotent retries and exponential backoff."""
import logging
import time
from collections import deque
from threading import Condition, Thread

import requests


class Transport:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.events = deque(maxlen=5000)
        self.alerts = deque(maxlen=5000)
        self.cv = Condition()
        self.stopped = False
        self.session = self._session()
        self.worker = Thread(target=self.run, daemon=True)
        self.worker.start()

    def _session(self) -> requests.Session:
        session = requests.Session()
        session.headers['x-agent-key'] = self.cfg['agent_api_key']
        return session

    def add(self, event: dict) -> None:
        with self.cv:
            self.events.append(event)
            self.cv.notify()

    def alert(self, alert: dict) -> None:
        with self.cv:
            self.alerts.append(alert)
            self.cv.notify()

    def settings(self) -> dict | None:
        try:
            response = requests.get(self.cfg['backend_url'] + '/api/settings',
                                    headers={'x-agent-key': self.cfg['agent_api_key']}, timeout=2)
            response.raise_for_status()
            data = response.json()
            if (data.get('responseMode') in ('suspend', 'alert_only')
                    and 0 <= data['warningThreshold'] < data['criticalThreshold'] <= 100
                    and isinstance(data['processAllowlist'], list)):
                return data
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass
        return None

    def run(self) -> None:
        next_flush = time.monotonic() + 2
        retry_at = {'events': 0, 'alerts': 0}
        delay = {'events': 1, 'alerts': 1}
        while not self.stopped:
            now = time.monotonic()
            with self.cv:
                if self.alerts and now >= retry_at['alerts']:
                    channel = 'alerts'
                    batch = list(self.alerts)[:1]
                elif (self.events and now >= retry_at['events']
                      and (len(self.events) >= 200 or now >= next_flush)):
                    channel = 'events'
                    batch = list(self.events)[:200]
                else:
                    self.cv.wait(timeout=.1)
                    continue
            is_alert = channel == 'alerts'
            try:
                response = self.session.post(
                    self.cfg['backend_url'] + ('/api/alerts' if is_alert else '/api/events/batch'),
                    json=batch[0] if is_alert else {'events': batch}, timeout=3)
                response.raise_for_status()
            except requests.RequestException:
                if delay[channel] == 1:
                    logging.warning('Backend delivery failed for %s; buffering and retrying', channel)
                retry_at[channel] = time.monotonic() + delay[channel]
                delay[channel] = min(delay[channel] * 2, 30)
                # Drop failed keep-alive connections after a backend restart.
                self.session.close()
                self.session = self._session()
                continue
            with self.cv:
                pending = self.alerts if is_alert else self.events
                key = 'alertId' if is_alert else 'eventId'
                sent = {event[key] for event in batch}
                remaining = [event for event in pending if event[key] not in sent]
                pending.clear()
                pending.extend(remaining)
            delay[channel] = 1
            retry_at[channel] = 0
            if not is_alert:
                next_flush = time.monotonic() + 2

    def close(self) -> None:
        self.stopped = True
        with self.cv:
            self.cv.notify_all()
        self.worker.join(timeout=4)
        if self.events or self.alerts:
            logging.warning('Shutdown with unsent in-memory records; queues are not durable')
        self.session.close()
