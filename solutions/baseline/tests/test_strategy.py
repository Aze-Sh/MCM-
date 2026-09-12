import importlib.util
import math
import numpy as np
import pytest


def modules():
    assert importlib.util.find_spec('b_strategy'), 'Search strategy not implemented'
    assert importlib.util.find_spec('b_simulation'), 'Synthetic simulator not implemented'
    import b_strategy, b_simulation
    return b_strategy, b_simulation


def test_polygon_clipping_keeps_true_source_and_wraps_angle():
    strategy, _ = modules()
    p = strategy.initial_region((0,0), 359.8)
    assert len(p) >= 3
    assert strategy.contains(p, (100,0))
    assert not strategy.contains(p, (-100,0))
    assert not strategy.contains(p, (1700,0))


def test_directional_cover_contains_all_cell_vertices_at_boundary():
    strategy, _ = modules()
    points = set(map(tuple, strategy.coverage_points()))
    # East-most boundary source cell extends outside the 1800m source disk.
    assert (2400.,0.) in points
    assert (2400.,600.) in points
    assert (1800.,0.) in points
    assert (1800.,600.) in points


def test_synthetic_protocol_matches_official_example_and_retry():
    _, sim = modules()
    from b_client import RobotClient
    world = sim.SyntheticSimulator([sim.Source(1, (600,800), 1200)])
    c = RobotClient('test', transport=world.transport)
    c.enter()
    c.measure((300,400),1)
    c.measure((300,400),2)
    c.clear((300,0),3)
    c.measure((300,0),2)
    c.exit()
    assert c.virtual_time == 199


@pytest.mark.parametrize('direction', [None,0,90,180,270])
def test_single_source_baseline_finds_and_clears_directional_cases(direction):
    strategy, sim = modules()
    from b_client import RobotClient
    world = sim.SyntheticSimulator([sim.Source(7, (1700,70), 1000, direction)], error_seed=17)
    c = RobotClient('test', transport=world.transport)
    c.enter()
    summary = strategy.search(c)
    assert c.cleared == {7}
    assert summary['coverage_complete']
    assert summary['all_detected_cleared']
    assert c.virtual_time == pytest.approx(c.accounted_time, abs=1e-3)


def test_failed_clear_does_not_overexclude_nearby_candidates():
    strategy, _ = modules()
    points = strategy.fallback_points(np.array([[0,0],[100,0],[100,100],[0,100]]), [(10,10)])
    # A failed clear at (10,10) cannot justify dropping a different centre (30,10):
    # the latter also covers possible sources outside the first clearance disk.
    assert (30.,10.) in list(map(tuple, points))
    assert (10.,10.) not in list(map(tuple, points))


def test_search_absorbs_localization_detours_into_remaining_coverage_route():
    strategy, sim = modules()
    from b_client import RobotClient
    sources = sim.random_case(20261001, mixed=False)
    world = sim.SyntheticSimulator(sources, error_seed=20261001)
    client = RobotClient('test', transport=world.transport)
    client.enter()
    summary = strategy.search(client)
    assert len(world.cleared) == len(sources)
    assert summary['coverage_complete']
    # The fixed serpentine baseline travels about 65.9 km in this case. A route
    # that resumes near each localization endpoint must save a material detour.
    assert world.distance < 62_000


def test_search_stops_immediately_after_known_maximum_is_cleared():
    strategy, sim = modules()
    from b_client import RobotClient
    sources = [sim.Source(channel, (0, 0), 1000) for channel in range(1, 17)]
    world = sim.SyntheticSimulator(sources, error_seed=3)
    client = RobotClient('test', transport=world.transport)
    client.enter()
    summary = strategy.search(client)
    assert len(world.cleared) == 16
    assert world.counts['measure'] == 16
    assert summary['completion_certified']
    assert summary['stop_reason'] == 'known_maximum_cleared'
