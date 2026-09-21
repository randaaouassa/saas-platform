from app.modules.dispatch.service import _candidate_score


def test_close_driver_scores_higher_than_far():
    near = _candidate_score(distance_km=1.0, active_deliveries=0)
    far = _candidate_score(distance_km=50.0, active_deliveries=0)
    assert near > far


def test_workload_reduces_score():
    free = _candidate_score(distance_km=5.0, active_deliveries=0)
    busy = _candidate_score(distance_km=5.0, active_deliveries=3)
    assert free > busy


def test_score_never_negative():
    s = _candidate_score(distance_km=1000.0, active_deliveries=100)
    assert s >= 0.0


def test_unknown_distance_uses_default():
    s = _candidate_score(distance_km=None, active_deliveries=0)
    assert s == 100.0