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


class LIBORSwapInstrument(SwapInstrument):
    """LIBOR swap instrument class for use with Swap Curve bootstrapper.

    This class can be utilized to hold the market data and conventions
    for a single swap, which is later utilized in when the .build()
    method is called on the curve where this instrument has been added.

    Arguments:
        effective (datetime)                : First accrual start date of
                                              the swap
        maturity (datetime, Tenor)          : The tenor or the last accrual end
                                              date of the swap
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
        fixed_payment_lag (Tenor)           : Payment lag for each fixed coupon
                                              payment.
                                              [default: '0D']
        float_payment_lag (Tenor)           : Payment lag for each floating
                                              coupon payment.
                                              [default: '0D']
        calendar (Calendar)                 : Holiday calendar used for all
                                              date adjustments
                                              [default: 'weekends']
        second (datetime)                   : Specify the first regular roll
                                              date for the accrual periods
                                              [default: False]
        penultimate (datetime)              : Specify the last regular roll
                                              date for the accrual periods
                                              [default: False]
        fixing_lag (Tenor)                  : Tenor (usually days) prior to the
                                              first accrual period that the
                                              floating rate is fixed
                                              [default: '0D']
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
        super(LIBORSwapInstrument, self).__init__(*args, **kwargs)
        self.instrument_type = "libor_swap"

    def discount_factor(self):
        """Returns the natural log of the discount factor for the swap
        using Newton's method root finder.
        """
        return scipy.optimize.newton(self._swap_value, 0)

    def _swap_value(self, guess, guessidx=1, args=()):
        """Private method used for root finding discount factor

        The main function for use with the root-finder. This function returns
        the value of a swap given a discount factor. It appends the discount
        factor to the existent array with the date of the instrument, calculates
        each cashflow and PV for each leg, and returns the net value of the pay
        fixed swap.

        Calculates it as:

                     DF[Fixing_date]              [rate_days/year]
               [ ------------------------ - 1 ] * ----------------
                    DF[Fixing + tenor]              [rate_tenor]

        Arguments:
            guess (float)   :   guess to be appended to a copy of the attached
                                curve
        """
        if not isinstance(guess, (int, float, long, complex)):
            # simultaneous bootstrapping sets the guess[1] as the libor guess
            guess = guess[guessidx]

        if hasattr(self.curve, "curve"):
            temp_curve = self.curve.curve
        else:  # Simultaneous stripped curve
            temp_curve = self.curve.curve_two.curve

        temp_curve = np.append(
            temp_curve,
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
                        guess,
                    )
                ],
                dtype=temp_curve.dtype,
            ),
        )

        interpolator = scipy.interpolate.PchipInterpolator(
            temp_curve["timestamp"], temp_curve["discount_factor"]
        )

        if self.curve.discount_curve is not False:
            discount_curve = self.curve.discount_curve.log_discount_factor
        else:
            discount_curve = interpolator

        # Floating leg calculations
        # Note that this way minimizes the number of loops
        # and calls to the interpolator objects
        fixing_dates = self.float_schedule.periods["fixing_date"].astype("<M8[s]")

        end_dates = np.empty_like(fixing_dates, dtype=np.uint64)
        accrual_periods = np.empty_like(fixing_dates, dtype=np.float64)
        rate_accrual_periods = np.empty_like(fixing_dates, dtype=np.float64)

        for idx, date in enumerate(self.float_schedule.periods["fixing_date"]):
            end_date = date.astype(object) + self.rate_tenor
            end_date = np.datetime64(end_date.isoformat())
            end_dates[idx] = end_date.astype("<M8[s]").astype(np.uint64)
            rate_accrual_periods[idx] = super(LIBORSwapInstrument, self).daycount(
                date, end_date, self.rate_basis
            )
            accrual_start = self.float_schedule.periods[idx]["accrual_start"]
            accrual_end = self.float_schedule.periods[idx]["accrual_end"]
            accrual_period = super(LIBORSwapInstrument, self).daycount(
                accrual_start, accrual_end, self.float_basis
            )
            accrual_periods[idx] = accrual_period

        initial_dfs = np.exp(interpolator(fixing_dates))
        end_dfs = np.exp(interpolator(end_dates))
        rate = (initial_dfs / end_dfs - 1) / rate_accrual_periods
        cashflows = rate * accrual_periods * self.notional
        self.float_schedule.periods["cashflow"] = cashflows

        payment_dates = self.float_schedule.periods["payment_date"].astype("<M8[s]")
        self.float_schedule.periods["PV"] = cashflows * np.exp(
            discount_curve(payment_dates)
        )

        floating_leg = self.float_schedule.periods["PV"].sum()

        # Fixed leg
        accrual_periods = np.empty(
            self.fixed_schedule.periods["accrual_end"].size, dtype=np.float64
        )

        for idx, date in enumerate(self.fixed_schedule.periods["accrual_end"]):
            accrual_start = self.fixed_schedule.periods[idx]["accrual_start"]
            accrual_period = super(LIBORSwapInstrument, self).daycount(
                accrual_start, date, self.fixed_basis
            )
            accrual_periods[idx] = accrual_period

        cashflows = self.rate * accrual_periods * self.notional
        self.fixed_schedule.periods["cashflow"] = cashflows

        payment_dates = self.fixed_schedule.periods["payment_date"].astype("<M8[s]")
        self.fixed_schedule.periods["PV"] = cashflows * np.exp(
            discount_curve(payment_dates)
        )

        fixed_leg = self.fixed_schedule.periods["PV"].sum()

        return floating_leg - fixed_leg
