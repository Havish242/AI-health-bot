import json
from app import app


def test_history_roundtrip():
    client = app.test_client()

    # ensure clean start
    r = client.post('/history/clear')
    assert r.status_code == 200

    # send a chat message
    r = client.post('/chat', json={'message': 'unit test message', 'use_ai': False})
    assert r.status_code == 200
    jr = r.get_json()
    assert 'reply' in jr

    # fetch history
    r = client.get('/history')
    assert r.status_code == 200
    jr = r.get_json()
    assert 'history' in jr
    hist = jr['history']
    assert isinstance(hist, list)
    assert len(hist) >= 1
    # last entry should match
    last = hist[-1]
    assert last.get('user') == 'unit test message'
    assert 'reply' in last

    # clear and verify empty
    r = client.post('/history/clear')
    assert r.status_code == 200
    r = client.get('/history')
    assert r.status_code == 200
    jr = r.get_json()
    assert jr.get('history') == []
