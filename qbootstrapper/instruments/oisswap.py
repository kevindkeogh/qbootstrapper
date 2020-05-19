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
import scipy.interpolate
import scipy.optimize
import sys
import time

# qlib libraries
from qbootstrapper.instruments import SwapInstrument


if sys.version_info > (3,):
    long = int


class OISSwapInstrument(SwapInstrument):
    """OIS swap instrument class for use with Swap Curve bootstrapper.

    This class can be utilized to hold the market data and conventions
    for a single swap, which is later utilized in when the .build()
    method is called on the curve where this instrument has been added.

    Arguments:
        effective (datetime)                : First accrual start date of
                                              the swap
        maturity (datetime)                 : Last accrual end date of
                                              the swap
        rate (float)                        : Fixed rate
        curve (Curve object)                : Associated curve object.
                                              There are callbacks to the
                                              curve for prior discount
                                              factors, so it must be
                                              assigned

        kwargs (optional)
        -----------------
        fixed_basis (string)                : Accrual basis of the fixed
                                              leg. See daycount method of
                                              base Instrument class for
                                              implemented conventions
                                              [default: '30360']
        float_basis (string)                : Accrual basis of the floating
                                              leg. See daycount method of
                                              base Instrument class for
                                              implemented conventions
                                              [default: 'act360']
        fixed_tenor (Tenor)                 : Length of the fixed accrual
                                              period
                                              [default: 6M]
        float_tenor (Tenor)                 : Length of the floating accrual
                                              period
                                              [default: 6M]
        fixed_period_adjustment (string)    : Adjustment type for fixed
                                              accrual periods. See the
                                              _date_adjust method of the base
                                              Instrument class for implemented
                                              conventions
                                              [default: 'unadjusted']
        float_period_adjustment (string)    : Adjustment type for floating
                                              accrual periods. See the
                                              _date_adjust method for the base
                                              Instrument class for implemented
                                              conventions
                                              [default: 'unadjusted']
        fixed_payment_adjustment (string)   : Adjustment type for fixed
                                              payment periods. See the
                                              _date_adjust method for the base
                                              Instrument class for implemented
                                              conventions
                                              [default: 'unadjusted']
        float_payment_adjustment (string)   : Adjustment type for floating
                                              payment periods. See the
                                              _date_adjust method for the base
                                              Instrument class for implemented
                                              conventions
                                              [default: 'unadjusted']
        second (datetime)                   : Specify the first regular roll
                                              date for the accrual periods
                                              [default: False]
        penultimate (datetime)              : Specify the last regular roll
                                              date for the accrual periods
                                              [default: False]
        fixing_lag (int)                    : Days prior to the first accrual
                                              period that the floating rate
                                              is fixed
                                              [default: 0]
        notional (int)                      : Notional amount for use with
                                              calculating swap the swap value.
                                              Larger numbers will be slower,
                                              but more exact.
                                              [default: 100]
        rate_tenor (Tenor)                  : Length of the floating rate
                                              accrual period
                                              [default: ON]
        rate_basis (string)                 : Accrual basis of the LIBOR rate.
                                              See the daycount method of the
                                              base Instrument class for
                                              implemented conventions.
                                              [default: 'act360']
    """

    def __init__(self, *args, **kwargs):
        super(OISSwapInstrument, self).__init__(*args, **kwargs)
        self.instrument_type = "ois_swap"

    def discount_factor(self):
        """Returns the discount factor for the swap using Newton's method
        root finder.
        """
        return scipy.optimize.newton(self._swap_value, 0)

    def _swap_value(self, guess, args=()):
        """Private method used for root finding discount factor

        The main function for use with the root-finder. This function returns
        the value of a swap given a discount factor. It appends the discount
        factor to the existent array with the date of the instrument, calculates
        each cashflow and PV for each leg, and returns the net value of the pay
        fixed swap.

        Arguments:
            guess (float)   :   guess to be appended to a copy of the attached
                                curve.

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
                        np.datetime64(
                            self.fixed_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .strftime("%Y-%m-%d")
                        ),
                        time.mktime(
                            self.fixed_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .timetuple()
                        ),
                        # np.datetime64(self.maturity.strftime("%Y-%m-%d")),
                        # time.mktime(self.maturity.timetuple()),
                        guess,
                    )
                ],
                dtype=self.curve.curve.dtype,
            ),
        )
        interpolator = scipy.interpolate.PchipInterpolator(
            temp_curve["timestamp"], temp_curve["discount_factor"]
        )

        for period in self.float_schedule.periods:
            forward_rate = self.__forward_rate(interpolator, period)
            accrual_period = super(OISSwapInstrument, self).daycount(
                period["accrual_start"], period["accrual_end"], self.float_basis
            )
            period["cashflow"] = forward_rate * self.notional

        payment_dates = self.float_schedule.periods["payment_date"].astype("<M8[s]")
        discount_factors = np.exp(interpolator(payment_dates.astype(np.uint64)))
        self.float_schedule.periods["PV"] = (
            self.float_schedule.periods["cashflow"] * discount_factors
        )

        float_leg = self.float_schedule.periods["PV"].sum()

        for period in self.fixed_schedule.periods:
            forward_rate = self.rate
            accrual_period = super(OISSwapInstrument, self).daycount(
                period["accrual_start"], period["accrual_end"], self.fixed_basis
            )
            period["cashflow"] = forward_rate * accrual_period * self.notional

        payment_dates = self.fixed_schedule.periods["payment_date"].astype("<M8[s]")
        discount_factors = np.exp(interpolator(payment_dates.astype(np.uint64)))
        self.fixed_schedule.periods["PV"] = (
            self.fixed_schedule.periods["cashflow"] * discount_factors
        )

        fixed_leg = self.fixed_schedule.periods["PV"].sum()

        return float_leg - fixed_leg

    def __forward_rate(self, interpolator, period):
        """Private method for calculating the compounded forward rate for an OIS
        swap.

        The compounded forward rate is calculated as the

                                     DF[i]
                                Π [ ------- ] - 1
                                i   DF[i+1]

        Note that it achieves very speedily by calculating each forward
        rate (+ 1) for the entire date array, and then calculating the product
        of the array. Additionally, there are 3 entries for every Friday, as
        each friday should compound 3 times (no new rates on weekends).

        Arguments:
            interpolator (scipy.interpolate):   temporary interpolator object
                                                that includes the current swap
                                                maturity guess discount factor.
            period (np.recarray)            :   1 line of the swapschedule array
                                                must contain the accrual start
                                                and end dates
        """
        start_date = period["accrual_start"].astype("<M8[s]")
        end_date = period["accrual_end"].astype("<M8[s]")
        one_day = np.timedelta64(1, "D")
        first_dates = np.arange(start_date, end_date, one_day)
        # Remove all Saturdays and Sundays
        first_dates = first_dates[
            ((first_dates.astype("datetime64[D]").view("int64") - 4) % 7) < 5
        ]
        second_dates = np.roll(first_dates, -1)
        second_dates[-1] = period["accrual_end"]

        # weights = (second_dates - first_dates) / np.timedelta64(1, "D")
        initial_dfs = np.exp(interpolator(first_dates))
        end_dfs = np.exp(interpolator(second_dates))
        # rates = ((initial_dfs / end_dfs) - 1) * (360 / weights)
        rates = initial_dfs / end_dfs
        rate = rates.prod() - 1
        return rate
