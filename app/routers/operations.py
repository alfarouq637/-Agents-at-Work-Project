"""Internal operations routes.

This router is the first extraction from the legacy application module. It
keeps the existing public paths while isolating operational data and decisions
from customer-facing site routes.
"""
from fastapi import APIRouter, Cookie, Header, HTTPException

from .. import audit, auth, corp, db, llm, roles
from ..schemas import PostDecisionRequest, ProposalDecisionRequest


router = APIRouter(tags=["internal-operations"])


def require_operations_admin(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
) -> None:
    """Require the signed administrator session injected by the HTTP middleware or cookie."""
    token = x_admin_key or autocorp_session
    user = auth.get_active_user(token)
    if not user or not user.get("is_admin"):
        raise HTTPException(401, "Administrator session required")


@router.get("/api/posts")
def get_posts(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    return db.q("select * from posts order by id desc limit 15")


@router.post("/api/posts/{pid}/decision")
async def post_decision(
    pid: int,
    body: PostDecisionRequest,
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    decision = body.decision
    result = await corp.decide_post(pid, decision)
    if result.get("error"):
        raise HTTPException(409, "This post is not awaiting a decision")
    audit.record("operations.post_decision", actor_id=0, actor_type="administrator", target_type="post", target_id=str(pid), metadata={"decision": decision})
    return result


@router.get("/api/proposals")
def get_proposals(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    return db.q(
        "select id,kind,target,reason,status,substr(content,1,600) content "
        "from proposals order by id desc limit 15"
    )


@router.post("/api/proposals/{pid}/decision")
async def proposal_decision(
    pid: int,
    body: ProposalDecisionRequest,
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    decision = body.decision
    proposal = db.one("SELECT id, kind, status FROM proposals WHERE id=?", (pid,))
    if decision == "rollback":
        if not proposal or proposal.get("kind") != "prompt" or proposal.get("status") != "applied":
            raise HTTPException(409, "Only an applied prompt proposal can be rolled back")
    elif not proposal or proposal.get("status") != "pending":
        raise HTTPException(409, "This proposal is not awaiting a decision")
    result = await (corp.rollback_proposal(pid) if decision == "rollback" else corp.decide_proposal(pid, decision))
    if result.get("error"):
        raise HTTPException(409, "The proposal decision could not be applied")
    audit.record("operations.proposal_decision", actor_id=0, actor_type="administrator", target_type="proposal", target_id=str(pid), metadata={"decision": decision})
    return result


@router.get("/api/summary")
def get_summary(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    row = db.one("""
        select
            coalesce((select sum(delta) from ledger where account='client_payment'), 0) as rev,
            coalesce((select sum(delta) from ledger where account like 'payroll:%'), 0) as pay,
            (select count(*) from site_orders) as total_orders,
            (select count(*) from site_pages) as total_sites,
            (select count(*) from agents) as hired_agents,
            (select count(*) from jobs) as total_jobs
    """) or {}
    revenue = float(row.get("rev", 0) or 0)
    payroll = -float(row.get("pay", 0) or 0)
    return {
        "revenue_egp": round(revenue, 2),
        "payroll_egp": round(payroll, 3),
        "profit_egp": round(revenue - payroll, 2),
        "margin_percent": round(((revenue - payroll) / revenue * 100), 1) if revenue > 0 else 0,
        "hired_agents": int(row.get("hired_agents", 0) or 0),
        "roster_roles": len(roles.all_names()),
        "jobs": int(row.get("total_jobs", 0) or 0),
        "generated_sites": int(row.get("total_sites", 0) or 0),
        "total_store_orders": int(row.get("total_orders", 0) or 0),
    }


@router.get("/api/ledger")
def get_ledger(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    return db.q("select id, ts, account, delta, memo, job_id from ledger order by id desc limit 40")


@router.get("/api/audit-events")
def get_audit_events(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    """Return recent security-relevant actions to the administrator only."""
    require_operations_admin(x_admin_key, autocorp_session)
    return db.q(
        """select id, occurred_at, actor_type, actor_id, action, target_type,
        target_id, outcome, request_id, metadata_json from audit_events order by id desc limit 100"""
    )


@router.get("/api/agents")
def get_agents(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    return db.q("select name,department,origin,uses,round(balance,3) balance from agents order by uses desc, name")


@router.get("/api/roster")
def get_roster(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    return {"total": len(roles.all_names()), "departments": {name: list(members) for name, members in roles.DEPARTMENTS.items()}}


@router.get("/api/providers")
def get_providers(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    return llm.status()


@router.post("/api/providers/test")
async def test_providers(
    x_admin_key: str = Header(default=""),
    autocorp_session: str = Cookie(default=""),
):
    require_operations_admin(x_admin_key, autocorp_session)
    return await llm.test_all()
