"""DNS change request web routes — new form, list, detail."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.exceptions import AppError, ForbiddenError
from app.micetro.dns_service import dns_service
from app.models.enums import DNSRecordType, RequestAction
from app.security.dependencies import (
    require_approver,
    require_authenticated_user,
    require_whitelisted_user,
)
from app.services.dns_request_service import DNSRequestService, RecordInput

router = APIRouter(prefix="/dns-requests", tags=["dns_requests"])
templates = Jinja2Templates(directory="app/templates")

RECORD_TYPES = [e.value for e in DNSRecordType if e != DNSRecordType.OTHER]
ACTIONS = [e.value for e in RequestAction]


def _flash(request: Request, message: str, category: str = "info") -> None:
    request.session.setdefault("flash", []).append(
        {"message": message, "category": category}
    )


# ── Zone search (HTMX) ───────────────────────────────────────────────────────

@router.get("/zones/search", response_class=HTMLResponse)
async def zone_search(
    request: Request,
    q: str = "",
    current_user=Depends(require_whitelisted_user),
):
    """HTMX endpoint: returns an HTML fragment of matching DNS zones."""
    if len(q.strip()) < 2:
        return HTMLResponse("")
    micetro_error = False
    try:
        zones = await dns_service.search_zones(q.strip(), limit=25)
    except Exception:
        zones = []
        micetro_error = True
    return templates.TemplateResponse(
        "partials/zone_suggestions.html",
        {"request": request, "zones": zones, "micetro_error": micetro_error},
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def list_requests(
    request: Request,
    current_user=Depends(require_whitelisted_user),
    db: AsyncSession = Depends(get_db),
):
    svc = DNSRequestService(db)
    if current_user.is_admin or current_user.is_approver:
        dns_requests = await svc.list_all()
    else:
        dns_requests = await svc.list_for_user(current_user.id)
    return templates.TemplateResponse(
        "dns_requests/list.html",
        {"request": request, "current_user": current_user, "dns_requests": dns_requests},
    )


# ── New form ──────────────────────────────────────────────────────────────────

@router.get("/new", response_class=HTMLResponse)
async def new_request_form(
    request: Request,
    current_user=Depends(require_whitelisted_user),
):
    return templates.TemplateResponse(
        "dns_requests/new.html",
        {
            "request": request,
            "current_user": current_user,
            "record_types": RECORD_TYPES,
            "actions": ACTIONS,
            "form": {},
        },
    )


# ── Create (POST) ─────────────────────────────────────────────────────────────

@router.post("/", response_class=HTMLResponse)
async def create_request(
    request: Request,
    action: str = Form(...),
    zone_name: str = Form(...),
    business_justification: str = Form(...),
    change_ticket: str = Form(default=""),
    notes: str = Form(default=""),
    submit_for_approval: str = Form(default=""),
    record_label: list[str] = Form(default=[]),
    record_type: list[str] = Form(default=[]),
    record_ttl: list[str] = Form(default=[]),
    record_value: list[str] = Form(default=[]),
    current_user=Depends(require_whitelisted_user),
    db: AsyncSession = Depends(get_db),
):
    # Build RecordInput list, skipping entirely-blank rows
    records: list[RecordInput] = []
    for label, rtype, ttl_raw, value in zip(
        record_label, record_type, record_ttl, record_value
    ):
        if not label.strip() and not value.strip():
            continue
        try:
            ttl = max(60, min(int(ttl_raw or "300"), 86400))
        except ValueError:
            ttl = 300
        records.append(RecordInput(
            label=label,
            record_type=rtype or "A",
            ttl=ttl,
            value=value,
        ))

    should_submit = submit_for_approval == "1"
    svc = DNSRequestService(db)

    try:
        dns_req = await svc.create(
            user=current_user,
            action=action,
            zone_name=zone_name,
            business_justification=business_justification,
            change_ticket=change_ticket or None,
            notes=notes or None,
            records=records,
            submit=should_submit,
        )
    except AppError as exc:
        return templates.TemplateResponse(
            "dns_requests/new.html",
            {
                "request": request,
                "current_user": current_user,
                "record_types": RECORD_TYPES,
                "actions": ACTIONS,
                "error": exc.detail,
                "form": {
                    "action": action,
                    "zone_name": zone_name,
                    "business_justification": business_justification,
                    "change_ticket": change_ticket,
                    "notes": notes,
                },
            },
            status_code=400,
        )

    if should_submit:
        _flash(request, f"Request {dns_req.request_number} submitted for approval.", "success")
    else:
        _flash(request, f"Draft {dns_req.request_number} saved.", "info")
    return RedirectResponse(f"/dns-requests/{dns_req.id}", status_code=303)


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get("/{request_id}", response_class=HTMLResponse)
async def request_detail(
    request_id: str,
    request: Request,
    current_user=Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    svc = DNSRequestService(db)
    dns_req = await svc.get_by_id(request_id)
    if dns_req is None:
        raise HTTPException(status_code=404)
    if not current_user.is_admin and not current_user.is_approver and str(dns_req.requester_id) != str(current_user.id):
        raise ForbiddenError()
    return templates.TemplateResponse(
        "dns_requests/detail.html",
        {"request": request, "current_user": current_user, "dns_request": dns_req},
    )


# ── Approve / Reject ───────────────────────────────────────────────────────

@router.post("/{request_id}/action", response_class=HTMLResponse)
async def approval_action(
    request_id: str,
    request: Request,
    decision: str = Form(...),
    comments: str = Form(default=""),
    current_user=Depends(require_approver),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a pending DNS request."""
    svc = DNSRequestService(db)
    try:
        dns_req = await svc.approve_or_reject(
            request_id=request_id,
            approver=current_user,
            decision=decision,
            comments=comments,
        )
    except AppError as exc:
        _flash(request, exc.detail, "danger")
        return RedirectResponse(f"/dns-requests/{request_id}", status_code=303)

    if decision == "approve":
        # Immediately execute the DNS changes in Micetro
        try:
            await svc.execute_in_micetro(dns_req.id)
            _flash(request, f"{dns_req.request_number} approved and executed in Micetro.", "success")
        except AppError as exec_exc:
            _flash(
                request,
                f"{dns_req.request_number} approved but Micetro execution failed: {exec_exc.detail}",
                "danger",
            )
    else:
        _flash(request, f"{dns_req.request_number} rejected.", "warning")
    return RedirectResponse(f"/dns-requests/{dns_req.id}", status_code=303)


# ── Manual execute / retry ─────────────────────────────────────────────────

@router.post("/{request_id}/execute", response_class=HTMLResponse)
async def execute_request(
    request_id: str,
    request: Request,
    current_user=Depends(require_approver),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger Micetro execution for an approved or failed request."""
    svc = DNSRequestService(db)
    try:
        dns_req = await svc.execute_in_micetro(request_id)
        _flash(request, f"{dns_req.request_number} executed in Micetro successfully.", "success")
    except AppError as exc:
        _flash(request, exc.detail, "danger")
    return RedirectResponse(f"/dns-requests/{request_id}", status_code=303)
