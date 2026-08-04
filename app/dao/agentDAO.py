from typing import Optional
from sqlmodel import Session, select

from ..schemas import SupportAgentCreate
from ..models import SupportAgent


def create_agent(session: Session, agent_data: SupportAgentCreate) -> SupportAgent:
    """ Creates a new support agent in the database."""
    agent = SupportAgent(
        name=agent_data.name,
        support_tier=agent_data.tier
    )
    session.add(agent)
    session.commit()
    session.refresh(agent)

    return agent

def get_agent_by_id(session: Session, agent_id: int) -> Optional[SupportAgent]:
    """ Retrieves a support agent by their ID."""
    return session.get(SupportAgent, agent_id)

def get_agents_by_tier(session: Session, tier: int) -> list[SupportAgent]:
    """ Retrieves all support agents of a specific support tier."""
    stmt = select(SupportAgent).where(SupportAgent.support_tier == tier)
    return session.exec(stmt).all()