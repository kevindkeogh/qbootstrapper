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
import sys

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
        fixed_tenor=None,
        float_tenor=None,
        fixed_period_adjustment="unadjusted",
        float_period_adjustment="unadjusted",
        fixed_payment_adjustment="unadjusted",
        float_payment_adjustment="unadjusted",
        fixed_payment_lag=None,
        float_payment_lag=None,
        calendar=None,
        second=False,
        penultimate=False,
        fixing_lag=None,
        notional=100,
        rate_tenor=None,
        rate_basis="act360",
        spot_lag=None,
        name=None,
    ):

        # assignments
        self.fixing_lag = fixing_lag if fixing_lag is not None else Tenor("0D")
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

        if bool(second):
            self.second = second
        if bool(penultimate):
            self.penultimate = penultimate

        self.rate = rate
        self.curve = curve
        self.notional = notional

        self.fixed_basis = fixed_basis
        self.fixed_tenor = fixed_tenor if fixed_tenor is not None else Tenor("6M")
        self.fixed_period_adjustment = fixed_period_adjustment
        self.fixed_payment_adjustment = fixed_payment_adjustment
        self.fixed_payment_lag = (
            fixed_payment_lag if fixed_payment_lag is not None else Tenor("0D")
        )

        self.float_basis = float_basis
        self.float_tenor = float_tenor if float_tenor is not None else Tenor("6M")
        self.float_period_adjustment = float_period_adjustment
        self.float_payment_adjustment = float_payment_adjustment
        self.float_payment_lag = (
            float_payment_lag if float_payment_lag is not None else Tenor("0D")
        )

        self.rate_tenor = rate_tenor if rate_tenor is not None else Tenor("ON")
        self.rate_basis = rate_basis

        self.name = name if name is not None else "SWAP"

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
                payment_lag=self.fixed_payment_lag,
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
                payment_lag=self.float_payment_lag,
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
                payment_lag=self.fixed_payment_lag,
            )
            self.float_schedule = Schedule(
                self.effective,
                self.maturity,
                self.float_tenor,
                period_adjustment=self.float_period_adjustment,
                payment_adjustment=self.float_payment_adjustment,
                fixing_lag=self.fixing_lag,
                calendar=self.calendar,
                payment_lag=self.float_payment_lag,
            )
