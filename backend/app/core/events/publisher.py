import uuid

from sqlalchemy.orm import Session

from app.core.events.models import DomainEvent


def emit(
    session: Session,
    *,
    type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    organization_id: uuid.UUID | None,
    actor_id: uuid.UUID | None = None,
    payload: dict | None = None,
    version: int = 1,
) -> DomainEvent:
    """Write a domain event to the outbox. Committed with the enclosing transaction."""
    event = DomainEvent(
        organization_id=organization_id,
        type=type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        actor_id=actor_id,
        payload=payload or {},
        version=version,
    )
    session.add(event)
    return event