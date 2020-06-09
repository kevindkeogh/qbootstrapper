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
import numpy as np
import scipy.interpolate
import scipy.optimize
import sys
import time

# qlib libraries
from qbootstrapper.instruments import SwapInstrument
from qbootstrapper.swapscheduler import Schedule
from qbootstrapper.utils import Calendar, Tenor


if sys.version_info > (3,):
    long = int


class BasisSwapInstrument(SwapInstrument):
    """Basis swap instrument class for use with Swap Curve bootstrapper.

    This class can be utilized to hold the market data and conventions
    for a single basis swap, which is later utilized in when the .build()
    method is called on the curve where this instrument has been added.

    Arguments:
        effective (datetime)                : First accrual start date of
                                              the swap
        maturity (datetime, Tenor)          : The tenor or the last accrual end
                                              date of the swap
        curve (Curve object)                : Associated curve object.
                                              There are callbacks to the
                                              curve for prior discount
                                              factors, so it must be
                                              assigned

        kwargs (optional)
        -----------------
        leg_one_spread (float)              : Spread on the floating rate
                                              for the first leg
                                              [default: 0]
        leg_two_spread (float)              : Spread on the floating rate
                                              for the second leg
                                              [default: 0]
        leg_one_basis (string)              : Accrual basis of the first
                                              leg. See daycount method of
                                              base Instrument class for
                                              implemented conventions
                                              [default: 'act360']
        leg_two_basis (string)              : Accrual basis of the second
                                              leg. See daycount method of
                                              base Instrument class for
                                              implemented conventions
                                              [default: 'act360']
        leg_one_tenor (Tenor)               : Length of the first leg's accrual
                                              period
                                              [default: 3M]
        leg_two_tenor (Tenor)               : Length of the second leg's
                                              accrual period
                                              [default: 3M]
        leg_one_period_adjustment (string)  : Adjustment type for the first
                                              leg's accrual periods. See the
                                              _date_adjust method of the base
                                              Instrument class for implemented
                                              conventions
                                              [default: 'unadjusted']
        leg_two_period_adjustment (string)  : Adjustment type for the second
                                              leg's accrual periods. See the
                                              _date_adjust method of the base
                                              Instrument class for implemented
                                              conventions
                                              [default: 'unadjusted']
        leg_one_payment_adjustment (string) : Adjustment type for first leg's
                                              payment periods. See the
                                              _date_adjust method for the base
                                              Instrument class for implemented
                                              conventions
                                              [default: 'unadjusted']
        leg_one_payment_adjustment (string) : Adjustment type for second leg's
                                              payment periods. See the
                                              _date_adjust method for the base
                                              Instrument class for implemented
                                              conventions
                                              [default: 'unadjusted']
        leg_one_payment_lag (Tenor)         : Payment lag for each coupon
                                              payment on the first leg.
                                              [default: '0D']
        leg_two_payment_lag (Tenor)         : Payment lag for each coupon
                                              payment on the second leg.
                                              [default: '0D']
        calendar (Calendar)                 : Holiday calendar used for all
                                              date adjustments
        second (datetime)                   : Specify the first regular roll
                                              date for the accrual periods
                                              [default: False]
        penultimate (datetime)              : Specify the last regular roll
                                              date for the accrual periods
                                              [default: False]
        notional (int)                      : Notional amount for use with
                                              calculating swap the swap value.
                                              Larger numbers will be slower,
                                              but more exact.
        leg_one_fixing_lag (Tenor)          : Tenor (usually days) prior to the
                                              first accrual period that the
                                              floating rate is fixed for the
                                              first leg
                                              [default: '0D']
        leg_two_fixing_lag (Tenor)          : Tenor (usually days) prior to the
                                              first accrual period that the
                                              floating rate is fixed for the
                                              second leg
                                              [default: '0D']
                                              [default: 100]
        leg_one_rate_tenor (Tenor)          : Length of the floating rate
                                              accrual period for the first leg
                                              [default: ON]
        leg_one_rate_basis (string)         : Accrual basis of the rate for the
                                              first leg.
                                              See the daycount method of the
                                              base Instrument class for
                                              implemented conventions.
                                              [default: 'act360']
        leg_two_rate_tenor (Tenor)          : Length of the floating rate
                                              accrual period for the second leg
                                              [default: ON]
        leg_two_rate_basis (string)         : Accrual basis of the rate for the
                                              second leg.
                                              See the daycount method of the
                                              base Instrument class for
                                              implemented conventions.
                                              [default: 'act360']
        name (string)                       : Name of the instrument
                                              [default: 'SWAP-BASIS-{maturity}']
    """

    def __init__(
        self,
        effective,
        maturity,
        curve,
        spot_lag,
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
        leg_one_payment_lag=None,
        leg_two_payment_lag=None,
        calendar=None,
        second=False,
        penultimate=False,
        notional=100,
        leg_one_fixing_lag=None,
        leg_two_fixing_lag=None,
        leg_one_rate_tenor=None,
        leg_one_rate_basis="act360",
        leg_two_rate_tenor=None,
        leg_two_rate_basis="act360",
        name=None,
    ):

        # assignments
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
        self.leg_one_payment_lag = leg_one_payment_lag
        self.leg_one_payment_lag = (
            leg_one_payment_lag if leg_one_payment_lag is not None else Tenor("0D")
        )

        self.leg_two_basis = leg_two_basis
        self.leg_two_tenor = leg_two_tenor if leg_two_tenor is not None else Tenor("3M")
        self.leg_two_period_adjustment = leg_two_period_adjustment
        self.leg_two_payment_adjustment = leg_two_payment_adjustment
        self.leg_two_payment_lag = (
            leg_two_payment_lag if leg_two_payment_lag is not None else Tenor("0D")
        )

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

        self.calendar = calendar if calendar is not None else Calendar("weekends")
        self.spot_lag = spot_lag if spot_lag is not None else Tenor("0D")
        self.effective = self.calendar.advance(effective, self.spot_lag)

        if type(maturity) is datetime.datetime:
            self.tenor = None
            self.maturity = maturity
        elif type(maturity) is Tenor:
            self.tenor = maturity
            self.maturity = self.calendar.advance(
                self.effective, maturity, "unadjusted"
            )
        else:
            raise ValueError("Maturity must be of type datetime or Tenor")

        if name is None:
            if self.tenor:
                self.name = "SWAP-BASIS-" + self.tenor.name
            else:
                self.name = "SWAP-BASIS-" + self.maturity.strftime("%Y-%m-%d")
        else:
            self.name = name

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
                payment_lag=self.leg_one_payment_lag,
                fixing_lag=self.leg_one_fixing_lag,
                calendar=self.calendar,
            )
            self.leg_two_schedule = Schedule(
                self.effective,
                self.maturity,
                self.leg_two_tenor,
                second=self.second,
                penultimate=self.penultimate,
                period_adjustment=self.leg_two_period_adjustment,
                payment_adjustment=self.leg_two_payment_adjustment,
                payment_lag=self.leg_two_payment_lag,
                fixing_lag=self.leg_two_fixing_lag,
                calendar=self.calendar,
            )
        else:
            self.leg_one_schedule = Schedule(
                self.effective,
                self.maturity,
                self.leg_one_tenor,
                period_adjustment=self.leg_one_period_adjustment,
                payment_adjustment=self.leg_one_payment_adjustment,
                payment_lag=self.leg_one_payment_lag,
                fixing_lag=self.leg_one_fixing_lag,
                calendar=self.calendar,
            )
            self.leg_two_schedule = Schedule(
                self.effective,
                self.maturity,
                self.leg_two_tenor,
                period_adjustment=self.leg_two_period_adjustment,
                payment_adjustment=self.leg_two_payment_adjustment,
                payment_lag=self.leg_two_payment_lag,
                fixing_lag=self.leg_two_fixing_lag,
                calendar=self.calendar,
            )


class AverageIndexBasisSwapInstrument(BasisSwapInstrument):
    """Note that leg_one must be the OIS curve, and leg_two must be the LIBOR
    curve
    """

    def __init__(self, *args, **kwargs):
        super(AverageIndexBasisSwapInstrument, self).__init__(*args, **kwargs)
        if self.name.startswith("SWAP-BASIS"):
            if self.tenor:
                self.name = "SWAP-AVERAGEINDEX-" + self.tenor.name
            else:
                self.name = "SWAP-AVERAGEINDEX-" + self.maturity.strftime("%Y-%m-%d")

    def discount_factor(self):
        """Returns the natural log of each of the OIS and LIBOR discount factors
        for the swap using the Levenberg-Marquardt method.

        Note that the first guess is the OIS discount factor, the second guess
        is the LIBOR discount factor
        """
        raise NotImplementedError

    def _swap_value(self, guesses, *_):
        """
        Note that this approach should only be used for a
        SimultaneousStrippedCurve

        TODO: Seperate cases for when self.curve.curve_type ==
        'Simultaneous_curve' and when not
        """
        ois_guess = guesses[0]
        libor_guess = guesses[1]

        curve_one = np.append(
            self.curve.curve_one.curve,
            np.array(
                [
                    (
                        np.datetime64(
                            self.leg_one_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .strftime("%Y-%m-%d")
                        ),
                        time.mktime(
                            self.leg_one_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .timetuple()
                        ),
                        self.name,
                        np.float64(self.leg_one_spread),
                        ois_guess,
                    )
                ],
                dtype=self.curve.curve_one.curve.dtype,
            ),
        )

        leg_one_interpolator = scipy.interpolate.PchipInterpolator(
            curve_one["timestamp"], curve_one["discount_factor"]
        )

        curve_two = np.append(
            self.curve.curve_two.curve,
            np.array(
                [
                    (
                        np.datetime64(
                            self.leg_two_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .strftime("%Y-%m-%d")
                        ),
                        time.mktime(
                            self.leg_two_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .timetuple()
                        ),
                        self.name,
                        np.float64(self.leg_one_spread),
                        libor_guess,
                    )
                ],
                dtype=self.curve.curve_two.curve.dtype,
            ),
        )
        leg_two_interpolator = scipy.interpolate.PchipInterpolator(
            curve_two["timestamp"], curve_two["discount_factor"]
        )

        discount_interpolator = scipy.interpolate.PchipInterpolator(
            self.curve.discount_curve.curve["timestamp"],
            self.curve.discount_curve.curve["discount_factor"],
        )

        for period in self.leg_one_schedule.periods:
            forward_rate = self.__compound_forward_rate(leg_one_interpolator, period)
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

        return ois_leg - libor_leg

    def __compound_forward_rate(self, interpolator, period):
        """Calculate OIS forward rate for a period
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
        # TODO: Check that the rate is actual/360
        rates = ((initial_dfs / end_dfs) - 1) * 360
        rate = rates.mean()
        return rate


class CompoundIndexBasisSwapInstrument(BasisSwapInstrument):
    """Note that leg_one must be the SOFR curve, and leg_two must be the OIS
    curve
    """

    def __init__(self, *args, **kwargs):
        super(CompoundIndexBasisSwapInstrument, self).__init__(*args, **kwargs)
        if self.name.startswith("SWAP-BASIS"):
            if self.tenor:
                self.name = "SWAP-COMPOUNDINDEX-" + self.tenor.name
            else:
                self.name = "SWAP-COMPOUNDINDEX-" + self.maturity.strftime("%Y-%m-%d")

    def discount_factor(self):
        """Returns the natural log discount factors for each curve for the
        basis swap using the Levenberg-Marquardt method.
        """
        raise NotImplementedError

    def _swap_value(self, guesses, *_):
        """
        Note that this approach should only be used for a
        SimultaneousStrippedCurve

        TODO: Seperate cases for when self.curve.curve_type ==
        'Simultaneous_curve' and when not
        """
        sofr_guess = guesses[0]
        ois_guess = guesses[1]

        # SOFR curve
        curve_one = np.append(
            self.curve.curve_one.curve,
            np.array(
                [
                    (
                        np.datetime64(
                            self.leg_one_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .strftime("%Y-%m-%d")
                        ),
                        time.mktime(
                            self.leg_one_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .timetuple()
                        ),
                        self.name,
                        np.float64(0),
                        sofr_guess,
                    )
                ],
                dtype=self.curve.curve_one.curve.dtype,
            ),
        )

        leg_one_interpolator = scipy.interpolate.PchipInterpolator(
            curve_one["timestamp"], curve_one["discount_factor"]
        )

        # OIS curve
        curve_two = np.append(
            self.curve.curve_two.curve,
            np.array(
                [
                    (
                        np.datetime64(
                            self.leg_two_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .strftime("%Y-%m-%d")
                        ),
                        time.mktime(
                            self.leg_two_schedule.periods[-1]["payment_date"]
                            .astype(object)
                            .timetuple()
                        ),
                        self.name,
                        np.float64(0),
                        ois_guess,
                    )
                ],
                dtype=self.curve.curve_two.curve.dtype,
            ),
        )
        leg_two_interpolator = scipy.interpolate.PchipInterpolator(
            curve_two["timestamp"], curve_two["discount_factor"]
        )

        discount_interpolator = scipy.interpolate.PchipInterpolator(
            self.curve.discount_curve.curve["timestamp"],
            self.curve.discount_curve.curve["discount_factor"],
        )

        # SOFR Leg
        for period in self.leg_one_schedule.periods:
            forward_rate = self.__compound_forward_rate(
                leg_one_interpolator, period, self.leg_one_rate_basis
            )
            accrual_period = super(CompoundIndexBasisSwapInstrument, self).daycount(
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

        sofr_leg = self.leg_one_schedule.periods["PV"].sum()

        # OIS Leg
        for period in self.leg_two_schedule.periods:
            forward_rate = self.__compound_forward_rate(
                leg_two_interpolator, period, self.leg_two_rate_basis
            )
            accrual_period = super(CompoundIndexBasisSwapInstrument, self).daycount(
                period["accrual_start"], period["accrual_end"], self.leg_two_basis
            )
            period["cashflow"] = (
                (forward_rate + self.leg_two_spread) * self.notional * accrual_period
            )

        payment_dates = self.leg_two_schedule.periods["payment_date"].astype("<M8[s]")
        discount_factors = np.exp(
            discount_interpolator(payment_dates.astype(np.uint64))
        )
        self.leg_two_schedule.periods["PV"] = (
            self.leg_two_schedule.periods["cashflow"] * discount_factors
        )

        ois_leg = self.leg_two_schedule.periods["PV"].sum()

        return sofr_leg - ois_leg

    def __compound_forward_rate(self, interpolator, period, rate_basis):
        """Calculate daily compounded forward rate for a period
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
        accrual_period = super(CompoundIndexBasisSwapInstrument, self).daycount(
            period["accrual_start"], period["accrual_end"], rate_basis
        )
        rates = ((initial_dfs / end_dfs) - 1) / accrual_period
        rate = (1 + rates).prod() - 1
        return rate
