#!/usr/bin/python
# -*- coding: utf-8 -*-

import geoip
import yaml
import sys
import os

import subprocess
from subprocess import PIPE, STDOUT


class ErrorParsingEntry(Exception):
    pass

class FormatNotSupported(Exception):
    pass

class BGPPeer(object):
    def __init__(self, address, asn):
        self.address = address
        self.asn = asn

class ASPath(object):
    def __init__(self, s):
        self.path = s.split(' ')

    def contains(self, asn):
        if asn in self.path:
            return True
        else:
            return False

class Prefixes(object):
    pass

class BGPEntry(object):
    toAddr = '127.0.0.1'
    toASN = 0

    fromPeer = None
    toPeer = None
    prefixes = ''
    ASPath = None
    originProtocol = ''
    nextHop = ''
    community = ''

    def relatedTo(self, asns):
        """
        We look at the Origin and AS Path to see if it contains the specified
        AS Number.

        Returns: True or False
        """
        for asn in asns:
            if (self.ASPath and self.ASPath.contains(asn)) \
                    or asn == self.fromPeer:
                return True
            else:
                return False

class BGPPrefixes(object):
    def __init__(self, prefixes):
        self.prefixes = prefixes

class BGPWithdraw(BGPEntry):
    def fromParts(self, parts):
        message_type, timestamp, \
        xxx1, \
        from_addr, from_asn, prefixes = parts

        self.fromPeer = BGPPeer(from_addr, int(from_asn))
        self.toPeer = BGPPeer(self.to_addr, self.to_asn)
        self.prefixes = BGPPrefixes(prefixes)

class BGPUpdate(BGPEntry):
    def fromParts(self, parts):
        message_type, timestamp, \
        xxx1, \
        from_addr, from_asn, prefixes, as_path, \
        origin_protocol, next_hop, \
        xxx2, xxx3, \
        community, \
        xxx4, xxx5, xxx6 = parts

        self.fromPeer = BGPPeer(from_addr, int(from_asn))
        self.toPeer = BGPPeer(self.to_addr, self.to_asn)
        self.prefixes = BGPPrefixes(prefixes)

        self.ASPath = ASPath(as_path)
        self.originProtocol = origin_protocol
        self.nextHop = next_hop
        self.community = community

class BGPEntryFactory(object):
    """
    Factory that takes care of creating instances of BGP Entry messages.
    """
    def fromLine(self, line):
        """
        Takes a line in the output of the command bgpdump -m mrt_file.bz2

        An Update Announce looks like this:

            BGP4MP|1354132819|A|164.128.32.11|3303|120.125.128.0/18|3303 15412 9264 7539 1659|EGP|164.128.32.11|0|0|3303:3008 3303:3050 15412:603 15412:621 15412:805 15412:1311|NAG||

        A Withdraw looks like this:

            BGP4MP|1354132819|W|67.17.82.114|3549|95.29.252.0/24
        """
        parts = line.strip().split('|')
        format_type, timestamp, message_type = parts[:3]

        if message_type == 'A':
            bgp_announce = BGPUpdate()
            bgp_announce.fromParts(parts)
            return bgp_announce

        elif message_type == 'W':
            bgp_widthdraw = BGPWithdraw()
            bgp_widthdraw.fromParts(parts)
            return bgp_widthdraw

class BGPDump(object):
    bgpdump = '/usr/local/bin/bgpdump'
    updateFiles = []
    entryFactory = BGPEntryFactory()

    def parseLine(self, line):
        entry = BGPEntry()
        entry.fromLine(line)
        return entry

    def getUpdates(self, asns=[]):
        """
        Returns all the BGP update messages that are related to a certain set
        of AS numbers.

        Args:

            asns (list): a list of strings containing the AS numbers to look for
                updates on.

        """
        BGPEntry.to_addr = '128.223.51.102'
        BGPEntry.to_asn = 6447

        for filename in self.updateFiles:
            cmd = [self.bgpdump, '-m', filename]
            print "Running %s" % cmd
            p = subprocess.Popen(cmd, stdout = PIPE)
            for line in p.stdout:
                entry = self.entryFactory.fromLine(line)
                if entry.relatedTo(asns):
                    yield entry
                else:
                    del entry

    def getYAMLUpdates(self,  asns=[]):
        for entry in self.getUpdates(asns):
            yield yaml.dump(self.getUpdates(asns))

try:
    filename = sys.argv[1]
except:
    print "run with python parser.py <filename>"

bgpdump = BGPDump()
# basepath = "path/to/bgp/bgpfoo/updates/"
# REPLACE THESE WITH THE UPDATE FILES OF THE TIMEFRAME YOU ARE INTERESTED IN
#
# filename1 = os.path.join(basepath, 'updates.20121128.2145.bz2')
# filename2 = os.path.join(basepath, 'updates.20121128.2145.bz2')
# filename = 'updates.20121202.0000.bz2'
# ASN is the list of ASNs we are interested in collecting update and withdraw
# messages on
asns = ['2497']

#bgpdump.updateFiles = [filename1, filename2]
bgpdump.updateFiles = [filename]
for x in bgpdump.getYAMLUpdates(asns):
    print x

