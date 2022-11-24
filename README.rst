certbot-dns-ionos
=====================

IONOS_ DNS Authenticator plugin for Certbot_

This plugin automates the process of completing a ``dns-01`` challenge by
creating, and subsequently removing, TXT records using the IONOS Remote API.

Configuration of IONOS
---------------------------

In the `System -> Remote Users` you have to have a user, with the following rights

- Client Functions
- DNS zone functions
- DNS txt functions


.. _IONOS: https://www.ionos.de/
.. _Certbot: https://certbot.eff.org/

Installation
------------

::

    pip install certbot-dns-ionos


Named Arguments
---------------

To start using DNS authentication for ionos, pass the following arguments on
certbot's command line:

=============================================== ===============================================
``--authenticator dns-ionos``                   select the authenticator plugin (Required)

``--dns-ionos-credentials``                     ionos Remote User credentials
                                                INI file. (Required)

``--dns-ionos-propagation-seconds``             waiting time for DNS to propagate before asking
                                                the ACME server to verify the DNS record.
                                                (Default: 10, Recommended: >= 600)
=============================================== ===============================================



Credentials
-----------

An example ``credentials.ini`` file:

.. code-block:: ini

   dns_ionos_prefix = myapikeyprefix
   dns_ionos_secret = verysecureapikeysecret
   dns_ionos_endpoint = https://api.hosting.ionos.com

The path to this file can be provided interactively or using the
``--dns-ionos-credentials`` command-line argument. Certbot
records the path to this file for use during renewal, but does not store the
file's contents.

**CAUTION:** You should protect these API credentials as you would the
password to your ionos account. Users who can read this file can use these
credentials to issue arbitrary API calls on your behalf. Users who can cause
Certbot to run using these credentials can complete a ``dns-01`` challenge to
acquire new certificates or revoke existing certificates for associated
domains, even if those domains aren't being managed by this server.

Certbot will emit a warning if it detects that the credentials file can be
accessed by other users on your system. The warning reads "Unsafe permissions
on credentials configuration file", followed by the path to the credentials
file. This warning will be emitted each time Certbot uses the credentials file,
including for renewal, and cannot be silenced except by addressing the issue
(e.g., by using a command like ``chmod 600`` to restrict access to the file and 
``chmod 700`` to restrict access to the folder).


Examples
--------

To acquire a single certificate for both ``example.com`` and
``*.example.com``, waiting 900 seconds for DNS propagation:

.. code-block:: bash

   certbot certonly \
     --authenticator dns-ionos \
     --dns-ionos-credentials /etc/letsencrypt/.secrets/domain.tld.ini \
     --dns-ionos-propagation-seconds 900 \
     --server https://acme-v02.api.letsencrypt.org/directory \
     --agree-tos \
     --rsa-key-size 4096 \
     -d 'example.com' \
     -d '*.example.com'


Docker
------

In order to create a docker container with a certbot-dns-ionos installation,
create an empty directory with the following ``Dockerfile``:

.. code-block:: docker

    FROM certbot/certbot
    RUN pip install certbot-dns-ionos

Proceed to build the image::

    docker build -t certbot/dns-ionos .

Once that's finished, the application can be run as follows::

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

It is suggested to secure the folder as follows::
chown root:root /etc/letsencrypt/.secrets
chmod 700 /etc/letsencrypt/.secrets

Changelog
=========

- 2022.05.15
  - Added capability to handle multiple domain validations #16

- 2021.09.20.post1

  - Fix version number

- 2021.09.20
  
  - Fix #9 Domain not known when using subdomain
