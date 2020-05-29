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
    """
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
        inst_one_pv = self.instrument_one._swap_value(guesses)
        inst_two_pv = self.instrument_two._swap_value(guesses)
        return max(abs(inst_one_pv), abs(inst_two_pv))
