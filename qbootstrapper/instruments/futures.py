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
import sys

# qlib libraries
from qbootstrapper.instruments import Instrument
from qbootstrapper.utils import imm_date, Tenor

if sys.version_info > (3,):
    long = int


class FuturesInstrumentByDates(Instrument):
    """Futures instrument class for use with Swap Curve bootstrapper.

    This class can be utilized to hold the market data and conventions
    for a single Futures contract, which is later utilized in when the
    .build() method is called on the curve where this instrument
    has been added.

    The future rate is calculated as the

                         DF[effective]
                         -------------
    1 + ((100 - price) / 100 * accrual_days / days_in_year)

    Arguments:
        effective (datetime)    : First day of the accrual period of the future
        maturity (datetime)     : Last day of the accrual period of the future
        price (float)           : Price of the future (assumes expiry price
                                  of the future is 100)
        curve (Curve)           : Curve being built, necessary for callbacks
                                  to the curve for discount factors

        kwargs
        ------
        basis (str)             : Accrual basis for the period
                                  [default: act360]

    TODO: Add FuturesInstrumentByTicker
    TODO: Add Futures convexity calculation
    """

    def __init__(self, effective, maturity, price, curve, basis="act360"):
        # assignments
        self.effective = effective
        self.maturity = maturity
        self.price = price
        self.rate = (100 - price) / 100
        self.basis = basis
        self.curve = curve
        self.accrual_period = super(FuturesInstrumentByDates, self).daycount(
            self.effective, self.maturity, self.basis
        )
        self.instrument_type = "Futures"

    def discount_factor(self):
        """Method for returning the discount factor for a future
        """
        discount_factor = self.curve.discount_factor(self.effective) / (
            1 + (self.rate * self.accrual_period)
        )
        return np.log(discount_factor)


class FuturesInstrumentByIMMCode(FuturesInstrumentByDates):
    """Futures instrument class for use with Swap Curve bootstrapper.

    This class can be utilized to hold the market data and conventions
    for a single Futures contract, which is later utilized in when the
    .build() method is called on the curve where this instrument
    has been added.

    The future rate is calculated as the

                         DF[effective]
                         -------------
    1 + ((100 - price) / 100 * accrual_days / days_in_year)

    Arguments:
        code (string)           : IMM Code of the future (e.g., H20)
        price (float)           : Price of the future (assumes expiry price
                                  of the future is 100)
        curve (Curve)           : Curve being built, necessary for callbacks
                                  to the curve for discount factors

        kwargs
        ------
        basis (str)             : Accrual basis for the period
                                  [default: act360]

    TODO: Add Futures convexity calculation
    """

    def __init__(self, code, price, curve, basis="act360", tenor=Tenor("3M")):
        # assignments
        self.code = code
        self.price = price
        self.rate = (100 - price) / 100
        self.basis = basis
        self.curve = curve

        self.effective = imm_date(code)
        self.maturity = self.effective + tenor
        self.accrual_period = super(FuturesInstrumentByIMMCode, self).daycount(
            self.effective, self.maturity, self.basis
        )
        self.instrument_type = "futures"
