#!/usr/bin/env python3

"""
Takes in input an OONI Run v2 descriptor and returns an error in case in
which we are testing duplicate inputs or endpoints.

We do not consider the input duplicate if different nettests are testing
the same or a similar input source.

We do not consider the input duplicate when we're using HTTP3 and TCP/TLS
for the same input, since those are distinct measurements.
"""

import json
import sys


def webconnectivity(descr):
    urls = set()
    for nettest in descr["nettests"]:
        if nettest["test_name"] not in set(
            ["web_connectivity", "web_connectivity@v0.5"]
        ):
            continue
        for input in nettest["inputs"]:
            print(f"[web_connectivity] checking {input}...")
            if input in urls:
                raise RuntimeError(f"[web_connectivity] input {input} already present")
            urls.add(input)


def dnscheck(descr):
    urls = {
        "http3": set(),
        "otherwise": set(),
    }
    for nettest in descr["nettests"]:
        if nettest["test_name"] != "dnscheck":
            continue
        http3_enabled = nettest.get("options", {}).get("HTTP3Enabled", False)
        for input in nettest["inputs"]:
            print(f"[dnscheck] checking {input} http3_enabled={http3_enabled}...")
            if http3_enabled:
                if input in urls["http3"]:
                    raise RuntimeError(
                        f"[dnscheck] input {input} already present for http3_enabled={http3_enabled}"
                    )
                urls["http3"].add(input)
            else:
                if input in urls["otherwise"]:
                    raise RuntimeError(
                        f"[dnscheck] input {input} already present for http3_enabled={http3_enabled}"
                    )
                urls["otherwise"].add(input)


def checkdescr(descr):
    webconnectivity(descr)
    dnscheck(descr)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: ./script/dnscheck.py FILE")

    with open(sys.argv[1], "r") as infp:
        descr = json.load(infp)
        checkdescr(descr)


if __name__ == "__main__":
    main()
