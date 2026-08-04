from sqlmodel import Session
from ..models import ShiftHandover, SupportAgent
from ..schemas import ShiftHandoverCreate
from ..exceptions import EntityNotFoundError

def create_shift_handover(session: Session, handover_data: ShiftHandoverCreate) -> ShiftHandover:
    """Creates a new shift handover in the database."""

    #Verify outgoing agent
    outgoing = session.get(SupportAgent, handover_data.outgoing_agent_id)
    if not outgoing:
        raise EntityNotFoundError(f"Outgoing agent with ID {handover_data.outgoing_agent_id} not found.")

    #Verify incoming agent
    incoming = session.get(SupportAgent, handover_data.incoming_agent_id)
    if not incoming:
        raise EntityNotFoundError(f"Incoming agent with ID {handover_data.incoming_agent_id} not found.")

    handover = ShiftHandover(
        incoming_agent_id=handover_data.incoming_agent_id,
        outgoing_agent_id=handover_data.outgoing_agent_id,
        critical_notes=handover_data.critical_notes
    )

    session.add(handover)
    session.commit()
    session.refresh(handover)
    
    return handover