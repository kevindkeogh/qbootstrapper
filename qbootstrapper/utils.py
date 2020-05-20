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
import datetime
import dateutil
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
        name (string)               : The named tenor, supports ON, D, W{,K},
                                      M{,O}, and Y{,R}
    """

    def __init__(self, name=None, *args):
        if name is None:
            raise ValueError("Tenor cannot be blank")
        self.name = name

    def __radd__(self, other):
        if self.name == "ON":
            kind = "ON"
        else:
            num = int(re.findall(r"(-?\d+)", self.name)[0])
            kind = re.findall(r"([a-zA-Z]+)", self.name)[0]

        if kind[0] == "Y":
            return other + dateutil.relativedelta.relativedelta(years=num)
        elif kind[0] == "M":
            return other + dateutil.relativedelta.relativedelta(months=num)
        elif kind[0] == "W":
            return other + dateutil.relativedelta.relativedelta(weeks=num)
        elif kind[0] == "D":
            return other + dateutil.relativedelta.relativedelta(days=num)
        elif kind == "ON":
            return other + dateutil.relativedelta.relativedelta(days=1)
        else:
            raise ValueError(f"Period: {kind} not recognized")

    def __rsub__(self, other):
        if self.name == "ON":
            return ValueError("Period: ON is cannot be subtracted")
        else:
            num = int(re.findall(r"(-?\d+)", self.name)[0])
            kind = re.findall(r"([a-zA-Z]+)", self.name)[0]

        if kind[0] == "Y":
            return other - dateutil.relativedelta.relativedelta(years=num)
        elif kind[0] == "M":
            return other - dateutil.relativedelta.relativedelta(months=num)
        elif kind[0] == "W":
            return other - dateutil.relativedelta.relativedelta(weeks=num)
        elif kind[0] == "D":
            return other - dateutil.relativedelta.relativedelta(days=num)
        else:
            raise ValueError(f"Period: {kind} not recognized")


class Calendar(object):
    """Calendar class
    Class that holds a list of holidays and weekends that can be used to
    advance and reverse dates. Also includes methods to adjust for business
    day conventions.

    Arguments:
        names (string)              : A variable number of strings representing
                                      holiday centers. These can be found in
                                      the calendars folder. Note that the
                                      'weekends' calendar is also supported,
                                      but is a no-op.
        weekends (list of ints)     : A list representing the weekdays that
                                      should be considered weekends. Monday is
                                      0, Sunday is 6.
                                      [default: [5, 6]]

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

    def __init__(self, *args, weekends=[5, 6]):
        self.holidays = set()
        self.weekends = weekends
        self.name = ""

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
                dt = datetime.datetime.strptime(row.strip(), "%Y-%m-%d")
                self.holidays.add(dt)

    def advance(self, now, tenor, convention="following"):
        next_date = now + tenor
        return self.adjust(next_date, convention)

    def reverse(self, now, tenor, convention="following"):
        prev_date = now - tenor
        return self.adjust(prev_date, convention)

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
                                        modified following
        """
        if convention == "unadjusted":
            return date

        if not self.is_holiday(date) and not self.is_weekend(date):
            return date

        if convention == "following":
            return self.advance(date, Tenor("1D"), convention)
        elif convention == "modified following":
            if self.advance(date, Tenor("1D")).month != date.month:
                return self.reverse(date, Tenor("1D"), "preceding")
            else:
                return self.advance(date, Tenor("1D"), "following")
        elif convention == "preceding":
            return self.reverse(date, Tenor("1D"), convention)
        else:
            raise ValueError(f"Convention: {convention} not recognized")

    def is_holiday(self, date):
        return date in self.holidays

    def is_weekend(self, date):
        return date.weekday() in self.weekends


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
        return third.replace(day=(15 + (4 - third.weekday()) % 7))
