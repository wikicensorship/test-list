#!/usr/bin/env python3

"""
This script takes in input a single file containing a list of DoT/DoH
endpoint URLs to be measured and outputs a list of JSON entries suitable
for testing those endpoints using dnscheck and OONI Run v2.
"""

import ipaddress
import sys
import json
from urllib.parse import urlsplit, urlencode, urlunparse
from urllib.request import urlopen


def calldohwithtype(domain, type):
    out = []
    scheme = "https"
    hostname = "dns.google"
    path = "/resolve"
    params = {
        "name": domain,
        "type": type,
    }
    query_string = urlencode(params)
    dohurl = urlunparse((scheme, hostname, path, "", query_string, ""))
    sys.stderr.write(f"DNS: lookup {dohurl}...\n")
    with urlopen(dohurl) as httpresp:
        data = httpresp.read()
        response = json.loads(data)
        for answer in response["Answer"]:
            atype = answer["type"]
            if (atype == 1 and type == "A") or (atype == 28 and type == "AAAA"):
                out.append(answer["data"])
    return out


def calldoh(domain):
    out = []
    out.extend(calldohwithtype(domain, "A"))
    out.extend(calldohwithtype(domain, "AAAA"))
    return " ".join(out)


def newentries(input_url):
    supports_quic = set(
        [
            "dns.google",
            "8.8.8.8",
            "cloudflare-dns.com",
            "1.1.1.1",
            "1.0.0.1",
            "family.cloudflare-dns.com",
            "1dot1dot1dot1.cloudflare-dns.com",
        ]
    )

    default_addrs = ""
    parsed_url = urlsplit(input_url)

    try:
        ipaddress.ip_address(str(parsed_url.hostname))
    except ValueError:
        default_addrs = calldoh(parsed_url.hostname)

    yield {
        "inputs": [
            input_url,
        ],
        "options": {
            "DefaultAddrs": default_addrs,
            "HTTP3Enabled": False,
        },
        "test_name": "dnscheck",
    }

    if parsed_url.scheme == "https" and parsed_url.hostname in supports_quic:
        yield {
            "inputs": [
                input_url,
            ],
            "options": {
                "DefaultAddrs": default_addrs,
                "HTTP3Enabled": True,
            },
            "test_name": "dnscheck",
        }


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: ./script/dnscheck.py FILE")

    entries = []
    with open(sys.argv[1], "r") as infp:
        for line in infp:
            line = line.strip()
            for entry in newentries(line):
                entries.append(entry)

    json.dump(entries, sys.stdout, indent="    ")
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
