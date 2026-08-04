from pydantic import BaseModel

# ==========================================
# Agent Schemas
# ==========================================

class AgentCreate(BaseModel):
    name: str
    level: int = 1

# ==========================================
# Incident Schemas
# ==========================================

class IncidentCreate(BaseModel):
    title: str
    description: str
    status: str = "open"
    owner_agent_id: int

class IncidentEscalate(BaseModel):
    agent_id: int
    action_description: str

class IncidentResolve(BaseModel):
    agent_id: int
    resolution_summary: str
