import pytest
from harness.run_registry import COMPLETED, FAILED, PENDING, RUNNING, Run, RunRegistry


@pytest.fixture
def registry(tmp_path):
    return RunRegistry(tmp_path / "test.db")


def test_create_run_returns_pending_run(registry):
    run = registry.create_run("my_workflow", "subject-1", {"company_id": "123"})
    assert isinstance(run, Run)
    assert run.status == PENDING
    assert run.workflow == "my_workflow"
    assert run.subject == "subject-1"
    assert run.inputs == {"company_id": "123"}
    assert run.attempt == 1
    assert run.started_at is None
    assert run.outputs is None
    assert run.error is None
    assert len(run.run_id) == 36  # UUID4 format


def test_create_run_generates_unique_ids(registry):
    run_a = registry.create_run("wf", "s", {})
    run_b = registry.create_run("wf", "s", {})
    assert run_a.run_id != run_b.run_id


def test_mark_running_first_time_does_not_increment_attempt(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    updated = registry.get_run(run.run_id)
    assert updated.status == RUNNING
    assert updated.attempt == 1
    assert updated.started_at is not None


def test_mark_running_on_resume_increments_attempt_and_clears_error(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    registry.fail_run(run.run_id, "timeout")
    registry.mark_running(run.run_id)  # resume
    updated = registry.get_run(run.run_id)
    assert updated.status == RUNNING
    assert updated.attempt == 2
    assert updated.error is None


def test_complete_run(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    registry.complete_run(run.run_id, {"report": "text", "score": 87})
    updated = registry.get_run(run.run_id)
    assert updated.status == COMPLETED
    assert updated.outputs == {"report": "text", "score": 87}
    assert updated.completed_at is not None


def test_fail_run(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    registry.fail_run(run.run_id, "API rate limit exceeded")
    updated = registry.get_run(run.run_id)
    assert updated.status == FAILED
    assert updated.error == "API rate limit exceeded"
    assert updated.completed_at is not None


def test_get_run_returns_none_for_unknown_id(registry):
    assert registry.get_run("00000000-0000-0000-0000-000000000000") is None


def test_list_runs_returns_all(registry):
    registry.create_run("wf_a", "s1", {})
    registry.create_run("wf_b", "s2", {})
    runs = registry.list_runs()
    assert len(runs) == 2


def test_list_runs_filters_by_workflow(registry):
    registry.create_run("wf_a", "s1", {})
    registry.create_run("wf_b", "s2", {})
    runs = registry.list_runs(workflow="wf_a")
    assert len(runs) == 1
    assert runs[0].workflow == "wf_a"


def test_list_runs_filters_by_status(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    registry.complete_run(run.run_id, {})
    registry.create_run("wf", "s2", {})  # PENDING
    completed = registry.list_runs(status=COMPLETED)
    assert len(completed) == 1
    assert completed[0].status == COMPLETED


def test_list_runs_ordered_newest_first(registry):
    import time
    registry.create_run("wf", "s1", {})
    time.sleep(0.01)
    registry.create_run("wf", "s2", {})
    runs = registry.list_runs()
    assert runs[0].created_at > runs[1].created_at
