from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db import get_session
from ..schemas import ShiftHandoverCreate, ShiftHandoverSummaryResponse

from ..dao import handoverDAO as handover_dao
from ..dao import incidentDAO as incident_dao
from ..dao import agentDAO as agent_dao

router = APIRouter(prefix="/shift-handovers", tags=["Shift Handovers"])

@router.post("/", response_model=ShiftHandoverSummaryResponse)
def submit_shift_handover(handover_data: ShiftHandoverCreate, session: Session = Depends(get_session)) -> ShiftHandoverSummaryResponse:
    """Submits shift notes and returns a complete operational summary
       of all active incidents for the incoming team."""

    handover = handover_dao.create_shift_handover(session=session, handover_data=handover_data)

    # Fetch all active incidents
    active_incidents = incident_dao.get_active_incidents(session=session)
    
    return ShiftHandoverSummaryResponse(
        handover_id=handover.id,
        critical_notes=handover.critical_notes,
        incoming_agent_id=handover_data.incoming_agent_id,
        active_incidents=active_incidents,
        active_incident_count=len(active_incidents)
    )