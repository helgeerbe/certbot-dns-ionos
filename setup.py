from setuptools import setup
from setuptools import find_packages

version = "0.2.0"

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
with open(path.join(this_directory, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="certbot-dns-ispconfig",
    version=version,
    description="ispconfig DNS Authenticator plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/m42e/certbot-dns-ispconfig",
    author="Matthias Bilger",
    author_email="matthias@bilger.info",
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
            "dns-ispconfig = certbot_dns_ispconfig.dns_ispconfig:Authenticator"
        ]
    },
    test_suite="certbot_dns_ispconfig",
)
