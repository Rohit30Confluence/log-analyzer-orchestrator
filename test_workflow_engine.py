import pytest

from orchestrator.models.workflow import Workflow, WorkflowStatus
from orchestrator.services.workflow_engine import InvalidTransition, transition


def test_valid_transition_succeeds():
    wf = Workflow(event_id="evt-x")
    transition(wf, WorkflowStatus.triggered)
    assert wf.status == WorkflowStatus.triggered.value


def test_invalid_transition_raises():
    wf = Workflow(event_id="evt-x")
    with pytest.raises(InvalidTransition):
        transition(wf, WorkflowStatus.completed)


def test_terminal_states_have_no_outgoing_transitions():
    wf = Workflow(event_id="evt-x", status=WorkflowStatus.completed)
    with pytest.raises(InvalidTransition):
        transition(wf, WorkflowStatus.executing)
