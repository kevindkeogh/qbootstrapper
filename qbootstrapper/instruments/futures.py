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
import scipy
import sys
import time

# qlib libraries
from qbootstrapper.instruments import Instrument
from qbootstrapper.utils import imm_date, Tenor, Calendar

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
        calendar (Calendar)     : Calendar used for payment date adjustment
                                  [default: weekends]

    TODO: Add Futures convexity calculation
    """

    def __init__(
        self, effective, maturity, price, curve, basis="act360", calendar=None
    ):
        # assignments
        self.effective = effective
        self.maturity = maturity
        self.price = price
        self.rate = (100 - price) / 100
        self.curve = curve
        self.basis = basis
        self.calendar = calendar if calendar is not None else Calendar("weekends")
        self.accrual_period = super(FuturesInstrumentByDates, self).daycount(
            self.effective, self.maturity, self.basis
        )
        self.instrument_type = "futures"

    def discount_factor(self):
        """Method for returning the discount factor for a future
        """
        df = self.curve.discount_factor(self.effective) / (
            1 + (self.rate * self.accrual_period)
        )

        return np.log(df)


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
        tenor (Tenor)           : Tenor of the the future
                                  [default: 3M]
        calendar (Calendar)     : Calendar used for payment date adjustment
                                  [default: weekends]


    TODO: Add Futures convexity calculation
    """

    def __init__(self, code, price, curve, basis="act360", calendar=None, tenor=None):
        # assignments
        self.code = code
        self.price = price
        self.rate = (100 - price) / 100
        self.curve = curve
        self.basis = basis
        self.tenor = tenor if tenor is not None else Tenor("3M")
        self.calendar = calendar if calendar is not None else Calendar("weekends")

        self.effective = imm_date(code)
        self.maturity = self.calendar.adjust(self.effective + self.tenor, "following")
        self.accrual_period = super(FuturesInstrumentByIMMCode, self).daycount(
            self.effective, self.maturity, self.basis
        )
        self.instrument_type = "futures"


class CompoundFuturesInstrumentByIMMCode(FuturesInstrumentByIMMCode):
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
        tenor (Tenor)           : Tenor of the the future
                                  [default: 3M]
        calendar (Calendar)     : Calendar used for payment date adjustment
                                  [default: weekends]
        contract_size (float)   : Notional used for calculating cashflows
                                  [default: 100]


    TODO: Add Futures convexity calculation
    """

    def __init__(
        self,
        code,
        price,
        curve,
        basis="act360",
        calendar=None,
        tenor=None,
        contract_size=100,
    ):
        # assignments
        self.code = code
        self.price = price
        self.rate = (100 - price) / 100
        self.curve = curve
        self.basis = basis
        self.tenor = tenor if tenor is not None else Tenor("3M")
        self.calendar = calendar if calendar is not None else Calendar("weekends")
        self.contract_size = contract_size

        self.effective = imm_date(code)
        self.maturity = self.calendar.adjust(self.effective + self.tenor, "following")
        self.accrual_period = super(FuturesInstrumentByIMMCode, self).daycount(
            self.effective, self.maturity, self.basis
        )
        self.instrument_type = "futures"

    def discount_factor(self):
        """Returns the discount factor for the futures using Newton's method
        root finder.
        """
        return scipy.optimize.newton(self._futures_value, 0)

    def _futures_value(self, guess, args=()):
        """
        """
        if not isinstance(guess, (int, float, long, complex)):
            # simultaneous bootstrapping sets the guess[0] as the ois guess
            guess = guess[0]

        temp_curve = self.curve.curve
        temp_curve = np.append(
            self.curve.curve,
            np.array(
                [
                    (
                        np.datetime64(self.maturity.strftime("%Y-%m-%d")),
                        time.mktime(self.maturity.timetuple()),
                        guess,
                    )
                ],
                dtype=self.curve.curve.dtype,
            ),
        )

        interpolator = scipy.interpolate.PchipInterpolator(
            temp_curve["timestamp"], temp_curve["discount_factor"]
        )

        # SOFR Leg
        df = np.exp(interpolator(np.datetime64(self.maturity).astype("<M8[s]")))
        sofr_forward_rate = self.__forward_rate(interpolator)
        sofr_pv = sofr_forward_rate * self.contract_size * df

        futures_pv = self.rate * self.contract_size * self.accrual_period * df

        return sofr_pv - futures_pv

    def __forward_rate(self, interpolator):
        """
        """
        start_date = np.datetime64(self.effective).astype("<M8[s]")
        end_date = np.datetime64(self.maturity).astype("<M8[s]")
        one_day = np.timedelta64(1, "D")
        start_day = start_date.astype(object).weekday()
        first_dates = np.arange(start_date, end_date, one_day)
        fridays = first_dates[4 - start_day :: 7]
        first_dates[5 - start_day :: 7] = fridays[
            : len(first_dates[5 - start_day :: 7])
        ]
        first_dates[6 - start_day :: 7] = fridays[
            : len(first_dates[6 - start_day :: 7])
        ]
        second_dates = first_dates + one_day
        initial_dfs = np.exp(interpolator(first_dates))
        end_dfs = np.exp(interpolator(second_dates))
        rates = initial_dfs / end_dfs
        rate = rates.prod() - 1
        return rate
