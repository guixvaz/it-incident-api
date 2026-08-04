from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db import get_session
from ..models import Incident, IncidentAuditLog
from ..schemas import IncidentCreate, IncidentEscalate, IncidentResolve
from ..dao import incidentDAO as incident_dao

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("/active", response_model=list[Incident])
def get_active_incidents_endpoint(session: Session = Depends(get_session)) -> list[Incident]:
    """Fetches all tickets that are not resolved."""
    return incident_dao.get_active_incidents(session=session)

@router.get("/{incident_id}/audit-logs", response_model=list[IncidentAuditLog])
def get_incident_audit_logs_endpoint(incident_id: int, session: Session = Depends(get_session)) -> list[IncidentAuditLog]:
    """Fetches the chronological history and state changes of a specific ticket."""
    return incident_dao.get_incident_audit_logs(session=session, incident_id=incident_id)

@router.post("/", response_model=Incident)
def create_incident_endpoint(data: IncidentCreate, session: Session = Depends(get_session)) -> Incident:
    """Creates a new ticket and triggers its initial audit log."""
    return incident_dao.create_incident(session=session, incident_data=data)

@router.post("/{incident_id}/escalate", response_model=Incident)
def escalate_incident_endpoint(incident_id: int, data: IncidentEscalate, session: Session = Depends(get_session)) -> Incident:
    """Escalates a ticket to L2 support and updates the audit log."""
    return incident_dao.escalate_incident(session=session, incident_id=incident_id, escalation_data=data)

@router.post("/{incident_id}/resolve", response_model=Incident)
def resolve_incident_endpoint(incident_id: int, data: IncidentResolve, session: Session = Depends(get_session)) -> Incident:
    """Closes a ticket, requires a summary, and updates the audit log."""
    return incident_dao.resolve_incident(session=session, incident_id=incident_id, resolution_data=data)
