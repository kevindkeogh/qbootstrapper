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

# qlib libraries
from qbootstrapper.instruments import Instrument

if sys.version_info > (3,):
    long = int


class SimultaneousInstrument(Instrument):
    """Calculate the discount factors given two instruments for two separate
    curves. This instrument should only be used when building a
    SimultaneousStrippedCurve.

    The order of the instruments should match the order of the curves in the
    simultaneous curve (i.e., the first instrument is the instrument for the
    curve entered as the first argument for the SimultaneousStrippedCurve, the
    second instrument the second argument. This bootstrapping assumes that the
    discount factors for both curves are bound between 0 and 2.

    Arguments:
        instrument_one (Instrument)         : Instrument that will be used in
                                              bootstrapping the first curve
        instrument_two (Instrument)         : Instrument that will be used in
                                              bootstrapping the second curve
        curve (Curve)                       : SimultaneousStrippedCurve to be
                                              bootstrapped

        kwargs (optional)
        -----------------
        method (str)                        : Method used by the scipy
                                              optimization function to find the
                                              roots for both curves
                                              [default: SLSQP]
        disp (bool)                         : Whether to print the result
                                              rather than returning it
                                              [default: False]
    """

    def __init__(
        self, instrument_one, instrument_two, curve, method="SLSQP", disp=False,
    ):

        self.instrument_one = instrument_one
        self.instrument_two = instrument_two
        self.method = method
        self.disp = disp
        self.instrument_type = "simultaneous_instrument"

    def discount_factor(self):
        """Method to return the discount factor for both instruments
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
        """Method to calculate the values of the two swaps. The method
        calculates the values for both swaps and returns the absolute max
        difference of both. Takes a list of guesses, referring to the discount
        factors for each curve.
        """
        inst_one_pv = self.instrument_one._swap_value(guesses, 0)
        inst_two_pv = self.instrument_two._swap_value(guesses, 1)

        return max(abs(inst_one_pv), abs(inst_two_pv))
