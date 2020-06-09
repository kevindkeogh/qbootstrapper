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
from qbootstrapper.utils import Calendar, Tenor

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
                                  [default: act360]
        calendar (Calendar)     : Calendar used for payment date adjustment
                                  [default: weekends]
        payment_adjustment (str): Payment date adjustment convention
                                  [default: following]
        name (string)           : Name of the instrument
                                  [default: 'FRA-{effective}-{maturity}']
    """

    def __init__(
        self,
        effective,
        maturity,
        rate,
        curve,
        basis="act360",
        calendar=None,
        payment_adjustment="following",
        spot_lag=None,
        name=None,
    ):
        # assignments
        self.calendar = calendar if calendar is not None else Calendar("weekends")
        self.spot_lag = spot_lag if spot_lag is not None else Tenor("0D")
        self.effective = self.calendar.advance(effective, self.spot_lag)
        self.maturity = maturity
        self.rate = rate
        self.basis = basis
        self.curve = curve
        self.accrual_period = super(FRAInstrumentByDates, self).daycount(
            self.effective, self.maturity, self.basis
        )
        self.payment_adjustment = payment_adjustment
        if name:
            self.name = name
        else:
            self.name = (
                "FRA-"
                + self.effective.strftime("%Y-%-m-%d")
                + "-"
                + self.maturity.strftime("%Y-%m-%d")
            )

        self.payment = calendar.adjust(self.maturity, self.payment_adjustment)

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
        tenor (Tenor)           : Tenor of the FRA
        rate (float)            : Fixing rate of the FRA
        curve (Curve)           : Curve being built, necessary for callbacks
                                  to the curve for discount factors

        kwargs
        ------
        basis (str)             : Accrual basis for the period
                                  [default: act360]
        calendar (Calendar)     : Calendar used for payment date adjustment
                                  [default: weekends]
        payment_adjustment (str): Payment date adjustment convention
                                  [default: following]
        name (string)           : Name of the instrument
                                  [default: 'FRA-{effective}-{maturity}']
    """

    def __init__(
        self,
        effective,
        tenor,
        rate,
        curve,
        basis="act360",
        calendar=Calendar("weekends"),
        payment_adjustment="following",
        spot_lag=None,
        name=None,
    ):
        # assignments
        self.calendar = calendar if calendar is not None else Calendar("weekends")
        self.spot_lag = spot_lag if spot_lag is not None else Tenor("0D")
        self.effective = self.calendar.advance(effective, self.spot_lag)
        self.maturity = effective + tenor
        self.tenor = tenor
        self.rate = rate
        self.basis = basis
        self.curve = curve
        self.calendar = calendar if calendar is not None else Calendar("weekends")
        self.payment_adjustment = payment_adjustment

        self.accrual_period = super(FRAInstrumentByDateAndTenor, self).daycount(
            self.effective, self.maturity, self.basis
        )

        self.payment = calendar.adjust(self.maturity, self.payment_adjustment)
        if name:
            self.name = name
        else:
            self.name = (
                "FRA-"
                + self.effective.strftime("%Y-%-m-%d")
                + "-"
                + self.maturity.strftime("%Y-%m-%d")
            )

    def discount_factor(self):
        """Method for returning the discount factor for a FRA
        """
        numerator = self.curve.discount_factor(self.effective)
        denominator = 1 + (self.rate * self.accrual_period)
        discount_factor = numerator / denominator
        return np.log(discount_factor)
