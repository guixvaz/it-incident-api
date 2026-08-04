from pydantic import BaseModel

# ==========================================
# Agent Schemas
# ==========================================

class SupportAgentCreate(BaseModel):
    name: str
    tier: int = 1

# ==========================================
# Incident Schemas
# ==========================================

class IncidentCreate(BaseModel):
    title: str
    description: str
    status: str = "open"
    owner_agent_id: int

class IncidentRead(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str

class IncidentEscalate(BaseModel):
    changed_by_agent_id: int
    action_description: str

class IncidentResolve(BaseModel):
    changed_by_agent_id: int
    resolution_summary: str

# ==========================================
# Shift Handover Schemas
# ==========================================

class ShiftHandoverCreate(BaseModel):
    """ Payload for creating a new shift handover. """
    incoming_agent_id: int
    outgoing_agent_id: int
    critical_notes: str

class ShiftHandoverSummaryResponse(BaseModel):
    """ A comprehensive report for the incoming shift. """
    handover_id: int
    critical_notes: str
    incoming_agent_id: int
    active_incidents: list[IncidentRead]
    active_incident_count: int