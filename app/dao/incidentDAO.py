from typing import Optional
from sqlmodel import Session, select
from ..models import Incident, SupportAgent, IncidentAuditLog
from ..schemas import IncidentCreate, IncidentEscalate

def create_incident(session: Session, incident_data: IncidentCreate, owner_agent_id: Optional[int] = None) -> Optional[Incident]:
    # 1. Validate agent existence
    agent = session.get(SupportAgent, incident_data.owner_agent_id)
    if not agent:
        raise ValueError(f"SupportAgent with id {incident_data.owner_agent_id} does not exist.")

    # 2. Create the incident
    new_incident = Incident(
        title=incident_data.title,
        description=incident_data.description,
        status=incident_data.status,
        owner_agent_id=incident_data.owner_agent_id
    )
    session.add(new_incident)
    session.flush()  # Flush to get the new incident ID

    # 3. Create an audit log entry
    audit_log = IncidentAuditLog(
        old_status="none",  # No previous status since it's a new incident
        new_status="open",
        action_description="Ticket created",
        incident_id=new_incident.id,
        changed_by_agent_id=incident_data.owner_agent_id
    )
    session.add(audit_log)

    # 4. Commit the transaction
    session.commit()
    session.refresh(new_incident)  # Refresh to get the latest state from the DB
    return new_incident

def escalate_incident(session: Session, incident_id: int, escalation_data: IncidentEscalate) -> Optional[Incident]:
    # 1. Retrieve the incident
    incident = session.get(Incident, incident_id)
    if not incident:
        raise ValueError(f"Incident with id {incident_id} does not exist.")

    # 2. Update the incident status and escalation reason
    if incident.status in [IncidentStatus.escalated, IncidentStatus.resolved]:
        raise ValueError(f"Incident with id {incident_id} is already {incident.status}.")
    old_status = incident.status

    # 3. Apply the escalation logic (e.g., change status, assign to a higher-level agent)
    incident.escalate()

    # 4. Create an audit log entry
    audit_log = IncidentAuditLog(
        old_status=incident.status,
        new_status="escalated",
        action_description="Ticket escalated",
        incident_id=incident.id,
        changed_by_agent_id=escalation_data.changed_by_agent_id
    )
    session.add(audit_log)

    # 5. Commit the transaction
    session.add(incident)
    session.add(audit_log)
    session.commit()
    session.refresh(incident)  # Refresh to get the latest state from the DB
    return incident

def get_incident_by_id(session: Session, incident_id: int) -> Optional[Incident]:
    return session.get(Incident, incident_id)

def get_active_incidents(session: Session) -> list[Incident]:
    stmt = select(Incident).where(Incident.status != IncidentStatus.closed)
    result = session.exec(stmt)
    return result.all()

def get_incident_audit_logs(session: Session, incident_id: int) -> list[IncidentAuditLog]:
    stmt = select(IncidentAuditLog).where(IncidentAuditLog.incident_id == incident_id)
    result = session.exec(stmt)
    return result.all()