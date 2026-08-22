import json
import re
import time
import logging
from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT
from app.tools.documents import search_documents_tool
from app.tools.operations import (
    get_account_tool,
    get_order_tool,
    get_ticket_tool,
    get_sla_status_tool,
    get_orders_by_account_tool,
    get_tickets_by_account_tool,
)
from app.tools.actions import (
    create_escalation_tool,
    update_ticket_tool,
    create_followup_task_tool,
)
from app.services.retrieval import RetrievalService
from app.data.repository import Repository
from app.security.auth import UserContext, is_internal, can_access_account
from typing import Optional
import httpx
from app.config import get_settings

logger = logging.getLogger("parcelpilot.agent")

_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)",
    r"you\s+are\s+now\s+",
    r"system\s*:\s*",
    r"act\s+as\s+",
    r"pretend\s+you\s+are\s+",
    r"disregard\s+(previous|all|above)",
    r"override\s+(previous|all|above)",
    r"new\s+instructions?\s*:",
    r"forget\s+(everything|all|previous)",
]


def sanitize_query(query: str) -> str:
    sanitized = query.strip()
    if len(sanitized) > 2000:
        sanitized = sanitized[:2000]
    for pattern in _INJECTION_PATTERNS:
        import re as _re
        if _re.search(pattern, sanitized, _re.IGNORECASE):
            logger.warning(f"Potential injection attempt detected: {sanitized[:100]}")
            break
    return sanitized


def extract_account_id(query: str) -> Optional[str]:
    patterns = [
        (r"northstar", "ACCT-001"),
        (r"lumenworks", "ACCT-002"),
        (r"beacon", "ACCT-003"),
        (r"axis\s*labs", "ACCT-004"),
        (r"ACCT-\d+", None),
    ]
    for pattern, override in patterns:
        if re.search(pattern, query, re.IGNORECASE):
            if override:
                return override
            match = re.search(r"ACCT-\d+", query)
            if match:
                return match.group()
    return None


def extract_order_id(query: str) -> Optional[str]:
    match = re.search(r"ORD-\d+", query)
    return match.group() if match else None


def extract_ticket_id(query: str) -> Optional[str]:
    match = re.search(r"TKT-\d+", query)
    return match.group() if match else None


def call_llm(messages: list[dict]) -> str:
    settings = get_settings()
    start = time.time()
    try:
        response = httpx.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.1,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        logger.info(f"LLM call ok latency={round(time.time()-start, 2)}s model={settings.llm_model}")
        return content
    except Exception as e:
        logger.error(f"LLM call failed latency={round(time.time()-start, 2)}s error={e}")
        return f"Error calling LLM: {str(e)}"


def run_agent(
    state: AgentState,
    repo: Repository,
    retrieval: RetrievalService,
) -> AgentState:
    query = sanitize_query(state.user_query)
    state.user_query = query
    user = state.user

    account_id = extract_account_id(query)
    order_id = extract_order_id(query)
    ticket_id = extract_ticket_id(query)

    logger.info(f"agent query user={user.user_id} account={account_id} order={order_id} ticket={ticket_id}")

    if account_id and not can_access_account(user, account_id):
        state.response = "Access denied: you do not have permission to access this account's data."
        state.confidence = "high"
        return state

    if account_id:
        state.account_id = account_id
        state.reasoning_steps.append(f"Identified account: {account_id}")

    tool_calls = []

    if account_id:
        result = get_account_tool(repo, user, account_id)
        state.structured_data["account"] = result
        tool_calls.append(("get_account", result))
        state.reasoning_steps.append(f"Retrieved account details for {account_id}")

    if order_id:
        result = get_order_tool(repo, user, order_id)
        state.structured_data["order"] = result
        tool_calls.append(("get_order", result))
        state.reasoning_steps.append(f"Retrieved order {order_id}")

    if ticket_id:
        result = get_ticket_tool(repo, user, ticket_id)
        state.structured_data["ticket"] = result
        tool_calls.append(("get_ticket", result))
        state.reasoning_steps.append(f"Retrieved ticket {ticket_id}")

    if account_id and not order_id and not ticket_id:
        orders_result = get_orders_by_account_tool(repo, user, account_id)
        state.structured_data["orders"] = orders_result
        tool_calls.append(("get_orders_by_account", orders_result))

        tickets_result = get_tickets_by_account_tool(repo, user, account_id)
        state.structured_data["tickets"] = tickets_result
        tool_calls.append(("get_tickets_by_account", tickets_result))

    doc_result = search_documents_tool(retrieval, user, query, account_id)
    state.retrieved_docs = doc_result.get("citations", [])
    state.citations = doc_result.get("citations", [])
    state.conflicts = doc_result.get("conflicts", [])
    tool_calls.append(("search_documents", doc_result))
    state.reasoning_steps.append(f"Searched documents: {doc_result.get('result_count', 0)} results")

    if not account_id and not order_id and not ticket_id:
        doc_result_no_account = search_documents_tool(retrieval, user, query)
        if doc_result_no_account.get("result_count", 0) > len(state.citations):
            state.citations = doc_result_no_account.get("citations", [])

    state.tool_calls = tool_calls
    logger.info(f"agent tools_called={[t[0] for t in tool_calls]}")

    doc_context = ""
    for c in state.citations[:5]:
        doc_context += f"\n- {c['document']} (Page {c['page']}, Authority: {c['authority']}): {c['excerpt']}"

    data_context = ""
    if state.structured_data.get("account"):
        acc = state.structured_data["account"].get("account", {})
        if acc:
            data_context += f"\nAccount: {acc.get('account_name')} ({acc.get('account_id')}) - Plan: {acc.get('plan')}"
    if state.structured_data.get("order"):
        ord_data = state.structured_data["order"].get("order", {})
        if ord_data:
            data_context += f"\nOrder: {ord_data.get('order_id')} - Status: {ord_data.get('status')} - Carrier: {ord_data.get('carrier')}"
            if ord_data.get("cancellation_requested_at"):
                data_context += f" - Cancellation requested: {ord_data.get('cancellation_requested_at')}"
            if ord_data.get("carrier_fault"):
                data_context += " - CARRIER AT FAULT"
            data_context += f" - Fee: INR {ord_data.get('shipment_fee_inr', 0)}"
            data_context += f" - Notes: {ord_data.get('notes', 'N/A')}"
    if state.structured_data.get("orders"):
        orders_list = state.structured_data["orders"].get("orders", [])
        if orders_list:
            data_context += f"\nOrders for account ({len(orders_list)} total):"
            for o in orders_list[:10]:
                data_context += f"\n  - {o.get('order_id')}: {o.get('status')}, Carrier: {o.get('carrier')}, Fee: INR {o.get('shipment_fee_inr', 0)}"
                if o.get("carrier_fault"):
                    data_context += " [CARRIER FAULT]"
    if state.structured_data.get("ticket"):
        tkt = state.structured_data["ticket"].get("ticket", {})
        if tkt:
            data_context += f"\nTicket: {tkt.get('ticket_id')} - Status: {tkt.get('status')} - Subject: {tkt.get('subject')}"
            if tkt.get("historical_resolution"):
                data_context += f" - Historical resolution: {tkt.get('historical_resolution')}"
    if state.structured_data.get("tickets"):
        tickets_list = state.structured_data["tickets"].get("tickets", [])
        if tickets_list:
            data_context += f"\nTickets for account ({len(tickets_list)} total):"
            for t in tickets_list[:10]:
                data_context += f"\n  - {t.get('ticket_id')}: {t.get('status')}, Subject: {t.get('subject')}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""User query: {query}

Data retrieved:
{data_context if data_context else "No structured data retrieved."}

Documents retrieved:
{doc_context if doc_context else "No documents retrieved."}

Conflicts: {json.dumps(state.conflicts) if state.conflicts else "None"}

Answer the user directly and briefly using the data above."""},
    ]

    llm_response = call_llm(messages)

    if any(keyword in query.lower() for keyword in ["escalat", "update ticket", "follow-up", "follow up"]):
        if "escalat" in query.lower():
            if ticket_id:
                action_result = create_escalation_tool(repo, user, ticket_id, reason="Customer-requested escalation", priority="high", team="Support")
                state.pending_actions.append(action_result)
            elif state.structured_data.get("ticket"):
                tkt = state.structured_data["ticket"].get("ticket", {})
                if tkt:
                    action_result = create_escalation_tool(repo, user, tkt["ticket_id"], reason="Customer-requested escalation", priority="high", team="Support")
                    state.pending_actions.append(action_result)

    state.response = llm_response
    state.confidence = "high" if state.citations and state.structured_data else "medium"
    if state.conflicts:
        state.confidence = "medium"
    if not state.citations and not state.structured_data:
        state.confidence = "low"

    return state
