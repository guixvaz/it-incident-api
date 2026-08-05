import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import (
    Incident,
    IncidentStatus,
    SupportAgent,
    SupportLevel,
    app,
    get_session,
)


@pytest.fixture
def client_and_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        with Session(engine) as session:
            yield client, session

    app.dependency_overrides.clear()


def test_closed_incident_requires_resolution_summary():
    with pytest.raises(ValidationError):
        Incident.model_validate(
            {
                "title": "Server offline",
                "description": "Server 04 is offline",
                "status": IncidentStatus.closed,
                "resolution_summary": None,
            }
        )


def test_unresolved_incidents_endpoint_returns_only_non_closed(client_and_session):
    client, session = client_and_session

    open_incident = Incident(title="Open", description="Open incident")
    closed_incident = Incident(
        title="Closed",
        description="Closed incident",
        status=IncidentStatus.closed,
        resolution_summary="Restarted service",
    )

    session.add(open_incident)
    session.add(closed_incident)
    session.commit()

    response = client.get("/incidents/unresolved")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Open"


def test_escalation_requires_reason_and_reassigns_to_level_2(client_and_session):
    client, session = client_and_session

    l1_agent = SupportAgent(name="Alex", level=SupportLevel.level_1)
    l2_agent = SupportAgent(name="Sam", level=SupportLevel.level_2)
    session.add(l1_agent)
    session.add(l2_agent)
    session.commit()

    incident = Incident(
        title="Disk alert",
        description="Disk usage over threshold",
        owner_agent_id=l1_agent.id,
    )
    session.add(incident)
    session.commit()
    session.refresh(incident)

    missing_reason = client.post(f"/incidents/{incident.id}/escalate", json={})
    assert missing_reason.status_code == 422

    response = client.post(
        f"/incidents/{incident.id}/escalate",
        json={"escalation_reason": "Needs database specialist"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == IncidentStatus.escalated
    assert payload["owner_agent_id"] == l2_agent.id
    assert payload["escalation_reason"] == "Needs database specialist"


def test_close_incident_requires_resolution_summary(client_and_session):
    client, session = client_and_session
    incident = Incident(title="Web app down", description="502 from load balancer")
    session.add(incident)
    session.commit()
    session.refresh(incident)

    invalid = client.patch(f"/incidents/{incident.id}/close", json={})
    assert invalid.status_code == 422

    valid = client.patch(
        f"/incidents/{incident.id}/close",
        json={"resolution_summary": "Restarted failing instance"},
    )
    assert valid.status_code == 200
    assert valid.json()["status"] == IncidentStatus.closed
