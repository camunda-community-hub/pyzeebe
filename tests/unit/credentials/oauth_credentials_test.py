from uuid import uuid4

import pytest
from mock import patch
from requests import HTTPError

from pyzeebe.credentials.oauth_credentials import OAuthCredentials
from pyzeebe.errors import InvalidOAuthCredentialsError


def test_get_access_token():
    with patch("requests_oauthlib.OAuth2Session.post") as post_mock:
        url = f"https://{str(uuid4())}/oauth/token"
        client_id = str(uuid4())
        client_secret = str(uuid4())
        audience = str(uuid4())
        OAuthCredentials.get_access_token(
            url=url, client_id=client_id, client_secret=client_secret, audience=audience)
        post_mock.assert_called_with(url,
                                     data={
                                         "client_id": client_id,
                                         "client_secret": client_secret,
                                         "audience": audience
                                     })


def test_get_invalid_access_token():
    with patch("requests_oauthlib.OAuth2Session.post") as post_mock:
        post_mock.side_effect = HTTPError()

        with pytest.raises(InvalidOAuthCredentialsError):
            OAuthCredentials.get_access_token(url=f"https://{str(uuid4())}/oauth/token", client_id=str(uuid4()),
                                              client_secret=str(uuid4()), audience=str(uuid4()))
