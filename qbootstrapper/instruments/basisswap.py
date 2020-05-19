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
from qbootstrapper.swapscheduler import Schedule
from qbootstrapper.utils import Tenor


if sys.version_info > (3,):
    long = int


class BasisSwapInstrument(SwapInstrument):
    """
    """

    def __init__(
        self,
        effective,
        maturity,
        curve,
        leg_one_spread=0,
        leg_two_spread=0,
        leg_one_basis="act360",
        leg_two_basis="act360",
        leg_one_tenor=None,
        leg_two_tenor=None,
        leg_one_period_adjustment="unadjusted",
        leg_two_period_adjustment="unadjusted",
        leg_one_payment_adjustment="unadjusted",
        leg_two_payment_adjustment="unadjusted",
        second=False,
        penultimate=False,
        notional=100,
        leg_one_fixing_lag=None,
        leg_two_fixing_lag=None,
        leg_one_rate_tenor=None,
        leg_one_rate_basis="act360",
        leg_two_rate_tenor=None,
        leg_two_rate_basis="act360",
    ):

        # assignments
        self.instrument_type = "basis_swap"
        self.effective = effective
        self.maturity = maturity
        if bool(second):
            self.second = second
        if bool(penultimate):
            self.penultimate = penultimate
        self.notional = notional

        self.leg_one_spread = leg_one_spread
        self.leg_two_spread = leg_two_spread
        self.curve = curve

        self.leg_one_basis = leg_one_basis
        self.leg_one_tenor = leg_one_tenor if leg_one_tenor is not None else Tenor("3M")
        self.leg_one_period_adjustment = leg_one_period_adjustment
        self.leg_one_payment_adjustment = leg_one_payment_adjustment

        self.leg_two_basis = leg_two_basis
        self.leg_two_tenor = leg_two_tenor if leg_two_tenor is not None else Tenor("3M")
        self.leg_two_period_adjustment = leg_two_period_adjustment
        self.leg_two_payment_adjustment = leg_two_payment_adjustment

        self.leg_one_fixing_lag = (
            leg_one_fixing_lag if leg_one_fixing_lag is not None else Tenor("0D")
        )
        self.leg_one_rate_tenor = (
            leg_one_rate_tenor if leg_one_rate_tenor is not None else Tenor("ON")
        )
        self.leg_one_rate_basis = leg_one_rate_basis

        self.leg_two_fixing_lag = (
            leg_two_fixing_lag if leg_two_fixing_lag is not None else Tenor("0D")
        )
        self.leg_two_rate_tenor = (
            leg_two_rate_tenor if leg_two_rate_tenor is not None else Tenor("3M")
        )
        self.leg_two_rate_basis = leg_two_rate_basis

        self._set_schedules()

    def _set_schedules(self):
        """Sets the schedules of the swap.
        """
        if hasattr(self, "second"):
            self.leg_one_schedule = Schedule(
                self.effective,
                self.maturity,
                self.leg_one_tenor,
                second=self.second,
                penultimate=self.penultimate,
                period_adjustment=self.leg_one_period_adjustment,
                payment_adjustment=self.leg_one_payment_adjustment,
                fixing_lag=self.leg_one_fixing_lag,
            )
            self.leg_two_shcedule = Schedule(
                self.effective,
                self.maturity,
                self.leg_two_tenor,
                second=self.second,
                penultimate=self.penultimate,
                period_adjustment=self.leg_two_period_adjustment,
                payment_adjustment=self.leg_two_payment_adjustment,
            )
        else:
            self.leg_one_schedule = Schedule(
                self.effective,
                self.maturity,
                self.leg_one_tenor,
                period_adjustment=self.leg_one_period_adjustment,
                payment_adjustment=self.leg_one_payment_adjustment,
            )
            self.leg_two_schedule = Schedule(
                self.effective,
                self.maturity,
                self.leg_two_tenor,
                period_adjustment=self.leg_two_period_adjustment,
                payment_adjustment=self.leg_two_payment_adjustment,
            )


class AverageIndexBasisSwapInstrument(BasisSwapInstrument):
    """Note that leg_one must be the OIS curve, and leg_two must be the LIBOR
    curve
    """

    def __init__(self, *args, **kwargs):
        super(AverageIndexBasisSwapInstrument, self).__init__(*args, **kwargs)
        self.instrument_type = "average_index_basis_swap"

    def discount_factor(self):
        """Returns the natural log of each of the OIS and LIBOR discount factors
        for the swap using the Levenberg-Marquardt method.

        Note that the first guess is the OIS discount factor, the second guess
        is the LIBOR discount factor
        """
        raise NotImplementedError

    def _swap_value(self, guesses):
        """
        Note that this approach should only be used for a
        SimultaneousStrippedCurve

        TODO: Seperate cases for when self.curve.curve_type ==
        'Simultaneous_curve' and when not
        """
        ois_guess = guesses[0]
        libor_guess = guesses[1]

        discount_curve = np.append(
            self.curve.discount_curve.curve,
            np.array(
                [
                    (
                        np.datetime64(self.maturity.strftime("%Y-%m-%d")),
                        time.mktime(self.maturity.timetuple()),
                        ois_guess,
                    )
                ],
                dtype=self.curve.discount_curve.curve.dtype,
            ),
        )

        leg_one_interpolator = scipy.interpolate.PchipInterpolator(
            discount_curve["timestamp"], discount_curve["discount_factor"]
        )

        projection_curve = np.append(
            self.curve.projection_curve.curve,
            np.array(
                [
                    (
                        np.datetime64(self.maturity.strftime("%Y-%m-%d")),
                        time.mktime(self.maturity.timetuple()),
                        libor_guess,
                    )
                ],
                dtype=self.curve.projection_curve.curve.dtype,
            ),
        )
        leg_two_interpolator = scipy.interpolate.PchipInterpolator(
            projection_curve["timestamp"], projection_curve["discount_factor"]
        )

        discount_interpolator = leg_one_interpolator

        for period in self.leg_one_schedule.periods:
            forward_rate = self.__ois_forward_rate(leg_one_interpolator, period)
            accrual_period = super(AverageIndexBasisSwapInstrument, self).daycount(
                period["accrual_start"], period["accrual_end"], self.leg_one_basis
            )
            period["cashflow"] = (
                (forward_rate + self.leg_one_spread) * self.notional * accrual_period
            )

        payment_dates = self.leg_one_schedule.periods["payment_date"].astype("<M8[s]")
        discount_factors = np.exp(
            discount_interpolator(payment_dates.astype(np.uint64))
        )
        self.leg_one_schedule.periods["PV"] = (
            self.leg_one_schedule.periods["cashflow"] * discount_factors
        )

        ois_leg = self.leg_one_schedule.periods["PV"].sum()

        # Libor leg calculations
        # Note that this way minimizes the number of loops
        # and calls to the interpolator objects
        fixing_dates = self.leg_two_schedule.periods["fixing_date"].astype("<M8[s]")

        end_dates = np.empty_like(fixing_dates, dtype=np.uint64)
        accrual_periods = np.empty_like(fixing_dates, dtype=np.float64)
        rate_accrual_periods = np.empty_like(fixing_dates, dtype=np.float64)

        for idx, date in enumerate(self.leg_two_schedule.periods["fixing_date"]):
            end_date = date.astype(object) + self.leg_two_rate_tenor
            end_date = np.datetime64(end_date.isoformat())
            end_dates[idx] = end_date.astype("<M8[s]").astype(np.uint64)
            rate_accrual_periods[idx] = super(
                AverageIndexBasisSwapInstrument, self
            ).daycount(date, end_date, self.leg_two_rate_basis)
            accrual_start = self.leg_two_schedule.periods[idx]["accrual_start"]
            accrual_end = self.leg_one_schedule.periods[idx]["accrual_end"]
            accrual_periods[idx] = super(
                AverageIndexBasisSwapInstrument, self
            ).daycount(accrual_start, accrual_end, self.leg_two_basis)

        initial_dfs = np.exp(leg_two_interpolator(fixing_dates))
        end_dfs = np.exp(leg_two_interpolator(end_dates))
        rate = (initial_dfs / end_dfs - 1) / rate_accrual_periods
        cashflows = (rate + self.leg_two_spread) * accrual_periods * self.notional
        self.leg_two_schedule.periods["cashflow"] = cashflows

        payment_dates = self.leg_two_schedule.periods["payment_date"].astype("<M8[s]")
        self.leg_two_schedule.periods["PV"] = cashflows * np.exp(
            discount_interpolator(payment_dates.astype(np.uint64))
        )

        libor_leg = self.leg_two_schedule.periods["PV"].sum()

        return abs(ois_leg - libor_leg)

    def __ois_forward_rate(self, interpolator, period):
        """
        """
        start_date = period["accrual_start"].astype("<M8[s]")
        end_date = period["accrual_end"].astype("<M8[s]")
        one_day = np.timedelta64(1, "D")
        start_day = start_date.astype(object).weekday()
        first_dates = np.arange(start_date, end_date, one_day)
        # replace all Saturdays and Sundays with Fridays
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
        rates = ((initial_dfs / end_dfs) - 1) * 360
        rate = rates.mean()
        return rate
