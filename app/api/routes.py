from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import uuid
import time
import logging
from datetime import datetime

from app.security.auth import get_user, UserContext, is_internal, UserRole
from app.data.repository import Repository
from app.data.models import Action, AuditLog
from app.services.retrieval import RetrievalService
from app.services.issue_detection import IssueDetectionService
from app.agent.graph import run_agent, extract_ticket_id
from app.agent.state import AgentState
from app.tools.actions import confirm_action_tool

router = APIRouter()
logger = logging.getLogger("parcelpilot")

_retrieval_instance = None


def _get_retrieval() -> RetrievalService:
    global _retrieval_instance
    if _retrieval_instance is None:
        from app.main import vector_store_instance
        _retrieval_instance = RetrievalService(vector_store_instance)
    return _retrieval_instance


def _get_session():
    from app.main import SessionLocal
    return SessionLocal()


class ChatRequest(BaseModel):
    message: str
    user_id: str = "support_agent"
    request_id: Optional[str] = None


class ChatResponse(BaseModel):
    request_id: str
    response: str
    citations: list = []
    tool_calls: list = []
    pending_actions: list = []
    conflicts: list = []
    confidence: str = "medium"
    reasoning_steps: list = []


class ConfirmActionRequest(BaseModel):
    action_id: str


class ConfirmActionResponse(BaseModel):
    action_id: str
    status: str
    message: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    request_id = req.request_id or str(uuid.uuid4())
    start_time = time.time()

    user = get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=401, detail=f"Unknown user: {req.user_id}")

    db = _get_session()
    try:
        repo = Repository(db)
        retrieval = _get_retrieval()

        state = AgentState(
            user_query=req.message,
            user=user,
        )

        state = run_agent(state, repo, retrieval)

        try:
            audit = AuditLog(
                id=str(uuid.uuid4()),
                request_id=request_id,
                user_id=user.user_id,
                account_id=state.account_id,
                action="chat",
                details=f"Query: {req.message[:200]}",
                timestamp=datetime.utcnow().isoformat(),
            )
            repo.log_audit(audit)
        except Exception as e:
            logger.warning(f"Audit log failed for {request_id}: {e}")

        tool_calls_summary = []
        for tool_name, result in state.tool_calls:
            tool_calls_summary.append({
                "tool": tool_name,
                "result_summary": str(result)[:200],
            })

        latency = round(time.time() - start_time, 3)
        logger.info(
            f"chat request_id={request_id} user={user.user_id} "
            f"account={state.account_id} latency={latency}s "
            f"confidence={state.confidence} tools={len(tool_calls_summary)}"
        )

        return ChatResponse(
            request_id=request_id,
            response=state.response,
            citations=state.citations,
            tool_calls=tool_calls_summary,
            pending_actions=state.pending_actions,
            conflicts=state.conflicts,
            confidence=state.confidence,
            reasoning_steps=state.reasoning_steps,
        )
    except HTTPException:
        raise
    except Exception as e:
        latency = round(time.time() - start_time, 3)
        logger.error(f"chat error request_id={request_id} latency={latency}s error={e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        db.close()


@router.post("/actions/{action_id}/confirm", response_model=ConfirmActionResponse)
def confirm_action(action_id: str):
    db = _get_session()
    try:
        repo = Repository(db)
        result = confirm_action_tool(repo, action_id)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return ConfirmActionResponse(
            action_id=action_id,
            status=result["status"],
            message=result["message"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"confirm_action error action_id={action_id} error={e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        db.close()


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str, user_id: str = "support_agent"):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown user")

    db = _get_session()
    try:
        repo = Repository(db)
        ticket = repo.get_ticket(ticket_id, user.account_id if not is_internal(user) else None)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found or access denied")

        return {
            "ticket_id": ticket.ticket_id,
            "account_id": ticket.account_id,
            "status": ticket.status,
            "subject": ticket.subject,
            "description": ticket.description,
            "channel": ticket.channel,
            "assigned_to": ticket.assigned_to,
            "created_at": ticket.created_at,
            "historical_resolution": ticket.historical_resolution,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_ticket error ticket_id={ticket_id} error={e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        db.close()


@router.get("/orders/{order_id}")
def get_order(order_id: str, user_id: str = "support_agent"):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown user")

    db = _get_session()
    try:
        repo = Repository(db)
        order = repo.get_order(order_id, user.account_id if not is_internal(user) else None)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or access denied")

        return {
            "order_id": order.order_id,
            "account_id": order.account_id,
            "carrier": order.carrier,
            "status": order.status,
            "booked_at": order.booked_at,
            "pickup_window_start": order.pickup_window_start,
            "pickup_window_end": order.pickup_window_end,
            "pickup_actual_at": order.pickup_actual_at,
            "shipment_fee_inr": order.shipment_fee_inr,
            "carrier_fault": order.carrier_fault,
            "customer_fault": order.customer_fault,
            "cancellation_requested_at": order.cancellation_requested_at,
            "notes": order.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_order error order_id={order_id} error={e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        db.close()


@router.get("/ops/issues")
def get_issues(user_id: str = "operations_admin"):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown user")
    if not is_internal(user):
        raise HTTPException(status_code=403, detail="Internal access required")

    db = _get_session()
    try:
        repo = Repository(db)
        detection = IssueDetectionService(repo)
        issues = detection.detect_issues(user.user_id)
        return {"issues": issues, "count": len(issues)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_issues error error={e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        db.close()


@router.get("/health")
def health():
    return {"status": "ok", "service": "parcelpilot-ai-support"}


@router.get("/sources/{source_id}")
def get_source(source_id: str):
    from app.services.reliability import DOCUMENT_METADATA

    source = DOCUMENT_METADATA.get(source_id)
    if not source:
        matches = [
            {"id": k, "name": v.get("document_name", k)}
            for k, v in DOCUMENT_METADATA.items()
            if source_id.lower() in k.lower() or source_id.lower() in v.get("document_name", "").lower()
        ]
        if not matches:
            raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")
        return {"matches": matches}

    return {
        "source_id": source_id,
        "document_name": source.get("document_name"),
        "document_type": source.get("document_type"),
        "version": source.get("version"),
        "status": source.get("status"),
        "effective_date": source.get("effective_date"),
        "customer_account_id": source.get("customer_account_id"),
        "source_priority": source.get("source_priority"),
        "section": source.get("section"),
    }
