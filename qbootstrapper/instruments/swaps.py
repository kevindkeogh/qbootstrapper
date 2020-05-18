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
import dateutil.relativedelta
import datetime
import numpy as np
import scipy.interpolate
import scipy.optimize
import sys
import time

# qlib libraries
from qbootstrapper.instruments import Instrument
from qbootstrapper.swapscheduler import Schedule
from qbootstrapper.utils import Calendar, Tenor

if sys.version_info > (3,):
    long = int


class SwapInstrument(Instrument):
    """Base class for swap instruments. See OISSwapInstrument and
    LIBORSwapInstrument for more detailed specs.
    """

    def __init__(
        self,
        effective,
        maturity,
        rate,
        curve,
        fixed_basis="30360",
        float_basis="act360",
        fixed_tenor=Tenor("6M"),
        float_tenor=Tenor("6M"),
        fixed_period_adjustment="unadjusted",
        float_period_adjustment="unadjusted",
        fixed_payment_adjustment="unadjusted",
        float_payment_adjustment="unadjusted",
        calendar=Calendar("weekends"),
        second=False,
        penultimate=False,
        fixing_lag=Tenor("0D"),
        notional=100,
        rate_tenor=Tenor("ON"),
        rate_basis="act360",
    ):

        # assignments
        self.effective = effective
        self.maturity = maturity
        if bool(second):
            self.second = second
        if bool(penultimate):
            self.penultimate = penultimate
        self.rate = rate
        self.calendar = calendar
        self.curve = curve
        self.fixing_lag = fixing_lag
        self.notional = notional

        self.fixed_basis = fixed_basis
        self.fixed_tenor = fixed_tenor
        self.fixed_period_adjustment = fixed_period_adjustment
        self.fixed_payment_adjustment = fixed_payment_adjustment

        self.float_basis = float_basis
        self.float_tenor = float_tenor
        self.float_period_adjustment = float_period_adjustment
        self.float_payment_adjustment = float_payment_adjustment

        self.rate_tenor = rate_tenor
        self.rate_basis = rate_basis

        self._set_schedules()

    def _set_schedules(self):
        """Sets the fixed and floating schedules of the swap.
        """
        if hasattr(self, "second"):
            self.fixed_schedule = Schedule(
                self.effective,
                self.maturity,
                self.fixed_tenor,
                second=self.second,
                penultimate=self.penultimate,
                period_adjustment=self.fixed_period_adjustment,
                payment_adjustment=self.fixed_payment_adjustment,
                fixing_lag=self.fixing_lag,
                calendar=self.calendar,
            )
            self.float_schedule = Schedule(
                self.effective,
                self.maturity,
                self.float_tenor,
                second=self.second,
                penultimate=self.penultimate,
                period_adjustment=self.float_period_adjustment,
                payment_adjustment=self.float_payment_adjustment,
                fixing_lag=self.fixing_lag,
                calendar=self.calendar,
            )
        else:
            self.fixed_schedule = Schedule(
                self.effective,
                self.maturity,
                self.fixed_tenor,
                period_adjustment=self.fixed_period_adjustment,
                payment_adjustment=self.fixed_payment_adjustment,
                fixing_lag=self.fixing_lag,
                calendar=self.calendar,
            )
            self.float_schedule = Schedule(
                self.effective,
                self.maturity,
                self.float_tenor,
                period_adjustment=self.float_period_adjustment,
                payment_adjustment=self.float_payment_adjustment,
                fixing_lag=self.fixing_lag,
                calendar=self.calendar,
            )


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
                                              [default: 'Act360']
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
                                              [default: 'Act360']
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

        for period in self.float_schedule.periods:
            forward_rate = self.__forward_rate(interpolator, period)
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
        start_day = start_date.astype(object).weekday()
        rate = 1
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
        rates = initial_dfs / end_dfs
        rate = rates.prod() - 1
        return rate


class LIBORSwapInstrument(SwapInstrument):
    """LIBOR swap instrument class for use with Swap Curve bootstrapper.

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
                                              [default: 'Act360']
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
                                              [default: 'Act360']
    """

    def __init__(self, *args, **kwargs):
        super(LIBORSwapInstrument, self).__init__(*args, **kwargs)
        self.instrument_type = "libor_swap"

    def discount_factor(self):
        """Returns the natural log of the discount factor for the swap
        using Newton's method root finder.
        """
        return scipy.optimize.newton(self._swap_value, 0)

    def _swap_value(self, guess, args=()):
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
            guess = guess[1]

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
        leg_one_basis="Act360",
        leg_two_basis="Act360",
        leg_one_tenor=Tenor("3M"),
        leg_two_tenor=Tenor("3M"),
        leg_one_period_adjustment="unadjusted",
        leg_two_period_adjustment="unadjusted",
        leg_one_payment_adjustment="unadjusted",
        leg_two_payment_adjustment="unadjusted",
        second=False,
        penultimate=False,
        notional=100,
        leg_one_fixing_lag=Tenor("0D"),
        leg_two_fixing_lag=Tenor("0D"),
        leg_one_rate_tenor=Tenor("ON"),
        leg_one_rate_basis="Act360",
        leg_two_rate_tenor=Tenor("3M"),
        leg_two_rate_basis="Act360",
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
        self.leg_one_tenor = leg_one_tenor
        self.leg_one_period_adjustment = leg_one_period_adjustment
        self.leg_one_payment_adjustment = leg_one_payment_adjustment

        self.leg_two_basis = leg_two_basis
        self.leg_two_tenor = leg_two_tenor
        self.leg_two_period_adjustment = leg_two_period_adjustment
        self.leg_two_payment_adjustment = leg_two_payment_adjustment

        self.leg_one_fixing_lag = leg_one_fixing_lag
        self.leg_one_rate_tenor = leg_one_rate_tenor
        self.leg_one_rate_basis = leg_one_rate_basis

        self.leg_two_fixing_lag = leg_two_fixing_lag
        self.leg_two_rate_tenor = leg_two_rate_tenor
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


class SimultaneousInstrument(Instrument):
    """
    """

    def __init__(
        self,
        discount_instrument,
        projection_instrument,
        curve,
        method="SLSQP",
        disp=False,
    ):

        self.discount_instrument = discount_instrument
        self.projection_instrument = projection_instrument
        self.method = method
        self.disp = disp
        self.instrument_type = "simultaneous_instrument"

    def discount_factor(self):
        """
        """
        guesses = np.array([-0.000001, -0.000001])
        bounds = ((np.log(0.001), np.log(2)), (np.log(0.001), np.log(2)))
        dfs = scipy.optimize.minimize(
            self._swap_value,
            guesses,
            method=self.method,
            bounds=bounds,
            options={"disp": self.disp},
        )
        return dfs

    def _swap_value(self, guesses):
        """
        """
        discount_value = self.discount_instrument._swap_value(guesses)
        projection_value = self.projection_instrument._swap_value(guesses)
        return max(abs(discount_value), abs(projection_value))
