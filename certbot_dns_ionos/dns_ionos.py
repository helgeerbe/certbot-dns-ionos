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
        logger.debug(f"_perform called with: domain: {domain}, validation_name: {validation_name}, validation: {validation}")
        self._get_ionos_client().add_txt_record(
            domain, validation_name, validation, self.ttl
        )

    def _cleanup(self, domain, validation_name, validation):
        self._get_ionos_client().del_matching_records(
            domain, validation_name
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
        elif type == 'patch':
            headers = self.headers
            headers['Content-Type'] = 'application/json'
            resp = requests.patch(url, headers=headers, data=json.dumps(data))
        elif type == 'delete':
            resp = requests.delete(url, headers=self.headers)
        else:
            raise errors.PluginError(
                "HTTP Error during request. Unknown type {0}".format(type)
            )
        logger.debug("API request to URL: %s", url)
        if resp.status_code != 200:
            content = json.loads(resp.content)[0] # on error content is array with 1 element
            error_msg = resp.reason + " " + content['message']
            raise errors.PluginError(
                "HTTP Error during request {0}:{1}".format(resp.status_code, error_msg)
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
        content, id = self.get_existing_txt(zone_id, record_name)
        if content is not None:
            if content == record_content:
                logger.info("already there, id {0}".format(id))
                return
            else:
                logger.info("adding additional record")
                entries = self.clean_entries(self.get_existing_records(zone_id, record_name))
                self.add_additional_record(
                    zone_id, record_name, record_content, record_ttl, entries
                )
        else:
            logger.info("insert new txt record")
            self._insert_txt_record(zone_id, record_name, record_content, record_ttl)

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
        self._api_request(type='patch', action='/dns/v1/zones/{0}'.format(zone_id), data=records)

    def _delete_txt_record(self, zone_id, primary_id):
        logger.debug("delete id: %s", primary_id)
        self._api_request(type='delete', action='/dns/v1/zones/{0}/records/{1}'.format(zone_id,primary_id))

    def get_existing_txt(self, zone_id, record_name):
        """
        Get existing TXT records from the RRset for the record name.

        If an error occurs while requesting the record set, it is suppressed
        and None is returned.

        :param str zone_id: The ID of the managed zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').

        :returns: TXT record value or None, record id or None
        :rtype: `string` or `None`, `string` or `None`

        """
        zone_data = self._api_request(type='get', action='/dns/v1/zones/{0}'.format(zone_id))
        for entry in zone_data['records']:
            if (
                entry["name"] == record_name
                and entry["type"] == "TXT"
            ):
                #seems "content" is double quoted. Remove quotes
                content = entry["content"]
                content = content.lstrip('\"')
                content = content.rstrip('\"')
                return content, entry["id"]
        return None, None

    def get_existing_records(self, zone_id, record_name):
        """
        Pull a list of existing TXT records with the record_name
        """
        zone_data = self._api_request(type='get', action='/dns/v1/zones/{0}'.format(zone_id))
        results = []
        for entry in zone_data['records']:
            if entry["name"] == record_name and entry["type"] == "TXT":
                results.append(entry)
        return results

    def clean_entries(self, entries):
        """
        Clean up existing DNS entries to prepare to write them back to the API
            by only including certain keys and cleaning up the content.
        """
        results = []
        for entry in entries:
            results.append({
                'name': entry['name'],
                'type': entry['type'],
                'content': entry['content'].replace('"', ''),  # Strip double-quotes
                'ttl': entry['ttl'],
                'disabled': entry['disabled'],
            })
        return results

    def add_additional_record(self, zone_id, record_name, record_content, record_ttl, existing_records):
        """
        Add another TXT record with the record_name but with new content. This
            is done to allow multiple domains to be validated at the same time.
        existing_records is a list of existing records since we need to issue
            a PATCH and include the existing records.
        """
        data = {}
        data['disabled'] = False
        data['type'] = 'TXT'
        data['name'] = record_name
        data['content'] = record_content
        data['ttl'] = record_ttl
        data['prio'] = 0
        existing_records.append(data)
        logger.debug("insert with data: %s", existing_records)
        self._api_request(type='patch', action='/dns/v1/zones/{0}'.format(zone_id), data=existing_records)

    def del_matching_records(self, domain, record_name):
        """
        Deletes any TXT records with matching record_name. Loops through all
            records with that name and deletes them.
        """
        zone_id, zone_name = self._find_managed_zone_id(domain)
        if zone_id is None:
            raise errors.PluginError("Domain not known")
        logger.debug("domain found: %s with id: %s", zone_name, zone_id)
        entries = self.get_existing_records(zone_id, record_name)
        for entry in entries:
            self._delete_txt_record(zone_id, entry['id'])
