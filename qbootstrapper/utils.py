#!/usr/bin/env python
# vim: set fileencoding=utf-8
"""
Copyright (c) Kevin Keogh 2016

Implements the Instruments ojects that are used by the Curve objects to hold
attributes of market data and return discount factors.

Note that cash and forward instruments calculate discount factors analytically,
discount factors for swaps are calculated using a root-finding algorithm.
"""

from __future__ import division
import datetime
import sys

if sys.version_info > (3,):
    long = int


def imm_date(imm_code):
    """Return the applicable date of an IMM code given the form F19"""
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
