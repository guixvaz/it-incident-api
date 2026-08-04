from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db import get_session
from ..models import SupportAgent
from ..schemas import SupportAgentCreate
from ..dao import agentDAO as agent_dao
from ..exceptions import EntityNotFoundError

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.post("/", response_model=SupportAgent)
def create_agent_endpoint(data: SupportAgentCreate, session: Session = Depends(get_session)) -> SupportAgent:
    """Endpoint to create a new support agent."""
    return agent_dao.create_agent(session=session, agent_data=data)

@router.get("/{agent_id}", response_model=SupportAgent)
def get_agent_endpoint(agent_id: int, session: Session = Depends(get_session)) -> SupportAgent:
    """Endpoint to retrieve a support agent by ID."""
    agent = agent_dao.get_agent_by_id(session=session, agent_id=agent_id)
    if not agent:
        raise EntityNotFoundError(f"Support agent with ID {agent_id} not found.")
    return agent