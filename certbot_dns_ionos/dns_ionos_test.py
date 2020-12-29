"""Tests for certbot_dns_ionos.dns_ionos."""

import unittest

import mock
import json
import requests_mock

from certbot import errors
from certbot.compat import os
from certbot.errors import PluginError
from certbot.plugins import dns_test_common
from certbot.plugins.dns_test_common import DOMAIN
from certbot.tests import util as test_util

FAKE_PREFIX = "prefix"
FAKE_SECRET = "secret"
FAKE_ENDPOINT = "mock://endpoint"


class AuthenticatorTest(
    test_util.TempDirTestCase, dns_test_common.BaseAuthenticatorTest
):
    def setUp(self):
        super(AuthenticatorTest, self).setUp()

        from certbot_dns_ionos.dns_ionos import Authenticator

        path = os.path.join(self.tempdir, "file.ini")
        dns_test_common.write(
            {
                "ionos_prefix": FAKE_PREFIX,
                "ionos_secret": FAKE_SECRET,
                "ionos_endpoint": FAKE_ENDPOINT,
            },
            path,
        )

        super(AuthenticatorTest, self).setUp()
        self.config = mock.MagicMock(
            ionos_credentials=path, ionos_propagation_seconds=0
        )  # don't wait during tests

        self.auth = Authenticator(self.config, "ionos")

        self.mock_client = mock.MagicMock()
        # _get_ionos_client | pylint: disable=protected-access
        self.auth._get_ionos_client = mock.MagicMock(return_value=self.mock_client)

    def test_perform(self):
        self.auth.perform([self.achall])

        expected = [
            mock.call.add_txt_record(
                DOMAIN, "_acme-challenge." + DOMAIN, mock.ANY, mock.ANY
            )
        ]
        self.assertEqual(expected, self.mock_client.mock_calls)

    def test_cleanup(self):
        # _attempt_cleanup | pylint: disable=protected-access
        self.auth._attempt_cleanup = True
        self.auth.cleanup([self.achall])

        expected = [
            mock.call.del_txt_record(
                DOMAIN, "_acme-challenge." + DOMAIN, mock.ANY, mock.ANY
            )
        ]
        self.assertEqual(expected, self.mock_client.mock_calls)


class ionosClientTest(unittest.TestCase):
    record_name = "foo"
    record_content = "bar"
    record_ttl = 42

    def setUp(self):
        from certbot_dns_ionos.dns_ionos import _ionosClient
        self.client = _ionosClient(FAKE_ENDPOINT, FAKE_PREFIX, FAKE_SECRET)

    def test_add_txt_record(self):
        with requests_mock.Mocker() as m:
            mock_response = [{
                "id": "11af3414-ebba-11e9-8df5-66fbe8a334b4",
                "name": "example.com",
                "type": "NATIVE"}]
            m.register_uri('GET', 'mock://endpoint/dns/v1/zones', status_code=200, reason="OK", json=mock_response)
            mock_response = {
                "id": "11af3414-ebba-11e9-8df5-66fbe8a334b4",
                "name": "example.com",
                "type": "NATIVE",
                "records": [
                    {
                    "id": "22af3414-abbe-9e11-5df5-66fbe8e334b4",
                    "name": "foo",
                    "rootName": "string",
                    "type": "TXT",
                    "content": "string",
                    "changeDate": "string",
                    "ttl": 0,
                    "prio": 0,
                    "disabled": False
                    }
                ]
            }
            m.register_uri('GET', 'mock://endpoint/dns/v1/zones/11af3414-ebba-11e9-8df5-66fbe8a334b4', status_code=200, reason="OK", json=mock_response)
            m.register_uri('PUT', 'mock://endpoint/dns/v1/zones/11af3414-ebba-11e9-8df5-66fbe8a334b4/records/22af3414-abbe-9e11-5df5-66fbe8e334b4', status_code=200, reason="OK")
            try:
                self.client.add_txt_record(
                    DOMAIN, self.record_name, self.record_content, self.record_ttl
                )
            except:
                self.fail("No exeption expected")

    def test_add_txt_record_fail_to_find_domain(self):
        with requests_mock.Mocker() as m:
            mock_response = [{
                "id": "11af3414-ebba-11e9-8df5-66fbe8a334b4",
                "name": "test.com",
                "type": "NATIVE"}]
            m.register_uri('GET', 'mock://endpoint/dns/v1/zones', status_code=200, reason="OK", json=mock_response)
            with self.assertRaises(errors.PluginError) as context:
                self.client.add_txt_record(
                    DOMAIN, self.record_name, self.record_content, self.record_ttl
                )

    
    def test_add_txt_record_fail_to_authenticate(self):
        with requests_mock.Mocker() as m:
            mock_response = {'message': 'Missing or invalid API key.'}
            m.register_uri('GET', 'mock://endpoint/dns/v1/zones', status_code=401, reason="Unauthorized", json=mock_response)
            with self.assertRaises(errors.PluginError) as context:
                self.client.add_txt_record(
                    DOMAIN, self.record_name, self.record_content, self.record_ttl
                )

    def test_del_txt_record(self):
        with requests_mock.Mocker() as m:
            mock_response = [{
                "id": "11af3414-ebba-11e9-8df5-66fbe8a334b4",
                "name": "example.com",
                "type": "NATIVE"}]
            m.register_uri('GET', 'mock://endpoint/dns/v1/zones', status_code=200, reason="OK", json=mock_response)
            mock_response = {
                "id": "11af3414-ebba-11e9-8df5-66fbe8a334b4",
                "name": "example.com",
                "type": "NATIVE",
                "records": [
                    {
                    "id": "22af3414-abbe-9e11-5df5-66fbe8e334b4",
                    "name": "foo",
                    "rootName": "string",
                    "type": "TXT",
                    "content": "string",
                    "changeDate": "string",
                    "ttl": 0,
                    "prio": 0,
                    "disabled": False
                    }
                ]
            }
            m.register_uri('GET', 'mock://endpoint/dns/v1/zones/11af3414-ebba-11e9-8df5-66fbe8a334b4', status_code=200, reason="OK", json=mock_response)
            m.register_uri('DELETE', 'mock://endpoint/dns/v1/zones/11af3414-ebba-11e9-8df5-66fbe8a334b4/records/22af3414-abbe-9e11-5df5-66fbe8e334b4', status_code=200, reason="OK")
            try:
                self.client.del_txt_record(
                    DOMAIN, self.record_name, self.record_content, self.record_ttl
                )
            except:
                    self.fail("No exeption expected")



if __name__ == "__main__":
    unittest.main()  # pragma: no cover
