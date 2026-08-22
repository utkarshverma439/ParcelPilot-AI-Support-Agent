import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from fastapi.testclient import TestClient


def _make_mock_session():
    session = MagicMock()

    accounts = {
        "ACCT-001": MagicMock(
            account_id="ACCT-001", account_name="Northstar Logistics",
            plan="Enterprise", status="active", csm="Alice",
            premium_support=True, notes="Key account",
        ),
        "ACCT-002": MagicMock(
            account_id="ACCT-002", account_name="LumenWorks",
            plan="Growth", status="active", csm="Bob",
            premium_support=False, notes=None,
        ),
    }

    orders = {
        "ORD-1001": MagicMock(
            order_id="ORD-1001", account_id="ACCT-001", carrier="Delhivery",
            status="booked", booked_at="2026-08-10", pickup_window_start="2026-08-12T09:00",
            pickup_window_end="2026-08-12T12:00", pickup_actual_at=None,
            shipment_fee_inr=1500.0, carrier_fault=False, customer_fault=False,
            cancellation_requested_at=None, notes="Standard shipment",
        ),
    }

    tickets = {
        "TKT-501": MagicMock(
            ticket_id="TKT-501", account_id="ACCT-001", created_at="2026-08-15",
            status="open", subject="Pickup delay", description="Pickup is late",
            channel="email", assigned_to="support_agent",
            last_customer_message_at="2026-08-16", historical_resolution=None,
        ),
    }

    def _query(model):
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        q.all.return_value = []
        return q

    def _smart_query(model):
        q = MagicMock()

        def _filter(*args, **kwargs):
            inner = MagicMock()
            inner._model = model

            def _first():
                return None

            def _all():
                return []

            inner.first = _first
            inner.all = _all
            return inner

        q.filter = _filter
        return q

    session.query = _smart_query

    def _patched_query(model):
        results_map = {
            "Account": accounts,
            "Order": orders,
            "Ticket": tickets,
        }
        store = results_map.get(model.__name__, {})

        q = MagicMock()

        def make_filter(filter_args):
            inner = MagicMock()

            def _first():
                return None

            def _all():
                return list(store.values())

            inner.first = _first
            inner.all = _all
            return inner

        q.filter = make_filter
        return q

    session.query = _patched_query

    return session


@pytest.fixture
def client():
    mock_vs = MagicMock()
    mock_vs.search.return_value = []
    mock_vs.collection.count.return_value = 0

    mock_session_factory = MagicMock(return_value=_make_mock_session())

    with patch("app.main.VectorStore", return_value=mock_vs), \
         patch("app.main.init_db", return_value=mock_session_factory), \
         patch("app.main.run_ingestion"), \
         patch("app.main.SessionLocal", mock_session_factory):
        from app import main
        main.SessionLocal = mock_session_factory
        from app.main import app
        with TestClient(app) as c:
            yield c


@pytest.fixture
def mock_llm():
    with patch("app.agent.graph.call_llm") as mock:
        mock.return_value = "Test response from LLM."
        yield mock


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "parcelpilot-ai-support"


class TestChatEndpoint:
    def test_chat_unknown_user_returns_401(self, client):
        resp = client.post("/chat", json={
            "message": "Hello",
            "user_id": "nonexistent_user",
        })
        assert resp.status_code == 401

    def test_chat_valid_request(self, client, mock_llm):
        resp = client.post("/chat", json={
            "message": "What is the support policy?",
            "user_id": "support_agent",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "request_id" in data
        assert "confidence" in data
        assert data["confidence"] in ("high", "medium", "low")

    def test_chat_returns_citations_list(self, client, mock_llm):
        resp = client.post("/chat", json={
            "message": "What are the cancellation terms?",
            "user_id": "support_agent",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["citations"], list)
        assert isinstance(data["tool_calls"], list)

    def test_chat_customer_scoped(self, client, mock_llm):
        resp = client.post("/chat", json={
            "message": "Show me my orders",
            "user_id": "customer_northstar",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data

    def test_chat_access_denied_cross_account(self, client, mock_llm):
        resp = client.post("/chat", json={
            "message": "Show me LumenWorks orders",
            "user_id": "customer_northstar",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "Access denied" in data["response"]


class TestSourcesEndpoint:
    def test_get_source_by_id(self, client):
        resp = client.get("/sources/01_Support_Policy_v3_CURRENT.pdf")
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_name"] == "Support Policy v3"
        assert data["status"] == "CURRENT"
        assert data["source_priority"] == 80

    def test_get_source_not_found(self, client):
        resp = client.get("/sources/nonexistent.pdf")
        assert resp.status_code == 404

    def test_get_source_search(self, client):
        resp = client.get("/sources/Northstar")
        assert resp.status_code == 200
        data = resp.json()
        assert "matches" in data


class TestOpsIssuesEndpoint:
    def test_ops_issues_internal(self, client):
        resp = client.get("/ops/issues?user_id=operations_admin")
        assert resp.status_code == 200
        data = resp.json()
        assert "issues" in data
        assert "count" in data

    def test_ops_issues_customer_forbidden(self, client):
        resp = client.get("/ops/issues?user_id=customer_northstar")
        assert resp.status_code == 403


class TestActionsEndpoint:
    def test_confirm_nonexistent_action(self, client):
        resp = client.post("/actions/nonexistent/confirm")
        assert resp.status_code == 400
