from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

class SupportAgent(SQLModel):
    """ Represents a support agent who can own incidents and participate in shift handovers."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    support_tier: int = Field(default=1)

    incidents: List["Incident"] = Relationship(back_populates="owner_agent")
    audit_logs: List["IncidentAuditLog"] = Relationship(back_populates="changed_by_agent")
    
    outgoing_handovers: List["ShiftHandover"] = Relationship(back_populates="outgoing_agent",
                                                             sa_relationship_kwargs={"foreign_keys": "ShiftHandover.outgoing_agent_id"}
                                                             )
    
    incoming_handovers: List["ShiftHandover"] = Relationship(back_populates="incoming_agent",
                                                            sa_relationship_kwargs={"foreign_keys": "ShiftHandover.incoming_agent_id"}
                                                            )

class Incident(SQLModel, table=True):
    """ Represents an IT incident that needs to be tracked and resolved."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    status: str = Field(default="open")
    priority: str = Field(default="medium")
    resolution_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    escalation_reason: Optional[str] = None

    audit_logs: List["IncidentAuditLog"] = Relationship(back_populates="incident")
    owner_agent_id: Optional[int] = Field(default=None, foreign_key="supportagent.id")
    owner_agent: Optional[SupportAgent] = Relationship(back_populates="incidents")

class ShiftHandover(SQLModel, table=True):
    """ Represents a shift handover between support agents."""
    id: Optional[int] = Field(default=None, primary_key=True)
    handover_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    critical_notes: Optional[str] = None

    outgoing_agent_id: int = Field(foreign_key="supportagent.id")
    incoming_agent_id: int = Field(foreign_key="supportagent.id")

    outgoing_agent: Optional[SupportAgent] = Relationship(back_populates="outgoing_handovers",
                                               sa_relationship_kwargs={"foreign_keys": "ShiftHandover.outgoing_agent_id"}
                                               )
    
    incoming_agent: Optional[SupportAgent] = Relationship(back_populates="incoming_handovers",
                                              sa_relationship_kwargs={"foreign_keys": "ShiftHandover.incoming_agent_id"}
                                              )

class IncidentAuditLog(SQLModel, table=True):
    """Immutable record of every state change on an incident."""
    id: Optional[int] = Field(default=None, primary_key=True)
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Changes made to the incident
    old_status: str
    new_status: str
    action_description: str #e.g., "Incident escalated to level 2 support due to database issue"
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    #Links to the incident
    incident_id: int = Field(foreign_key="incident.id")
    incident: Optional["Incident"] = Relationship(back_populates="audit_logs")

    # Links to the agent who made the change
    changed_by_agent_id: Optional[int] = Field(default=None, foreign_key="supportagent.id")
    changed_by_agent: Optional[SupportAgent] = Relationship(back_populates="audit_logs")
    