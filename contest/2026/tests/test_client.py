import importlib.util
import json
import pytest


def client_module():
    assert importlib.util.find_spec('b_client'), 'B protocol client is not implemented'
    import b_client
    return b_client


def reply(t, **fields):
    return 200, dict(accepted=True, real_timestamp_ms=1760000000000, virtual_time_s=t, **fields)


def test_official_199_second_sequence_and_clear_preserves_channel(tmp_path):
    mod = client_module()
    responses = iter([
        reply(0, remaining_real_duration_s=1200, max_real_duration_s=1200, max_virtual_duration_s=360000),
        reply(105, measure_result='direction', svd_deg=12.34),
        reply(111, measure_result='near'),
        reply(194, clear_result='no_target_in_range'),
        reply(199, measure_result='no_signal'),
        reply(199, exit_reason='user_exit'),
    ])
    c = mod.RobotClient('test-team', transport=lambda path, body: next(responses), log_path=tmp_path/'actions.jsonl')
    c.enter()
    c.measure((300, 400), 1)
    c.measure((300, 400), 2)
    c.clear((300, 0), 3)
    assert c.channel == 2
    c.measure((300, 0), 2)
    c.exit()
    assert c.virtual_time == 199
    assert c.accounted_time == 199
    assert c.position == (300, 0)
    assert c.cleared == set()
    assert len((tmp_path/'actions.jsonl').read_text().splitlines()) == 6


def test_response_loss_reuses_identical_request_and_counts_success_once():
    mod = client_module()
    seen = []
    def transport(path, raw):
        if path == '/enter':
            return reply(0, remaining_real_duration_s=1200, max_virtual_duration_s=360000)
        seen.append((path, raw))
        if len(seen) == 1:
            raise TimeoutError('Server accepted action but response was lost')
        return reply(5, clear_result='success')
    c = mod.RobotClient('test-team', transport=transport, retry_delay=0)
    c.enter()
    c.clear((0, 0), 7)
    assert seen[0] == seen[1]
    assert c.cleared == {7}
    assert c.accounted_time == 5
    assert c.channel == 1


def test_rejected_action_does_not_reset_state():
    mod = client_module()
    answers = iter([reply(0, remaining_real_duration_s=1200), reply(25, measure_result='no_signal'),
                    (200, dict(accepted=False, real_timestamp_ms=0, virtual_time_s=0))])
    c = mod.RobotClient('test-team', transport=lambda p, b: next(answers))
    c.enter()
    c.measure((100, 0), 1)
    with pytest.raises(mod.ProtocolError):
        c.clear((200, 0), 2)
    assert c.position == (100, 0)
    assert c.virtual_time == 25


def test_unknown_outcome_blocks_different_new_action():
    mod = client_module()
    def transport(path, raw):
        if path == '/enter': return reply(0, remaining_real_duration_s=1200)
        raise TimeoutError('lost')
    c = mod.RobotClient('test-team', transport=transport, retries=0)
    c.enter()
    with pytest.raises(mod.UncertainAction): c.measure((100, 0), 1)
    with pytest.raises(mod.UncertainAction): c.measure((200, 0), 1)
    assert c.position == (0, 0)


def test_malformed_success_cannot_enable_new_action():
    mod = client_module()
    responses = iter([reply(0, remaining_real_duration_s=1200), (200, {'virtual_time_s': 5})])
    c = mod.RobotClient('test', transport=lambda p,b: next(responses))
    c.enter()
    with pytest.raises(mod.UncertainAction): c.measure((0,0),1)
    with pytest.raises(mod.UncertainAction): c.clear((0,0),1)


@pytest.mark.parametrize('position,channel', [((float('nan'),0),1), ((2000001,0),1), ((0,0),21), ((0,0),True)])
def test_invalid_action_is_rejected_before_network(position, channel):
    mod = client_module()
    c = mod.RobotClient('test-team', transport=lambda p,b: pytest.fail('Invalid input reached transport'))
    with pytest.raises(ValueError): c.measure(position, channel)
