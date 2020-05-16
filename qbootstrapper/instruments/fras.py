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
import numpy as np
import re
import sys

# qlib libraries
from qbootstrapper.instruments import Instrument

if sys.version_info > (3,):
    long = int


class FRAInstrumentByDates(Instrument):
    """FRA instrument class for use with the Swap Curve bootstrapper.

    This class can be utilized to hold the market data and conventions
    for a single FRA contract, which is later utilized
    The forward rate is calculated as the

                      DF[effective]
                      -------------
          1 + (r * accrual_days / days_in_year)

    Arguments:
        effective (datetime)    : First day of the accrual period of the FRA
        maturity (datetime)     : Last day of the accrual period of the FRA
        rate (float)            : Fixing rate of the FRA
        curve (Curve)           : Curve being built, necessary for callbacks
                                  to the curve for discount factors

        kwargs
        ------
        basis (str)             : Accrual basis for the period
                                  [default: Act360]

    TODO: Add FRAInstrumentByTenor
    """

    def __init__(self, effective, maturity, rate, curve, basis="Act360"):
        # assignments
        self.effective = effective
        self.maturity = maturity
        self.rate = rate
        self.basis = basis
        self.curve = curve
        self.accrual_period = super(FRAInstrumentByDates, self).daycount(
            self.effective, self.maturity, self.basis
        )
        self.instrument_type = "FRA"

    def discount_factor(self):
        """Method for returning the discount factor for a FRA
        """
        numerator = self.curve.discount_factor(self.effective)
        denominator = 1 + (self.rate * self.accrual_period)
        discount_factor = numerator / denominator
        return np.log(discount_factor)


class FRAInstrumentByDateAndTenor(Instrument):
    """FRA instrument class for use with the Swap Curve bootstrapper.

    This class can be utilized to hold the market data and conventions
    for a single FRA contract, which is later utilized
    The forward rate is calculated as the

                      DF[effective]
                      -------------
          1 + (r * accrual_days / days_in_year)

    Arguments:
        effective (datetime)    : First day of the accrual period of the FRA
        tenor (datetime)     : Last day of the accrual period of the FRA
        rate (float)            : Fixing rate of the FRA
        curve (Curve)           : Curve being built, necessary for callbacks
                                  to the curve for discount factors

        kwargs
        ------
        basis (str)             : Accrual basis for the period
                                  [default: Act360]

    TODO: Add FRAInstrumentByTenor
    """

    def __init__(self, effective, tenor, rate, curve, basis="act360"):
        # assignments
        self.effective = effective
        self.tenor = tenor
        self.rate = rate
        self.basis = basis
        self.curve = curve

        length_num = re.findall("\d+", self.tenor)[0]
        length_type = re.findall("[A-Za-z]")[0]
        self.maturity = effective + super(FRAInstrumentByDateAndTenor, self)._timedelta(
            length_num, length_type
        )
        self.accrual_period = super(FRAInstrumentByDateAndTenor, self).daycount(
            self.effective, self.maturity, self.basis
        )
        self.instrument_type = "fra"

    def discount_factor(self):
        """Method for returning the discount factor for a FRA
        """
        numerator = self.curve.discount_factor(self.effective)
        denominator = 1 + (self.rate * self.accrual_period)
        discount_factor = numerator / denominator
        return np.log(discount_factor)
