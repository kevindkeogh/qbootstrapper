#!/usr/bin/env python
# vim: set fileencoding=utf-8
"""
Copyright (c) Kevin Keogh 2016-2020

Implements the Instruments ojects that are used by the Curve objects to hold
attributes of market data and return discount factors.

Note that cash and forward instruments calculate discount factors analytically,
discount factors for swaps are calculated using a root-finding algorithm.
"""
# python libraries
from __future__ import division
import datetime
import dateutil.relativedelta
import numpy as np
import sys

if sys.version_info > (3,):
    long = int


class Instrument(object):
    """Base Instrument convenience class
    Class is primarily used for the date adjustment methods that are used
    by the sub-classes.
    """

    def __init__(self):
        pass

    def _date_adjust(self, date, adjustment):
        """Method to return a date that is adjusted according to the
        adjustment convention method defined

        Arguments:
            date (datetime)     : Date to be adjusted
            adjustment (str)    : Adjustment type
                                  available: unadjusted,
                                             following,
                                             preceding,
                                             modified following
        """
        if adjustment == "unadjusted":
            return date
        elif adjustment == "following":
            if date.weekday() < 5:
                return date
            else:
                return date + self._timedelta(7 - date.weekday(), "days")
        elif adjustment == "preceding":
            if date.weekday() < 5:
                return date
            else:
                return date - self._timedelta(max(0, date.weekday() - 5), "days")
        elif adjustment == "modified following":
            if date.month == self._date_adjust(date, "following").month:
                return self._date_adjust(date, "following")
            else:
                return date - self._timedelta(7 - date.weekday(), "days")
        else:
            raise Exception(
                'Adjustment period "{adjustment}" ' "not recognized".format(**locals())
            )

    @staticmethod
    def _timedelta(length_num, length_type):
        """Static method to return the date +/- some length with a length type

        Arguments:
            length_num (int)    : Length of the period (e.g., if the period
                                  is 6 months, this is 6)
            length_type (str)   : Period type (e.g., if the period is 6 months,
                                  this is months)
                                  available: months,
                                             weeks,
                                             days
        """
        if length_type.lower() in ["years", "year", "y", "yr"]:
            return dateutil.relativedelta.relativedelta(years=length_num)
        elif length_type.lower() in ["months", "month", "m", "mo"]:
            return dateutil.relativedelta.relativedelta(months=length_num)
        elif length_type.lower() in ["weeks", "week", "w", "wk"]:
            return dateutil.relativedelta.relativedelta(weeks=length_num)
        elif length_type.lower() in ["days", "day", "d"]:
            return dateutil.relativedelta.relativedelta(days=length_num)
        else:
            raise Exception(
                'Period length "{length_type}" ' "not recognized".format(**locals())
            )

    @staticmethod
    def daycount(effective, maturity, basis):
        """Static method to return the accrual length, as a decimal,
        between an effective and a maturity subject to a basis convention

        Arguments:
            effective (datetime)    : First day of the accrual period
            maturity (datetime)     : Last day of the accrual period
            basis (str)             : Basis convention
                                      available: Act360,
                                                 Act365,
                                                 30360,
                                                 30E360

        """
        if type(effective) == np.datetime64:
            timestamp = effective.astype("<M8[s]").astype(np.uint64)
            effective = datetime.datetime.fromtimestamp(timestamp)
            timestamp = maturity.astype("<M8[s]").astype(np.uint64)
            maturity = datetime.datetime.fromtimestamp(timestamp)
        if basis.lower() == "act360":
            accrual_period = (maturity - effective).days / 360
        elif basis.lower() == "act365":
            accrual_period = (maturity - effective).days / 365
        elif basis.lower() == "30360":
            start, end = min(effective.day, 30), min(maturity.day, 30)
            months = 30 * (maturity.month - effective.month) + 360 * (
                maturity.year - effective.year
            )
            accrual_period = (end - start + months) / 360
        elif basis.lower() == "30e360":
            start, end = max(0, 30 - effective.day), min(30, maturity.day)
            months = 30 * (maturity.month - effective.month - 1)
            years = 360 * (maturity.year - effective.year)
            accrual_period = (years + months + start + end) / 360
        else:
            raise Exception(
                'Accrual basis "{basis}" ' "not recognized".format(**locals())
            )
        return accrual_period
