"""DNS Authenticator for IONOS."""
import json
import logging
import time

import requests
import zope.interface

from certbot import errors
from certbot import interfaces
from certbot.plugins import dns_common

logger = logging.getLogger(__name__)


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for IONOS

    This Authenticator uses the IONOS Remote REST API to fulfill a dns-01 challenge.
    """

    description = "Obtain certificates using a DNS TXT record (if you are using IONOS for DNS)."
    ttl = 60

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super(Authenticator, cls).add_parser_arguments(
            add, default_propagation_seconds=120
        )
        add("credentials", help="IONOS credentials INI file.")

    def more_info(self):  # pylint: disable=missing-docstring,no-self-use
        return (
            "This plugin configures a DNS TXT record to respond to a dns-01 challenge using "
            + "the IONOS Remote REST API."
        )

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            "credentials",
            "IONOS credentials INI file",
            {
                "endpoint": "URL of the IONOS Remote API.",
                "prefix": "Prefix for IONOS Remote API.",
                "secret": "Secret for IONOS Remote API.",
            },
        )

    def _perform(self, domain, validation_name, validation):
        self._get_ionos_client().add_txt_record(
            domain, validation_name, validation, self.ttl
        )

    def _cleanup(self, domain, validation_name, validation):
        self._get_ionos_client().del_txt_record(
            domain, validation_name, validation, self.ttl
        )

    def _get_ionos_client(self):
        return _ionosClient(
            self.credentials.conf("endpoint"),
            self.credentials.conf("prefix"),
            self.credentials.conf("secret"),
        )


class _ionosClient(object):
    """
    Encapsulates all communication with the IONOS Remote REST API.
    """

    def __init__(self, endpoint, prefix, secret):
        logger.debug("creating ionosclient")
        self.endpoint = endpoint
        self.headers = {}
        self.headers['accept'] = 'application/json'
        self.headers['X-API-Key'] = prefix + '.' + secret

    def _find_managed_zone_id(self, domain):
        """
        Find the managed zone for a given domain.

        :param str domain: The domain for which to find the managed zone.
        :returns: The ID of the managed zone, if found.
        :rtype: str zone id, str zone name
        """
        logger.debug("get zones")
        zones = self._api_request(type='get', action="/dns/v1/zones")
        logger.debug("zones found %s", zones)
        for zone in zones:
            # get the zone id
            if zone['name'] == domain:
                return zone['id'], zone['name']
        # if the domain does not exactly match one of the zones, check if it
        # is a subdomain
        for zone in zones:
            # get the zone id
            if domain.endswith(zone['name']):
                return zone['id'], zone['name']
        return None, None

    def _api_request(self, type, action, data = None):
        url = self._get_url(action)
        resp = None
        if type == 'get':
            resp = requests.get(url, headers=self.headers)
        elif type == 'put':
            headers = self.headers
            headers['Content-Type'] = 'application/json'
            resp = requests.put(url, headers=headers, data=json.dumps(data))
        elif type == 'post':
            headers = self.headers
            headers['Content-Type'] = 'application/json'
            resp = requests.post(url, headers=headers, data=json.dumps(data))
        elif type == 'delete':
            resp = requests.delete(url, headers=self.headers)
        else:
            raise errors.PluginError(
                "HTTP Error during request. Unknown type {0}".format(type)
            )
        logger.debug("API Request to URL: %s", url)
        if not resp.ok:
            content = json.loads(resp.content)
            raise errors.PluginError(
                "HTTP Error during request {0}:{1}".format(resp.status_code, content)
            )
        result = None
        if type == 'get':
            try:
                result = resp.json()
            except:
                raise errors.PluginError(
                    "API response with non JSON: {0}".format(resp.text)
                )
        return result

    def _get_url(self, action):
        return "{0}{1}".format(self.endpoint, action)

    def add_txt_record(self, domain, record_name, record_content, record_ttl):
        """
        Add a TXT record using the supplied information.

        :param str domain: The domain to use to look up the managed zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the IONOS API
        """
        zone_id, zone_name = self._find_managed_zone_id(domain)
        if zone_id is None:
            raise errors.PluginError("Domain not known")
        logger.debug("domain found: %s with id: %s", zone_name, zone_id)
        entries = self.get_existing_txts(zone_id, record_name)
        for entry in entries:
            if entry[0] == record_content:
                logger.info("already there, id {0} with content {1}".format(entry[1], entry[0]))
                return
        logger.info("insert new txt record")
        self._insert_txt_record(zone_id, record_name, record_content, record_ttl)

    def del_txt_record(self, domain, record_name, record_content, record_ttl):
        """
        Delete a TXT record using the supplied information.

        :param str domain: The domain to use to look up the managed zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the IONOS API
        """
        zone_id, zone_name = self._find_managed_zone_id(domain)
        if zone_id is None:
            raise errors.PluginError("Domain not known")
        logger.debug("domain found: %s with id: %s", zone_name, zone_id)
        entries = self.get_existing_txts(zone_id, record_name)
        maybe_entry = next(filter(lambda x: x[0] == record_content, entries), None)
        if maybe_entry is not None:
            self._delete_txt_record(zone_id, maybe_entry[1])

    def _update_txt_record(self, zone_id, primary_id, record_content, record_ttl):
        data = {}
        data['disabled'] = False
        data['content'] = record_content
        data['ttl'] = record_ttl
        data['prio'] = 0
        logger.debug("update with data: %s", data)
        self._api_request(type='put', action='/dns/v1/zones/{0}/records/{1}'.format(zone_id,primary_id), data=data)

    def _insert_txt_record(self, zone_id, record_name, record_content, record_ttl):
        data = {}
        data['disabled'] = False
        data['type'] = 'TXT'
        data['name'] = record_name
        data['content'] = record_content
        data['ttl'] = record_ttl
        data['prio'] = 0
        records = []
        records.append(data)
        logger.debug("insert with data: %s", data)
        self._api_request(type='post', action='/dns/v1/zones/{0}/records'.format(zone_id), data=records)

    def _delete_txt_record(self, zone_id, primary_id):
        logger.debug("delete id: %s", primary_id)
        self._api_request(type='delete', action='/dns/v1/zones/{0}/records/{1}'.format(zone_id,primary_id))

    def get_existing_txts(self, zone_id, record_name):
        """
        Get existing TXT records from the RRset for the record name.

        :param str zone_id: The ID of the managed zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').

        :returns: List of all TXT records with the provided record_name as tuple (content, id)
        :rtype: list[str, str]
        """
        zone_data = self._api_request(type='get', action='/dns/v1/zones/{0}'.format(zone_id))
        entries = filter(lambda x: x["name"] == record_name and x["type"] == "TXT", zone_data['records'])
        # seems "content" is double quoted. Remove quotes from content
        return list(map(lambda x: (x["content"].lstrip('\"').rstrip('\"'), x["id"]), entries))
