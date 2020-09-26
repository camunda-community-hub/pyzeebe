from unittest.mock import patch
from uuid import uuid4

from pyzeebe.credentials.oauth_credentials import OAuthCredentials


def test_get_access_token():
    with patch("requests_oauthlib.OAuth2Session.post") as post_mock:
        url = f"https://{str(uuid4())}/oauth/token"
        client_id = str(uuid4())
        client_secret = str(uuid4())
        audience = str(uuid4())
        OAuthCredentials.get_access_token(url=url, client_id=client_id, client_secret=client_secret, audience=audience)
        post_mock.assert_called_with(url,
                                     data={
                                         "client_id": client_id,
                                         "client_secret": client_secret,
                                         "audience": audience
                                     })
