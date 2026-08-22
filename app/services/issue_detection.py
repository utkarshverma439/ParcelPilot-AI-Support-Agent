from app.data.repository import Repository
from app.data.models import Ticket, Order
from typing import Optional


class IssueDetectionService:
    def __init__(self, repo: Repository):
        self.repo = repo

    def detect_issues(self, user_id: Optional[str] = None) -> list[dict]:
        issues = []
        issues.extend(self._detect_sla_breaches())
        issues.extend(self._detect_repeated_complaints())
        issues.extend(self._detect_carrier_issues())
        issues.extend(self._detect_high_severity_unresolved())
        issues.extend(self._detect_unusual_patterns())
        return issues

    def _detect_sla_breaches(self) -> list[dict]:
        issues = []
        tickets = self.repo.get_open_tickets()

        sla_thresholds = {
            "Enterprise": {"P1": 0.25, "P2": 2, "P3": 8},
            "Growth": {"P1": 2, "P2": 4, "P3": 16},
            "Standard": {"P1": 4, "P2": 8, "P3": 16},
        }

        for ticket in tickets:
            account = self.repo.get_account(ticket.account_id)
            if not account:
                continue

            thresholds = sla_thresholds.get(account.plan, sla_thresholds["Standard"])

            if "security" in (ticket.subject or "").lower() or "api key" in (ticket.subject or "").lower():
                severity = "P1"
            elif "failing" in (ticket.subject or "").lower() or "outage" in (ticket.subject or "").lower():
                severity = "P1"
            elif "how do" in (ticket.subject or "").lower():
                severity = "P3"
            else:
                severity = "P2"

            threshold_hours = thresholds.get(severity, 8)

            issues.append({
                "type": "sla_monitoring",
                "severity": "high" if severity == "P1" else "medium",
                "ticket_id": ticket.ticket_id,
                "account_id": ticket.account_id,
                "account_name": account.account_name if account else "Unknown",
                "subject": ticket.subject,
                "severity_level": severity,
                "sla_threshold_hours": threshold_hours,
                "created_at": ticket.created_at,
                "message": f"{ticket.ticket_id} ({account.account_name if account else 'Unknown'}) - {severity} ticket open: {ticket.subject}",
            })

        return issues

    def _detect_repeated_complaints(self) -> list[dict]:
        issues = []
        tickets = self.repo.get_all_tickets()
        subject_groups = {}

        for ticket in tickets:
            if not ticket.subject:
                continue
            key = ticket.subject.lower().strip()
            subject_groups.setdefault(key, []).append(ticket)

        for subject, group in subject_groups.items():
            if len(group) >= 2:
                accounts = set(t.account_id for t in group)
                if len(accounts) >= 2:
                    issues.append({
                        "type": "repeated_complaint",
                        "severity": "high",
                        "subject": subject,
                        "count": len(group),
                        "accounts": list(accounts),
                        "ticket_ids": [t.ticket_id for t in group],
                        "message": f"Repeated complaint '{subject}' reported by {len(accounts)} customers across {len(group)} tickets",
                    })
                else:
                    issues.append({
                        "type": "repeated_complaint",
                        "severity": "medium",
                        "subject": subject,
                        "count": len(group),
                        "accounts": list(accounts),
                        "ticket_ids": [t.ticket_id for t in group],
                        "message": f"Repeated complaint '{subject}' from {accounts.pop()} across {len(group)} tickets",
                    })

        return issues

    def _detect_carrier_issues(self) -> list[dict]:
        issues = []
        orders = self.repo.get_all_orders()
        carrier_faults = {}

        for order in orders:
            if order.carrier_fault:
                carrier_faults.setdefault(order.carrier, []).append(order)

        for carrier, fault_orders in carrier_faults.items():
            affected_accounts = set(o.account_id for o in fault_orders)
            issues.append({
                "type": "carrier_issue",
                "severity": "high",
                "carrier": carrier,
                "fault_count": len(fault_orders),
                "affected_accounts": list(affected_accounts),
                "order_ids": [o.order_id for o in fault_orders],
                "message": f"Carrier {carrier} has {len(fault_orders)} orders with reported faults affecting {len(affected_accounts)} accounts",
            })

        return issues

    def _detect_high_severity_unresolved(self) -> list[dict]:
        issues = []
        tickets = self.repo.get_open_tickets()

        for ticket in tickets:
            if not ticket.subject:
                continue
            subject_lower = ticket.subject.lower()
            if any(kw in subject_lower for kw in ["failing", "outage", "security", "api key", "exposure"]):
                issues.append({
                    "type": "high_severity_unresolved",
                    "severity": "urgent",
                    "ticket_id": ticket.ticket_id,
                    "account_id": ticket.account_id,
                    "subject": ticket.subject,
                    "assigned_to": ticket.assigned_to,
                    "created_at": ticket.created_at,
                    "message": f"URGENT: High-severity ticket {ticket.ticket_id} remains open: {ticket.subject}",
                })

        return issues

    def _detect_unusual_patterns(self) -> list[dict]:
        issues = []
        orders = self.repo.get_all_orders()

        cancellations = [o for o in orders if o.cancellation_requested_at]
        if len(cancellations) >= 3:
            issues.append({
                "type": "unusual_pattern",
                "severity": "medium",
                "pattern": "high_cancellation_rate",
                "count": len(cancellations),
                "order_ids": [o.order_id for o in cancellations],
                "message": f"High cancellation activity: {len(cancellations)} orders have cancellation requests",
            })

        return issues
