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
        term_length (int)       : Length of the instrument period
        curve (Curve)           : Curve being built, necessary for callbacks
                                  to the curve for discount factors

        kwargs
        ------
        basis (str)             : Accrual basis for the period
                                  [default: Act360]
        length_type             : Length of the term_length in units
                                  [default: months]
        payment_adjustment (str): Adjustment to the payment date from the
                                  end of the accrual period
                                  [default: unadjusted]

    """

    def __init__(
        self,
        effective,
        rate,
        term_length,
        curve,
        basis="act360",
        length_type="months",
        payment_adjustment="unadjusted",
    ):
        # assignments
        self.effective = effective
        self.rate = rate
        self.term_length = term_length
        self.basis = basis
        self.length_type = length_type
        self.payment_adjustment = payment_adjustment
        self.instrument_type = "cash"

        # calculations
        self._date_calculations()
        self.accrual_period = super(LIBORInstrument, self).daycount(
            self.effective, self.maturity, self.basis
        )

    def _date_calculations(self):
        """Method for setting the accrual period and dates for a Cash
        instrument
        """
        self._term = super(LIBORInstrument, self)._timedelta(
            self.term_length, self.length_type
        )
        self.maturity = self.effective + self._term
        self.payment_date = super(LIBORInstrument, self)._date_adjust(
            self.maturity, self.payment_adjustment
        )

    def discount_factor(self):
        """Method for returning the discount factor for a Cash rate
        """
        return np.log(1 / (1 + (self.rate * self.accrual_period)))
