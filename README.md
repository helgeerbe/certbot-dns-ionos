# certbot-dns-ionos

[IONOS](https://www.ionos.de/) DNS Authenticator plugin for [Certbot](https://certbot.eff.org/)

![Ionos](https://www.ionos.co.uk/newsroom/wp-content/uploads/sites/7/2021/12/LOGO_IONOS_Blue_RGB-1.png)

This plugin automates the process of completing a ``dns-01`` challenge by
creating, and subsequently removing, TXT records using the [IONOS Remote API](https://developer.hosting.ionos.com/docs/dns).

## Configuration of IONOS

In the `System -> Remote Users` you have to have a user, with the following rights

- Client Functions
- DNS zone functions
- DNS txt functions

## Installation

### Snap

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/certbot-dns-ionos)
Snap version will be compatible with certbot 3.0. Thanks to [DorianCoding](https://github.com/DorianCoding) to make this plugin avalabe in the Snap Store.

### Pip

`pip install certbot-dns-ionos`

## Named Arguments

To start using DNS authentication for ionos, pass the following arguments on certbot's command line:

| Command args | Command definition |
| --- | --- |
|``--authenticator dns-ionos`` | select the authenticator plugin (Required) |
|``--dns-ionos-credentials`` |ionos Remote User credentials INI file. (Required) |
|``--dns-ionos-propagation-seconds``|waiting time for DNS to propagate before asking the ACME server to verify the DNS record. (Default: 10, Recommended: 60) |

## Credentials

An example ``credentials.ini`` file:

```ini
dns_ionos_prefix = myapikeyprefix
dns_ionos_secret = verysecureapikeysecret
dns_ionos_endpoint = https://api.hosting.ionos.com
```

The key can be managed under the following link:  <https://developer.hosting.ionos.de/?source=IonosControlPanel>

The path to this file can be provided interactively or using the
`--dns-ionos-credentials` command-line argument. Certbot
records the path to this file for use during renewal, but does not store the file's contents.

> [!CAUTION]
> You should protect these API credentials as you would the
password to your ionos account. Users who can read this file can use these credentials to issue arbitrary API calls
on your behalf. Users who can cause Certbot to run using these credentials can complete a ``dns-01`` challenge
to acquire new certificates or revoke existing certificates for associated domains, even if those domains aren't
being managed by this server.

> [!WARNING]
> Certbot will emit a warning if it detects that the credentials file can be accessed by other users on your system.
The warning reads "Unsafe permissions on credentials configuration file", followed by the path to the
credentials file. This warning will be emitted each time Certbot uses the credentials file, including for renewal,
and cannot be silenced except by addressing the issue (e.g., by using a command like ``chmod 600`` to 
restrict access to the file and ``chmod 700`` to restrict access to the folder).

## Examples

To acquire a single certificate for both ``example.com`` and
``*.example.com``, waiting 900 seconds for DNS propagation:

```bash
certbot certonly \
--authenticator dns-ionos \
--dns-ionos-credentials /etc/letsencrypt/.secrets/domain.tld.ini \
--dns-ionos-propagation-seconds 900 \
--server https://acme-v02.api.letsencrypt.org/directory \
--agree-tos \
--rsa-key-size 4096 \
-d 'example.com' \
-d '*.example.com'
```

## Docker

In order to create a docker container with a certbot-dns-ionos installation,
create an empty directory with the following ``Dockerfile``:

```docker
FROM certbot/certbot
RUN pip install certbot-dns-ionos
```

Proceed to build the image

```docker
docker build -t certbot/dns-ionos .
```

Once that's finished, the application can be run as follows::

```docker
docker run --rm \
-v /var/lib/letsencrypt:/var/lib/letsencrypt \
-v /etc/letsencrypt:/etc/letsencrypt \
--cap-drop=all \
certbot/dns-ionos certonly \
--authenticator dns-ionos \
--dns-ionos-propagation-seconds 900 \
--dns-ionos-credentials \
/etc/letsencrypt/.secrets/domain.tld.ini \
--no-self-upgrade \
--keep-until-expiring --non-interactive --expand \
--server https://acme-v02.api.letsencrypt.org/directory \
-d example.com -d '*.example.com'
```

It is suggested to secure the folder as follows

```bash
chown root:root /etc/letsencrypt/.secrets
chmod 700 /etc/letsencrypt/.secrets
```

The file 'domain.tld.ini' must be replaced with the version of the example 'credentials.ini' adapted to your provider.

## Changelog

- 2024.11.09
  - Update for Certbot 3.0.0
- 2024.10.20
  - fix: set long_description_content_type to text/markdown.
    This error breaks the upload to pypi
- 2024.10.19
  - Update for Certbot 2.11.0
  - Update README.md, changed from README.rst
  - Addition of a snap
  - Correction in case of API error
- 2024.01.08
  - Update README.rst
  - Add Link to IONOS control panel and reference between credentials.ini and domain.tld.ini
- 2023.11.13
  - Fix managed zone lookup to ensure correct domain is selected where there are two domains with the same ending e.g. example.com and thisisanexample.com (PR #22)
- 2022.11.24
  - Remove zope to fix compatibility with Certbot 2.x (Fixes #19)
  - As a reminder, Certbot will default to issuing ECDSA certificates from release 2.0.0.
  - If you update from a prior certbot release, run the plugin once manually. You will be prompted to update RSA key type to ECDSA.
- 2022.05.15
  - Added capability to handle multiple domain validations #16
- 2021.09.20.post1
  - Fix version number
- 2021.09.20
  - Fix #9 Domain not known when using subdomain

## Related Plugins

It's important to note that this plugin targets [IONOS Developer DNS API](https://developer.hosting.ionos.com/docs/dns>).
If you are using IONOS [Cloud DNS service](https://cloud.ionos.com/network/cloud-dns>),
there is a different plugin provided by IONOS: <https://github.com/ionos-cloud/certbot-dns-ionos-cloud>
