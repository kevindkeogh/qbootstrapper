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


class LIBORInstrument(Instrument):
    """LIBOR cash instrument class for use with the Swap Curve bootstrapper.

    This class can be utilized to hold the market data and conventions
    for a single cash LIBOR-equivalent contract, which is later utilized
    The forward rate is calculated as the

                            1
                      -------------
          1 + (r * accrual_days / days_in_year)

    Arguments:
        effective (datetime)    : Effective date of the LIBOR-equivalent
                                  cash instrument
        rate (float)            : Interest rate of the instrument
        tenor (Tenor)           : Tenor of the instrument
        curve (Curve)           : Curve being built, necessary for callbacks
                                  to the curve for discount factors

        kwargs
        ------
        basis (str)             : Accrual basis for the period
                                  [default: act360]
        payment_adjustment (str): Adjustment to the payment date from the
                                  end of the accrual period
                                  [default: unadjusted]
        calendar (Calendar)     : Calendar used for holiday adjustments
                                  [default: weekends]
        fixing_lag (Tenor)      : Fixing lag between rate setting and first
                                  accrual date
                                  [default: 0D]
    """

    def __init__(
        self,
        effective,
        rate,
        tenor,
        curve,
        basis="act360",
        payment_adjustment="unadjusted",
        calendar=None,
        spot_lag=None,
    ):
        # assignments
        self.spot_lag = spot_lag if spot_lag is not None else Tenor("0D")
        self.calendar = calendar if calendar is not None else Calendar("weekends")
        self.effective = self.calendar.advance(effective, self.spot_lag)
        self.rate = rate
        self.tenor = tenor
        self.curve = curve
        self.basis = basis
        self.payment_adjustment = payment_adjustment
        self.instrument_type = "cash"
        print(self.effective)

        # calculations
        self._date_calculations()
        self.accrual_period = super(LIBORInstrument, self).daycount(
            self.curve.date, self.maturity, self.basis
        )

    def _date_calculations(self):
        """Method for setting the accrual period and dates for a Cash
        instrument
        """
        if type(self.tenor) == Tenor:
            self.maturity = self.calendar.advance(
                self.effective, self.tenor, self.payment_adjustment
            )
        else:
            self.maturity = self.tenor

        self.payment_date = self.calendar.adjust(self.maturity, self.payment_adjustment)

    def discount_factor(self):
        """Method for returning the discount factor for a Cash rate
        """
        return np.log(1 / (1 + (self.rate * self.accrual_period)))
