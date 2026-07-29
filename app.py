from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel, Session, create_engine, select


class SupportLevel(str, Enum):
    level_1 = "level_1"
    level_2 = "level_2"


class IncidentStatus(str, Enum):
    open = "open"
    escalated = "escalated"
    closed = "closed"


class ShiftHandoverIncidentLink(SQLModel, table=True):
    shift_handover_id: Optional[int] = Field(
        default=None, foreign_key="shifthandover.id", primary_key=True
    )
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True
    )


class SupportAgent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    level: SupportLevel = Field(default=SupportLevel.level_1)

    owned_incidents: list["Incident"] = Relationship(back_populates="owner_agent")
    incoming_handovers: list["ShiftHandover"] = Relationship(back_populates="incoming_agent")


class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    status: IncidentStatus = Field(default=IncidentStatus.open)
    resolution_summary: Optional[str] = Field(default=None)
    escalation_reason: Optional[str] = Field(default=None)

    owner_agent_id: Optional[int] = Field(default=None, foreign_key="supportagent.id")
    owner_agent: Optional[SupportAgent] = Relationship(back_populates="owned_incidents")

    handovers: list["ShiftHandover"] = Relationship(
        back_populates="incidents", link_model=ShiftHandoverIncidentLink
    )

    @model_validator(mode="after")
    def validate_resolution_summary(self) -> "Incident":
        if self.status == IncidentStatus.closed and not (self.resolution_summary or "").strip():
            raise ValueError("Closed incidents require a resolution summary")
        return self


class ShiftHandover(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    incoming_agent_id: int = Field(foreign_key="supportagent.id")
    incoming_agent: SupportAgent = Relationship(back_populates="incoming_handovers")

    incidents: list[Incident] = Relationship(
        back_populates="handovers", link_model=ShiftHandoverIncidentLink
    )


class SupportAgentCreate(SQLModel):
    name: str
    level: SupportLevel = SupportLevel.level_1


class IncidentCreate(SQLModel):
    title: str
    description: str
    status: IncidentStatus = IncidentStatus.open
    resolution_summary: Optional[str] = None
    owner_agent_id: Optional[int] = None


class ShiftHandoverCreate(SQLModel):
    summary: str
    incoming_agent_id: int
    incident_ids: list[int] = Field(default_factory=list)


class EscalateIncidentRequest(SQLModel):
    escalation_reason: str = Field(min_length=1)


class CloseIncidentRequest(SQLModel):
    resolution_summary: str = Field(min_length=1)


sqlite_file_name = "incidents.db"
sqlite_url = f"sqlite:///./{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

app = FastAPI(title="IT Incident API")


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.post("/agents", response_model=SupportAgent)
def create_agent(agent: SupportAgentCreate, session: Session = Depends(get_session)) -> SupportAgent:
    db_agent = SupportAgent.model_validate(agent)
    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)
    return db_agent


@app.post("/incidents", response_model=Incident)
def create_incident(incident: IncidentCreate, session: Session = Depends(get_session)) -> Incident:
    db_incident = Incident.model_validate(incident)
    session.add(db_incident)
    session.commit()
    session.refresh(db_incident)
    return db_incident


@app.post("/shift-handovers", response_model=ShiftHandover)
def create_shift_handover(
    handover: ShiftHandoverCreate, session: Session = Depends(get_session)
) -> ShiftHandover:
    incidents = []
    if handover.incident_ids:
        incidents = session.exec(select(Incident).where(Incident.id.in_(handover.incident_ids))).all()

    db_handover = ShiftHandover(
        summary=handover.summary,
        incoming_agent_id=handover.incoming_agent_id,
        incidents=incidents,
    )
    session.add(db_handover)
    session.commit()
    session.refresh(db_handover)
    return db_handover


@app.get("/incidents/unresolved", response_model=list[Incident])
def get_unresolved_incidents(session: Session = Depends(get_session)) -> list[Incident]:
    return session.exec(select(Incident).where(Incident.status != IncidentStatus.closed)).all()


@app.post("/incidents/{incident_id}/escalate", response_model=Incident)
def escalate_incident(
    incident_id: int,
    payload: EscalateIncidentRequest,
    session: Session = Depends(get_session),
) -> Incident:
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status == IncidentStatus.closed:
        raise HTTPException(status_code=400, detail="Closed incidents cannot be escalated")

    level_2_agent = session.exec(
        select(SupportAgent)
        .where(SupportAgent.level == SupportLevel.level_2)
        .order_by(SupportAgent.id)
    ).first()
    if not level_2_agent:
        raise HTTPException(status_code=400, detail="No Level 2 agent available for escalation")

    incident.owner_agent_id = level_2_agent.id
    incident.status = IncidentStatus.escalated
    incident.escalation_reason = payload.escalation_reason

    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


@app.patch("/incidents/{incident_id}/close", response_model=Incident)
def close_incident(
    incident_id: int,
    payload: CloseIncidentRequest,
    session: Session = Depends(get_session),
) -> Incident:
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    validated = Incident.model_validate(
        {
            **incident.model_dump(),
            "status": IncidentStatus.closed,
            "resolution_summary": payload.resolution_summary,
        }
    )

    incident.status = validated.status
    incident.resolution_summary = validated.resolution_summary

    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident
