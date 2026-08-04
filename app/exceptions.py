
class IncidentDomainError(Exception):
    """Base exception for all IT Incident API business logic errors."""
    pass

class EntityNotFoundError(IncidentDomainError):
    """Raised when a requested database record (Agent, Incident) does not exist."""
    pass

class StateTransitionError(IncidentDomainError):
    """Raised when an incident attempts an invalid lifecycle status change."""
    pass