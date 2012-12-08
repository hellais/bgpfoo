
# http://archive.routeviews.org/bgpdata/2012.11/UPDATES/updates.20121101.0130.bz2
# http://bgplay.routeviews.org/

import os
import itertools
from datetime import datetime, timedelta

from urllib2 import urlopen, URLError, HTTPError


class InvalidNumber(Exception):
    pass

def twoLetterNumber(number):
    """
    Takes a number and converts it to two letters. For example int(1) becomes
    str(01), int(11) becomes str(11).
    """
    s = str(number)
    if len(s) == 2:
        return s
    elif len(s) == 1:
        return '0'+s
    else:
        raise InvalidNumber

def datesInRange(start_date, end_date, slot_size=15):
    """
    Args:
        start_date (datetime): The start date

        end_date (datetime): The end date

        slot_size (int): The expressed in minutes time slot for splitting dates.
    """
    delta = end_date - start_date
    # The number of slots in a day is the number of hours * 60 / slot_size
    slots = delta.days * 24 * (60 / slot_size)
    # We need to also add the seconds delta and this is seconds difference /
    # seconds in an hour * the slot size
    slots += delta.seconds / (60 * slot_size)
    for slot in range(slots + 1):
        seconds = slot * 15 * 60
        yield start_date + timedelta(seconds=seconds)

class RouteViewsArchive(object):
    baseUrl = "http://archive.routeviews.org/bgpdata/"
    formatString = "%(year)s.%(month)s/UPDATES/updates.%(year)s%(month)s%(day)s.%(hour)s%(minute)s.bz2"

    # we need to discard the seconds and minutes
    _x = datetime.now()
    _current_date = _x.replace(second=0, minute=0)

    # **note** it is important that you do not set the seconds and minutes on
    # the timedate objects
    # We set the start_date by default to 7 days
    startDate = _current_date - timedelta(days=2)
    endDate = _current_date

    def _updatesInRange(self):
        for d in datesInRange(self.startDate, self.endDate):
            vals = {'year': d.year,
                    'month': twoLetterNumber(d.month),
                    'day': twoLetterNumber(d.day),
                    'hour': twoLetterNumber(d.hour),
                    'minute': twoLetterNumber(d.minute)
            }
            yield  self.formatString % vals

    def _downloadFile(self, url):
        try:
            f = urlopen(url)
            print "downloading " + url

            with open(os.path.basename(url), "wb") as local_file:
                local_file.write(f.read())

        except HTTPError, e:
            print "HTTP Error:", e.code, url
        except URLError, e:
            print "URL Error:", e.reason, url

    def downloadUpdates(self):
        for filename in self._updatesInRange():
            url = self.baseUrl + filename
            self._downloadFile(url)


rva = RouteViewsArchive()
rva.startDate = datetime(2012, 12, 2)
rva.endDate = datetime(2012, 12, 3)
# This will download the updates in the specified time period to the current
# working directory.
# XXX add possibility to configure where it should output the files to
rva.downloadUpdates()

