from __future__ import annotations

from app.orm.incident import Incident, can_transition_incident


def apply_incident_vote(
    incident: Incident,
    vote_value: str,
) -> None:
    if vote_value == "true":
        incident.true_vote_count += 1
    elif vote_value == "false":
        incident.false_vote_count += 1
    else:
        raise ValueError("Unsupported vote value.")

    total_votes = incident.true_vote_count + incident.false_vote_count
    incident.confidence_score = incident.true_vote_count / total_votes if total_votes else 0


def transition_incident(
    incident: Incident,
    next_status: str,
    *,
    admin_override: bool = False,
    resolution_notes: str | None = None,
) -> None:
    if not admin_override and not can_transition_incident(incident.status, next_status):
        raise ValueError("Requested incident transition is not allowed.")
    incident.status = next_status
    if resolution_notes:
        incident.resolution_notes = resolution_notes
