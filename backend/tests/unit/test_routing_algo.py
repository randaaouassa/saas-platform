from app.modules.routing.service import _nearest_neighbor_order


def test_empty_points_returns_empty():
    assert _nearest_neighbor_order(None, []) == []


def test_single_point():
    assert _nearest_neighbor_order(None, [(1.0, 1.0)]) == [0]


def test_orders_by_proximity_to_start():
    start = (0.0, 0.0)
    points = [(10.0, 10.0), (1.0, 1.0), (5.0, 5.0)]
    order = _nearest_neighbor_order(start, points)
    # nearest to origin first, then next-nearest, then farthest
    assert order[0] == 1  # (1,1)
    assert order[1] == 2  # (5,5)
    assert order[2] == 0  # (10,10)


def test_returns_all_indices():
    points = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]
    order = _nearest_neighbor_order(None, points)
    assert sorted(order) == [0, 1, 2]