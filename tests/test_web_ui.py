"""Tests for the HelloWorld Web UI."""

import json
import sys
import threading
import time
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from web_ui import HelloWorldWebUI, EventBus
from dispatcher import Dispatcher


@pytest.fixture
def ui_server(tmp_path):
    """Start a Web UI server on a free port, yield (url, ui), then shut down."""
    dispatcher = Dispatcher(vocab_dir=str(tmp_path))
    ui = HelloWorldWebUI(dispatcher=dispatcher, host="127.0.0.1", port=0)

    # Find a free port
    import socket
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()

    ui.port = port
    t = ui.start_background()
    time.sleep(0.3)  # let server start

    yield f"http://127.0.0.1:{port}", ui

    # No clean shutdown needed — daemon thread


def _get(url, path):
    resp = urlopen(f"{url}{path}")
    return json.loads(resp.read().decode())


def _post(url, path, body):
    data = json.dumps(body).encode()
    req = Request(f"{url}{path}", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urlopen(req)
    except HTTPError as e:
        # Read error body for 4xx responses (server returns JSON errors)
        return json.loads(e.read().decode())
    return json.loads(resp.read().decode())


# ------------------------------------------------------------------
# EventBus
# ------------------------------------------------------------------

def test_event_bus_publish_subscribe():
    bus = EventBus()
    q = bus.subscribe()
    bus.publish("test", {"key": "value"})
    assert len(q) == 1
    event_type, payload = q[0]
    assert event_type == "test"
    assert json.loads(payload) == {"key": "value"}


def test_event_bus_unsubscribe():
    bus = EventBus()
    q = bus.subscribe()
    bus.unsubscribe(q)
    bus.publish("test", {"key": "value"})
    assert len(q) == 0


def test_event_bus_multiple_subscribers():
    bus = EventBus()
    q1 = bus.subscribe()
    q2 = bus.subscribe()
    bus.publish("msg", {"data": 1})
    assert len(q1) == 1
    assert len(q2) == 1


# ------------------------------------------------------------------
# API endpoints
# ------------------------------------------------------------------

def test_root_returns_html(ui_server):
    url, _ = ui_server
    resp = urlopen(f"{url}/")
    html = resp.read().decode()
    assert "<!DOCTYPE html>" in html
    assert "HelloWorld" in html


def test_api_receivers(ui_server):
    url, _ = ui_server
    data = _get(url, "/api/receivers")
    assert "receivers" in data
    assert isinstance(data["receivers"], list)


def test_api_collisions(ui_server):
    url, _ = ui_server
    data = _get(url, "/api/collisions")
    assert "count" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["collisions"], list)


def test_api_agents_empty(ui_server):
    url, _ = ui_server
    data = _get(url, "/api/agents")
    assert data["agents"] == []


def test_api_eval(ui_server):
    url, ui = ui_server
    # Register a receiver first
    ui.dispatcher._get_or_create_receiver("TestR")
    data = _post(url, "/api/eval", {"source": "TestR"})
    assert "results" in data


def test_api_eval_empty_source(ui_server):
    url, _ = ui_server
    data = _post(url, "/api/eval", {"source": ""})
    assert "error" in data


def test_api_send(ui_server):
    url, _ = ui_server
    data = _post(url, "/api/send", {"receiver": "TestR", "content": "hello"})
    assert "msg_id" in data
    assert data["sender"] == "Human"


def test_api_send_missing_fields(ui_server):
    url, _ = ui_server
    data = _post(url, "/api/send", {"receiver": ""})
    assert "error" in data


def test_api_receiver_inbox(ui_server):
    url, _ = ui_server
    data = _get(url, "/api/receivers/TestR/inbox")
    assert "messages" in data


def test_api_receiver_detail_not_found(ui_server):
    url, _ = ui_server
    try:
        _get(url, "/api/receivers/NonExistent")
    except HTTPError as e:
        assert e.code == 404


# ------------------------------------------------------------------
# SSE events
# ------------------------------------------------------------------

def test_events_published_on_send(ui_server):
    url, ui = ui_server
    q = ui.events.subscribe()
    _post(url, "/api/send", {"receiver": "TestR", "content": "hello"})
    time.sleep(0.1)
    assert len(q) >= 1
    event_type, payload = q[0]
    assert event_type == "message"
    data = json.loads(payload)
    assert data["to"] == "TestR"


def test_events_published_on_eval(ui_server):
    url, ui = ui_server
    ui.dispatcher._get_or_create_receiver("EvalR")
    q = ui.events.subscribe()
    _post(url, "/api/eval", {"source": "EvalR"})
    time.sleep(0.1)
    assert len(q) >= 1
    event_type, _ = q[0]
    assert event_type == "eval"
