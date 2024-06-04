from unittest.mock import Mock

import grpc
import pytest

from pyzeebe import AuthMetadataPlugin
from pyzeebe.credentials.base import CredentialsABC
from pyzeebe.credentials.typing import CallContext
from pyzeebe.errors.credentials_errors import InvalidOAuthCredentialsError


class TestAuthMetadataPlugin:
    @pytest.fixture()
    def credentials_mock(self) -> Mock:
        return Mock(spec_set=CredentialsABC)

    @pytest.fixture()
    def callback_mock(self) -> Mock:
        return Mock(spec_set=grpc.AuthMetadataPluginCallback)

    @pytest.fixture()
    def context_mock(self) -> Mock:
        return Mock(spec_set=CallContext)

    def test_auth_plugin_metadata_success(
        self, context_mock: Mock, credentials_mock: Mock, callback_mock: Mock
    ) -> None:
        metadata_mock = Mock()

        credentials_mock.get_auth_metadata.return_value = metadata_mock

        plugin = AuthMetadataPlugin(credentials=credentials_mock)

        plugin(context_mock, callback_mock)

        callback_mock.assert_called_once_with(metadata_mock, None)
        credentials_mock.get_auth_metadata.assert_called_once_with(context_mock)

    def test_auth_plugin_metadata_exception(
        self, context_mock: Mock, credentials_mock: Mock, callback_mock: Mock
    ) -> None:
        exception = InvalidOAuthCredentialsError(url=Mock(), client_id=Mock(), audience=Mock())
        credentials_mock.get_auth_metadata.side_effect = [exception]

        plugin = AuthMetadataPlugin(credentials=credentials_mock)

        plugin(context_mock, callback_mock)

        callback_mock.assert_called_once_with((), exception)
        credentials_mock.get_auth_metadata.assert_called_once_with(context_mock)
