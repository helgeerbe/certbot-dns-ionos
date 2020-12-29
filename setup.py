from setuptools import setup
from setuptools import find_packages

version = "0.0.5"

install_requires = [
    "acme>=0.29.0",
    "certbot>=0.34.0",
    "setuptools",
    "requests",
    "mock",
    "requests-mock",
]

# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.rst")) as f:
    long_description = f.read()

setup(
    name="certbot-dns-ionos",
    version=version,
    description="IONOS DNS Authenticator plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/helgeerbe/certbot-dns-ionos",
    author="Helge Erbe",
    author_email="helge@erbehome.de",
    license="Apache License 2.0",
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "certbot.plugins": [
            "dns-ionos = certbot_dns_ionos.dns_ionos:Authenticator"
        ]
    },
    test_suite="certbot_dns_ionos",
)
