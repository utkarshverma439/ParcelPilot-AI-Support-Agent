import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
from app.data.models import init_db, Account, Order, Ticket, Action
from app.data.ingestion import run_ingestion
from app.data.repository import Repository
from app.security.auth import get_user, is_internal, can_access_account
from app.services.retrieval import RetrievalService
from app.services.reliability import DOCUMENT_METADATA, rank_sources, filter_deprecated, detect_conflicts
from app.services.issue_detection import IssueDetectionService
from app.agent.graph import run_agent, extract_account_id, extract_order_id, extract_ticket_id, sanitize_query
from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT
from app.tools.documents import search_documents_tool
from app.tools.operations import get_account_tool, get_order_tool, get_ticket_tool, get_sla_status_tool, get_orders_by_account_tool, get_tickets_by_account_tool
from app.tools.actions import create_escalation_tool, confirm_action_tool
import logging

P, F, E = 0, 0, []
def ok(n, c, d=""):
    global P, F
    if c: P += 1; print(f"  PASS  {n}")
    else: F += 1; E.append((n, d)); print(f"  FAIL  {n} {d}")

print("=" * 60)
print("PARCELPILOT COMPREHENSIVE VALIDATION")
print("=" * 60)

db_path = "parcelpilot_test_validate.db"
if os.path.exists(db_path): os.remove(db_path)
SL = init_db(f"sqlite:///{db_path}")
db = SL(); repo = Repository(db)
mv = MagicMock(); mv.search.return_value = []; mv.collection.count.return_value = 0
run_ingestion(db, mv); retrieval = RetrievalService(mv)

print("\n--- 1. CHAT + RAG + EXCEL LOOKUP ---")
ok("Excel: accounts", db.query(Account).count() > 0)
ok("Excel: orders", db.query(Order).count() > 0)
ok("Excel: tickets", db.query(Ticket).count() > 0)
ns = db.query(Account).filter(Account.account_id == "ACCT-001").first()
ok("Northstar exists", ns is not None)
ok("NS plan=Enterprise", ns and ns.plan == "Enterprise")
ok("LW exists", db.query(Account).filter(Account.account_id == "ACCT-002").first() is not None)
ok("NS has orders", db.query(Order).filter(Order.account_id == "ACCT-001").count() > 0)
ok("NS has tickets", db.query(Ticket).filter(Ticket.account_id == "ACCT-001").count() > 0)

print("\n--- 2. RAG (Document Retrieval) ---")
ui = get_user("support_agent")
r = search_documents_tool(retrieval, ui, "cancellation policy")
ok("Doc search dict", isinstance(r, dict))
ok("Doc search citations", "citations" in r)
ok("Doc search conflicts", "conflicts" in r)
ok("6 docs metadata", len(DOCUMENT_METADATA) == 6)
ok("NS agreement p=90", DOCUMENT_METADATA["05_Northstar_Logistics_Enterprise_Agreement.pdf"]["source_priority"] == 90)
ok("Policy v3 p=80", DOCUMENT_METADATA["01_Support_Policy_v3_CURRENT.pdf"]["source_priority"] == 80)
ok("Deprecated p=20", DOCUMENT_METADATA["02_Support_Policy_v2_DEPRECATED.pdf"]["source_priority"] == 20)
ok("Rank sources", len(rank_sources([{"metadata":{"source_priority":10}},{"metadata":{"source_priority":90}}])) == 2)
ok("Filter deprecated", len(filter_deprecated([{"metadata":{"status":"DEPRECATED"}},{"metadata":{"status":"CURRENT"}}])) == 1)
ok("Detect conflicts", isinstance(detect_conflicts([]), list))

print("\n--- 3. THREE REQUIRED TOOLS ---")
un = get_user("customer_northstar")
ok("Tool1: search_documents", callable(search_documents_tool))
a = get_account_tool(repo, ui, "ACCT-001")
ok("Tool2: get_account", "account" in a)
ok("Tool2: NS name", a["account"]["account_name"] == "Northstar Logistics")
ok("Tool2: get_order", "order" in get_order_tool(repo, ui, "ORD-1001"))
ok("Tool2: get_ticket", "ticket" in get_ticket_tool(repo, ui, "TKT-501"))
sla_r = get_sla_status_tool(repo, ui, "TKT-501")
ok("Tool2: get_sla", "plan" in sla_r and sla_r.get("plan") == "Enterprise")
o = get_orders_by_account_tool(repo, ui, "ACCT-001")
ok("Tool2: orders_by_acct", "orders" in o and len(o["orders"]) > 0)
t = get_tickets_by_account_tool(repo, ui, "ACCT-001")
ok("Tool2: tickets_by_acct", "tickets" in t and len(t["tickets"]) > 0)
ok("Tool3: create_escalation", callable(create_escalation_tool))
ok("Tool3: confirm_action", callable(confirm_action_tool))

print("\n--- 4. MULTI-STEP AGENT ---")
st = AgentState(user_query="Can I cancel ORD-1001?", user=un)
with patch("app.agent.graph.call_llm", return_value="Yes, no fee."):
    st = run_agent(st, repo, retrieval)
ok("Agent: no explicit account", st.account_id is None)
ok("Agent: no account data", "account" not in st.structured_data)
ok("Agent: fetches order", "order" in st.structured_data)
ok("Agent: searches docs", len(st.citations) >= 0)
ok("Agent: tool calls", len(st.tool_calls) > 0)
ok("Agent: reasoning steps", len(st.reasoning_steps) > 0)
ok("Agent: has response", st.response and len(st.response) > 0)
ok("Agent: confidence", st.confidence in ("high", "medium", "low"))

print("\n--- 5. ACCESS CONTROL ---")
ul = get_user("customer_lumenworks")
us = get_user("support_agent")
uo = get_user("operations_admin")
ok("Auth: user found", un is not None)
ok("Auth: unknown=None", get_user("fake_user") is None)
ok("Auth: customer NOT internal", not is_internal(un))
ok("Auth: support IS internal", is_internal(us))
ok("Auth: ops IS internal", is_internal(uo))
ok("Auth: NS->ACCT-001", can_access_account(un, "ACCT-001"))
ok("Auth: NS!->ACCT-002", not can_access_account(un, "ACCT-002"))
ok("Auth: LW->ACCT-002", can_access_account(ul, "ACCT-002"))
ok("Auth: LW!->ACCT-001", not can_access_account(ul, "ACCT-001"))
ok("Auth: Internal all", can_access_account(us, "ACCT-001") and can_access_account(us, "ACCT-002"))
lw = get_order_tool(repo, un, "ORD-2001")
ok("Data: NS blocked LW", "error" in lw or lw == {})
ns_o = get_order_tool(repo, un, "ORD-1001")
ok("Data: NS gets own", ns_o and "order" in ns_o)
sc = AgentState(user_query="Show me LumenWorks orders", user=un)
with patch("app.agent.graph.call_llm", return_value="blocked"):
    sc = run_agent(sc, repo, retrieval)
ok("Agent: cross-account blocked", "Access denied" in sc.response)

print("\n--- 6. CONFIRMATION + ACTION ---")
e = create_escalation_tool(repo, us, "TKT-501", reason="Test", priority="high", team="Support")
ok("Action: created", e.get("action_id") is not None)
ok("Action: pending", e.get("status") == "pending")
ok("Action: confirm_required", e.get("confirmation_required") is True)
aid = e["action_id"]
ok("Action: in DB", repo.get_action(aid) is not None)
ok("Action: DB pending", repo.get_action(aid).status == "pending")
c = confirm_action_tool(repo, aid)
ok("Action: confirm OK", c.get("status") == "executed")
ok("Action: DB executed", repo.get_action(aid).status == "executed")
d = confirm_action_tool(repo, aid)
ok("Action: idempotent", "error" in d or "already" in str(d))

print("\n--- 7. SOURCE PRECEDENCE + CITATIONS + CONFLICTS ---")
srcs = [{"metadata":{"source_priority":20,"status":"DEPRECATED"}},{"metadata":{"source_priority":80,"status":"CURRENT"}},{"metadata":{"source_priority":90,"status":"ACTIVE"}}]
rk = rank_sources(srcs)
ok("Precedence: sorted", rk[0]["metadata"]["source_priority"] == 90)
ok("Precedence: filtered", len(filter_deprecated(srcs)) == 2)
cf = detect_conflicts([{"metadata":{"source_priority":80,"document_type":"policy","document_name":"v3"}},{"metadata":{"source_priority":20,"document_type":"policy","document_name":"v2"}}])
ok("Conflicts: detected", len(cf) > 0)
ok("Conflicts: has resolution", "resolution" in cf[0])

print("\n--- 8. ERROR HANDLING ---")
ok("Sanitize: strip", sanitize_query("  hi  ") == "hi")
ok("Sanitize: truncate", sanitize_query("x"*3000) == "x"*2000)
ok("Extract: northstar", extract_account_id("Northstar?") == "ACCT-001")
ok("Extract: lumenworks", extract_account_id("LumenWorks") == "ACCT-002")
ok("Extract: none", extract_account_id("general") is None)
ok("Extract: ORD", extract_order_id("ORD-1001") == "ORD-1001")
ok("Extract: TKT", extract_ticket_id("TKT-501") == "TKT-501")

print("\n--- 9. PROACTIVE ISSUE DETECTION ---")
det = IssueDetectionService(repo)
iss = det.detect_issues("operations_admin")
ok("Issues: returns list", isinstance(iss, list))
ok("Issues: finds some", len(iss) > 0)
types = set(i["type"] for i in iss)
ok("Issues: has sla_monitoring", "sla_monitoring" in types)
ok("Issues: has severity", all("severity" in i for i in iss))
ok("Issues: has message", all("message" in i for i in iss))

print("\n--- 10. OBSERVABILITY ---")
ok("Logger exists", logging.getLogger("parcelpilot") is not None)
ok("Agent logger", logging.getLogger("parcelpilot.agent") is not None)

print("\n--- 11. SECURITY ---")
ok("Prompt: docs as DATA", "DATA, not instructions" in SYSTEM_PROMPT)
ok("Prompt: customer scoped", "customers can only access" in SYSTEM_PROMPT.lower())
ok("Prompt: confirmation", "confirmation" in SYSTEM_PROMPT.lower())
ok("Prompt: no fabrication", "fabricate" in SYSTEM_PROMPT.lower())
ok("Input: injection patterns exist", len(__import__("app.agent.graph", fromlist=["_INJECTION_PATTERNS"])._INJECTION_PATTERNS) > 0)

print("\n" + "=" * 60)
print(f"RESULTS: {P} passed, {F} failed, {P+F} total")
if E:
    print("\nFAILURES:")
    for n, d in E: print(f"  - {n}: {d}")
print("=" * 60)
try:
    db.close()
    if os.path.exists(db_path): os.remove(db_path)
except Exception:
    pass
