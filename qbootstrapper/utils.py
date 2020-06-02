#!/usr/bin/env python
# vim: set fileencoding=utf-8
"""
Copyright (c) Kevin Keogh 2016-2020

Implements the Instruments ojects that are used by the Curve objects to hold
attributes of market data and return discount factors.

Note that cash and forward instruments calculate discount factors analytically,
discount factors for swaps are calculated using a root-finding algorithm.
"""

from __future__ import division
import collections.abc
import datetime
import dateutil
import numpy as np
import re
import os
import pkg_resources
import sys


if sys.version_info > (3,):
    long = int


class Tenor(object):
    """Tenor class
    Class that interprets a string such as "6M" or "10Y" and holds the
    timedelta for use in calculating dates. The class uses dunder (__...)
    methods to allow for easy adding and subtracting from dates. Note
    that only right-{add,subtract} are supported (i.e., date + tenor),
    left-{add,subtract} are not supported, as they don't have an obvious
    meaning (tenor - date?)

    Arguments:
        name (string)               : The named tenor, supports ON, D, BD,
                                      W{,K}, M{,O}, and Y{,R}
    """

    def __init__(self, name=None, *args):
        if name is None:
            raise ValueError("Tenor cannot be blank")
        self.name = name

        if self.name == "ON":
            self.num = 1
            self.kind = "ON"
        else:
            self.num = int(re.findall(r"(-?\d+)", self.name)[0])
            self.kind = re.findall(r"([a-zA-Z]+)", self.name)[0]

    def __radd__(self, other):
        if self.kind[0] == "Y":
            return other + dateutil.relativedelta.relativedelta(years=self.num)
        elif self.kind[0] == "M":
            return other + dateutil.relativedelta.relativedelta(months=self.num)
        elif self.kind[0] == "W":
            return other + dateutil.relativedelta.relativedelta(weeks=self.num)
        elif self.kind[0] == "D":
            return other + dateutil.relativedelta.relativedelta(days=self.num)
        elif self.kind == "ON":
            return other + dateutil.relativedelta.relativedelta(days=1)
        else:
            raise ValueError(f"Period: {self.kind} not recognized")

    def __rsub__(self, other):
        if self.kind[0] == "Y":
            return other - dateutil.relativedelta.relativedelta(years=self.num)
        elif self.kind[0] == "M":
            return other - dateutil.relativedelta.relativedelta(months=self.num)
        elif self.kind[0] == "W":
            return other - dateutil.relativedelta.relativedelta(weeks=self.num)
        elif self.kind[0] == "D":
            return other - dateutil.relativedelta.relativedelta(days=self.num)
        elif self.kind[0] == "ON":
            raise ValueError(f"Period: ON not supported for subtraction")
        else:
            raise ValueError(f"Period: {self.kind} not recognized")


class Calendar(object):
    """Calendar class
    Class that holds a list of holidays and weekends that can be used to
    advance and reverse dates. Also includes methods to adjust for business
    day conventions.

    Arguments:
        names (str)                 : A variable number of strings representing
                                      holiday centers. These can be found in
                                      the calendars folder. Note that the
                                      'weekends' calendar is also supported,
                                      but is a no-op.
        weekends (str)              : A string representing which days should
                                      be considered weekdyas. A weekday is 1,
                                      a weekend is 0, week starts on Monday.
                                      [default: 1111100]

    Methods:
        advance (                   : A method to advance, using the applicable
                 now: datetime,       holiday center, the date by a given tenor
                 tenor: Tenor,          convention is defaulted to following
                 convention: str
                 )
        reverse (                   : A method to reverse, using the applicable
                 now: datetime,       holiday center, the date by a given tenor
                 tenor: Tenor,          convention is defaulted to following
                 convention: str
                 )
        adjust (                    : A method to adjust a date given a
                 date: datetime,      business day convention
                 convention: str        Supported conventions are:
                 )                          unadjusted,
                                            following
                                            preceding
                                            modified following

    """

    def __init__(self, *args, weekends="1111100"):
        self.weekends = weekends
        self.name = ""
        self.holidays = []
        self.cal = np.busdaycalendar(self.weekends, self.holidays)

        for idx, arg in enumerate(args):
            if arg.lower() == "weekends":
                continue

            if self.name == "":
                self.name = str(arg)
            else:
                self.name += " " + str(arg)

            self._read_file(arg)

    def _read_file(self, cal):
        try:
            filename = os.path.join("calendars", cal.upper() + ".txt")
            filepath = pkg_resources.resource_filename(__name__, filename)
        except Exception as e:
            return ValueError(f"Could not find calendar {cal} in sources: {e}")

        with open(filepath, "r") as fh:
            for row in fh:
                self.holidays.append(row.strip())

        self.cal = np.busdaycalendar(self.weekends, self.holidays)

    def advance(self, now, tenor, convention="following"):
        if tenor.kind[0] == "B":
            dt = np.datetime64(now).astype("<M8[D]")
            dt = np.busday_offset(dt, tenor.num, roll=convention, busdaycal=self.cal)
            return datetime.datetime.fromordinal(dt.astype(object).toordinal())
        else:
            next_date = now + tenor
            return self.adjust(next_date, convention)

    def reverse(self, now, tenor, convention="following"):
        if tenor.kind[0] == "B":
            dt = np.datetime64(now).astype("<M8[D]")
            dt = np.busday_offset(dt, tenor.num, roll=convention, busdaycal=self.cal)
            return datetime.datetime.fromordinal(dt.astype(object).toordinal())
        else:
            next_date = now - tenor
            return self.adjust(next_date, convention)

    def adjust(self, date, convention):
        """Method to return a date that is adjusted according to the supplied
        business day convention

        Arguments:
            date (datetime)     : date to be adjusted
            adjustment (str)    : Adjustment type
                                    available:
                                        unadjusted
                                        following
                                        preceding
                                        modifiedfollowing
        """
        if convention == "unadjusted":
            return date

        dt = np.datetime64(date).astype("<M8[D]")
        if self.is_busday(dt):
            return date

        return datetime.datetime.fromordinal(
            np.busday_offset(dt, 0, roll=convention, busdaycal=self.cal)
            .astype(object)
            .toordinal()
        )

    def is_holiday(self, date):
        dt = np.datetime64(date)
        return np.is_busday(dt, busdaycal=np.busdaycalendar("1111111", self.holidays))

    def is_weekend(self, date):
        dt = np.datetime64(date)
        return np.is_busday(dt)

    def is_busday(self, date):
        dt = np.datetime64(date)
        return np.is_busday(dt, busdaycal=self.cal)


class Fixings:
    """Fixings class to hold and provide historical index fixings.

    Arguments:
        name (str)                  : Name of the index

        kwargs (optional)
        -----------------
        fixings (iterable)          : Iterable of pairs of datetimes and fixing
                                      amounts
        scale (float)               : Specify the scale of the fixings
    """

    def __init__(self, name, fixings=None, scale=1):
        self.name = name
        self.fixings = {}
        self.scale = scale

        if fixings is not None:
            self.add_fixings(fixings)

    def add_fixings(self, fixings, scale=None):
        """Add fixings to the Fixings object
        Arguments:
            fixings (iterable)          : Iterable of pairs of datetimes and
                                          fixing amounts
            scale (float)               : Specify the scale of the fixings
        """
        if scale is None:
            scale = self.scale
        for fixing in fixings:
            if type(fixing[0]) != np.datetime64:
                try:
                    date = np.datetime64(fixing[0]).astype("<M8[s]")
                except Exception:
                    raise Exception("Dates must be np.datetime64")

            self.fixings[date] = float(fixing[1]) / scale

    def get(self, dates):
        """Get fixings for a date or iterable of dates
        """
        if isinstance(dates, collections.abc.Iterable):
            return [self.fixings[date] for date in dates]
        else:
            try:
                return [self.fixings[dates]]
            except KeyError:
                one_day = np.timedelta64(1, "D")
                return self.get(dates - one_day)


def imm_date(imm_code):
    """Return the applicable date of an IMM code given the form Z20"""
    letter = imm_code[0]
    year = 2000 + int(imm_code[1:])

    codes = {
        "F": 1,
        "G": 2,
        "H": 3,
        "J": 4,
        "K": 5,
        "M": 6,
        "N": 7,
        "Q": 8,
        "U": 9,
        "V": 10,
        "X": 11,
        "Z": 12,
    }

    third = datetime.datetime(year, codes[letter], 15)
    if third.weekday() == 2:
        return third
    else:
        return third.replace(day=(15 + (2 - third.weekday()) % 7))
