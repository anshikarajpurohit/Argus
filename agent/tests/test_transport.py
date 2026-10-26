import time
from unittest.mock import Mock
import requests
from edr_agent.transport import Transport

def eventually(predicate,seconds=5):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if predicate():return
        time.sleep(.03)
    assert predicate()

def test_outage_retry_and_batch(monkeypatch,cfg):
    session=Mock();session.headers={};response=Mock();response.raise_for_status.return_value=None
    session.post.side_effect=[requests.ConnectionError(),response];monkeypatch.setattr(requests,'Session',lambda:session)
    transport=Transport(cfg)
    try:
        for i in range(200):transport.add({'eventId':str(i)})
        eventually(lambda:session.post.call_count>=2);eventually(lambda:not transport.events)
        assert len(session.post.call_args.kwargs['json']['events'])==200
    finally:transport.close()

def test_queue_bound_and_immediate_alert(monkeypatch,cfg):
    session=Mock();session.headers={};monkeypatch.setattr(requests,'Session',lambda:session)
    transport=Transport(cfg)
    try:
        transport.alert({'alertId':'a'});eventually(lambda:session.post.called,1)
        assert session.post.call_args.args[0].endswith('/api/alerts')
        with transport.cv:
            for i in range(5001):transport.events.append({'eventId':str(i)})
            assert len(transport.events)==5000 and transport.events[0]['eventId']=='1'
            transport.events.clear()
    finally:transport.close()


def test_alert_does_not_wait_for_event_backoff(monkeypatch,cfg):
    from threading import Event
    failed=Event();delivered=Event();session=Mock();session.headers={}
    def post(url,**kwargs):
        if url.endswith('/api/events/batch'):
            failed.set();raise requests.ConnectionError()
        delivered.set();return Mock()
    session.post.side_effect=post;monkeypatch.setattr(requests,'Session',lambda:session)
    transport=Transport(cfg)
    try:
        for i in range(200):transport.add({'eventId':str(i)})
        assert failed.wait(1)
        transport.alert({'alertId':'priority'})
        assert delivered.wait(.8)
    finally:transport.close()
