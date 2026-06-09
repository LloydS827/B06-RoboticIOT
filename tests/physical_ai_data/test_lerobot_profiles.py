from physical_ai_data.lerobot_profiles import (
    AlohaProfile,
    FallbackProfile,
    PushTProfile,
    select_lerobot_profile,
)


def test_select_lerobot_profile_from_repo_id():
    assert isinstance(select_lerobot_profile("lerobot/pusht", "auto"), PushTProfile)
    assert isinstance(select_lerobot_profile("lerobot/aloha_sim_transfer_cube_human", "auto"), AlohaProfile)
    assert isinstance(select_lerobot_profile("unknown/repo", "auto"), FallbackProfile)


def test_explicit_profile_overrides_repo_id():
    assert isinstance(select_lerobot_profile("unknown/repo", "pusht"), PushTProfile)
    assert isinstance(select_lerobot_profile("lerobot/pusht", "fallback"), FallbackProfile)


def test_unknown_explicit_profile_raises():
    try:
        select_lerobot_profile("lerobot/pusht", "not-real")
    except ValueError as exc:
        assert "Unsupported LeRobot profile" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
