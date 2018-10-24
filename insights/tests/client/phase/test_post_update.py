# -*- coding: UTF-8 -*-

from insights.client.phase.v1 import post_update
from mock.mock import patch
from pytest import raises

def patch_insights_config(old_function):
    patcher = patch("insights.client.phase.v1.InsightsConfig",
                    **{"return_value.load_all.return_value.status": False,
                       "return_value.load_all.return_value.unregister": False,
                       "return_value.load_all.return_value.offline": False,
                       "return_value.load_all.return_value.enable_schedule": False,
                       "return_value.load_all.return_value.disable_schedule": False,
                       "return_value.load_all.return_value.analyze_container": False,
                       "return_value.load_all.return_value.display_name": False,
                       "return_value.load_all.return_value.register": False})
    return patcher(old_function)


@patch("insights.client.phase.v1.InsightsClient")
@patch_insights_config
def test_post_update_payload_on(insights_config, insights_client):
    """
    Registration is not processed when a payload is uploaded
    """
    insights_config.return_value.load_all.return_value.payload = True
    try:
        post_update()
    except SystemExit:
        pass
    insights_client.return_value.register.assert_not_called()

@patch("insights.client.phase.v1.InsightsClient")
@patch_insights_config
def test_post_update_payload_off(insights_config, insights_client):
    """
    Registration is processed in normal operation (no payload)
    """
    insights_config.return_value.load_all.return_value.payload = False
    try:
        post_update()
    except SystemExit:
        pass
    insights_client.return_value.register.assert_called_once()

@patch("insights.client.phase.v1.InsightsClient")
@patch_insights_config
# @patch("insights.client.phase.v1.InsightsClient")
def test_exit_ok(insights_config, insights_client):
    """
    Support collection replaces the normal client run.
    """
    with raises(SystemExit) as exc_info:
        post_update()
    assert exc_info.value.code == 0