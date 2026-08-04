from typing import Optional
from sqlmodel import Session, select
from ..models import SupportAgent

def create_agent(session: Session, agent_data: AgentCreate) -> SupportAgent:
    """ Creates a new support agent in the database."""
    agent = SupportAgent(
        name=agent_data.name,
        support_level=agent_data.level
    )
    session.add(agent)
    session.commit()
    session.refresh(agent)

    return agent

def get_agent_by_id(session: Session, agent_id: int) -> Optional[SupportAgent]:
    """ Retrieves a support agent by their ID."""
    return session.get(SupportAgent, agent_id)

def get_agents_by_level(session: Session, level: int) -> list[SupportAgent]:
    """ Retrieves all support agents of a specific support level."""
    stmt = select(SupportAgent).where(SupportAgent.support_level == level)
    return session.exec(stmt).all()