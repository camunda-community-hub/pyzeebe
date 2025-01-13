import os
from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.channel.utils import (
    DEFAULT_ZEEBE_ADDRESS,
    get_camunda_address,
    get_camunda_client_id,
    get_camunda_client_secret,
    get_camunda_cluster_id,
    get_camunda_cluster_region,
    get_camunda_oauth_url,
    get_camunda_token_audience,
    get_zeebe_address,
)
from pyzeebe.errors import SettingsError


class TestGetZeebeAddress:

    def test_returns_passed_address(self):
        address = str(uuid4())

        assert address == get_zeebe_address(address)

    def test_returns_default_address(self):
        address = get_zeebe_address()

        assert address == DEFAULT_ZEEBE_ADDRESS

    @patch.dict(
        os.environ,
        {"ZEEBE_ADDRESS": "ZEEBE_ADDRESS"},
    )
    def test_returns_env_var_if_provided(self):
        address = get_zeebe_address("zeebe_address")

        assert address == "ZEEBE_ADDRESS"


class TestGetCamundaOauthUrl:
    @patch.dict(
        os.environ,
        {"CAMUNDA_OAUTH_URL": "CAMUNDA_OAUTH_URL", "ZEEBE_AUTHORIZATION_SERVER_URL": "ZEEBE_AUTHORIZATION_SERVER_URL"},
    )
    def test_camunda_oauth_url_has_highest_priority(self):
        result = get_camunda_oauth_url("oauth_url")

        assert result == "CAMUNDA_OAUTH_URL"

    @patch.dict(os.environ, {"ZEEBE_AUTHORIZATION_SERVER_URL": "ZEEBE_AUTHORIZATION_SERVER_URL"})
    def test_zeebe_authorization_server_url_has_second_highest_priority(self):
        result = get_camunda_oauth_url("oauth_url")

        assert result == "ZEEBE_AUTHORIZATION_SERVER_URL"

    def test_param_has_lowest_priority(self):
        result = get_camunda_oauth_url("oauth_url")

        assert result == "oauth_url"

    @patch.dict(os.environ, {})
    def test_none_has_fourth_highest_priority(self):
        with pytest.raises(SettingsError):
            get_camunda_oauth_url()


class TestGetCamundaClientId:
    @patch.dict(os.environ, {"CAMUNDA_CLIENT_ID": "CAMUNDA_CLIENT_ID", "ZEEBE_CLIENT_ID": "ZEEBE_CLIENT_ID"})
    def test_is_calculated_from_camunda_environment_variable_as_highest_priority(self):
        result = get_camunda_client_id()

        assert result == "CAMUNDA_CLIENT_ID"

    @patch.dict(os.environ, {"ZEEBE_CLIENT_ID": "ZEEBE_CLIENT_ID"})
    def test_is_calculated_from_zeebe_environment_variable_as_second_priority(self):
        result = get_camunda_client_id()

        assert result == "ZEEBE_CLIENT_ID"

    @patch.dict(os.environ, {})
    def test_throw_exception_if_not_configured(self):
        with pytest.raises(SettingsError):
            get_camunda_client_id()


class TestGetCamundaClientSecret:
    @patch.dict(
        os.environ, {"CAMUNDA_CLIENT_SECRET": "CAMUNDA_CLIENT_SECRET", "ZEEBE_CLIENT_SECRET": "ZEEBE_CLIENT_SECRET"}
    )
    def test_is_calculated_from_camunda_environment_variable_as_highest_priority(self):
        result = get_camunda_client_secret()

        assert result == "CAMUNDA_CLIENT_SECRET"

    @patch.dict(os.environ, {"ZEEBE_CLIENT_SECRET": "ZEEBE_CLIENT_SECRET"})
    def test_is_calculated_from_zeebe_environment_variable_as_second_priority(self):
        result = get_camunda_client_secret()

        assert result == "ZEEBE_CLIENT_SECRET"

    @patch.dict(os.environ, {})
    def test_throw_exception_if_not_configured(self):
        with pytest.raises(SettingsError):
            get_camunda_client_secret()


class TestGetCamundaCloudClusterId:
    @patch.dict(os.environ, {"CAMUNDA_CLUSTER_ID": "CAMUNDA_CLUSTER_ID"})
    def test_is_calculated_from_camunda_environment_variable_as_highest_priority(self):
        result = get_camunda_cluster_id()

        assert result == "CAMUNDA_CLUSTER_ID"

    def test_environment_error(self):
        with pytest.raises(SettingsError):
            get_camunda_cluster_id()


class TestGetCamundaCloudClusterRegion:
    @patch.dict(os.environ, {"CAMUNDA_CLUSTER_REGION": "CAMUNDA_CLUSTER_REGION"})
    def test_is_calculated_from_camunda_environment_variable_as_highest_priority(self):
        result = get_camunda_cluster_region("cluster_region_param")

        assert result == "CAMUNDA_CLUSTER_REGION"

    def test_is_calculated_from_default_value_parameter_as_second_priority(self):
        result = get_camunda_cluster_region("cluster_region_param")

        assert result == "cluster_region_param"

    @patch.dict(os.environ, {})
    def test_raises_environment_error_if_no_default_value_as_fallback_provided(self):
        with pytest.raises(SettingsError):
            get_camunda_cluster_region()


class TestGetCamundaTokenAudience:
    @patch.dict(
        os.environ,
        {
            "CAMUNDA_TOKEN_AUDIENCE": "CAMUNDA_TOKEN_AUDIENCE",
            "ZEEBE_TOKEN_AUDIENCE": "ZEEBE_TOKEN_AUDIENCE",
        },
    )
    def test_is_calculated_from_camunda_token_audience_as_highest_priority(self):
        result = get_camunda_token_audience("token_audience_param")

        assert result == "CAMUNDA_TOKEN_AUDIENCE"

    @patch.dict(
        os.environ,
        {
            "ZEEBE_TOKEN_AUDIENCE": "ZEEBE_TOKEN_AUDIENCE",
        },
    )
    def test_is_calculated_from_zeebe_token_audience_as_second_highest_priority(self):
        result = get_camunda_token_audience("token_audience_param")

        assert result == "ZEEBE_TOKEN_AUDIENCE"

    def test_is_calculated_from_camunda_token_audience_as_third_highest_priority(self):
        result = get_camunda_token_audience("token_audience_param")

        assert result == "token_audience_param"

    @patch.dict(os.environ, {})
    def test_raises_environment_error_as_fourth_highest_priority(self):
        with pytest.raises(SettingsError):
            get_camunda_token_audience()


class TestGetCamundaAddress:
    def test_is_calculated_from_parameters_as_highest_priority(self):
        result = get_camunda_address("cluster_id_param", "camunda_region_param")

        assert result == "cluster_id_param.camunda_region_param.zeebe.camunda.io:443"

    def test_raises_error_if_cluster_id_is_none(self):
        with pytest.raises(SettingsError):
            get_camunda_address(None, "camunda_region_param")

    def test_raises_error_if_cluster_region_is_none(self):
        with pytest.raises(SettingsError):
            get_camunda_address("cluster_id_param", None)

    def test_raises_error_if_all_args_are_none(self):
        with pytest.raises(SettingsError):
            get_camunda_address(None, None)
