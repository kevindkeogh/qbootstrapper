#! /usr/bin/env python
# vim: set fileencoding=utf-8
"""
Copyright (c) Kevin Keogh 2016-2020

Implements the Curve ojects that can be used to hold discount factor
curves and implement the build method for bootstrapping.

Note that there must be at least 1 analytic (cash/fra/futures) instrument
in the curve if there are swaps in the curve, otherwise the splines cannot
build and the curve will fail.
"""
# python libraries
import datetime
import numpy as np
import operator
import scipy.interpolate
import time

# qlib libraries
import qbootstrapper as qb


class Curve(object):
    """Base Interest Rate Swap Curve class
    The Curve class, holds multiple attributes and methods for use with
    interest rate swap curve construction. The class also allows, after
    construction, discount factors to be drawn for arbitrary dates.

    Arguments:
        effective_date (datetime)   : Effective date of the curve

        kwargs
        ------
        name (str)                  : Curve name
        discount_curve (Curve)      : Discount curve for dual curve bootstrap
                                      [default: False]
        allow_extrapolation (bool)  : Boolean for allowing the interpolant
                                      to extrapolation

    Attributes:
        curve (np.array)            : Numpy 3xn array of log discount factors
                                      Takes the form:
                                            Date (string), Date (epoch), log(DF)
        discount_curve (Curve)      : If the discount_curve is specified,
                                      holds the reference to the curve

        instruments (list)          : List of the instruments in the curve
        allow_extrapolation (bool)  : Boolean, reflecting whether the
                                      interpolant can extrapolate
    """

    def __init__(
        self, effective_date, name=None, discount_curve=False, allow_extrapolation=True
    ):
        if type(effective_date) is not datetime.datetime:
            raise TypeError("Effective date must be of type datetime.datetime")

        if not isinstance(discount_curve, Curve) and discount_curve is not False:
            raise TypeError("Discount curve must of of type Curve")

        if type(allow_extrapolation) is not bool:
            raise TypeError("Allow_extrapolation must be of type 'bool'")

        self.curve = np.array(
            [
                (
                    np.datetime64(effective_date.strftime("%Y-%m-%d")),
                    time.mktime(effective_date.timetuple()),
                    "NA",
                    np.float64(0),
                    np.log(1),
                )
            ],
            dtype=[
                ("maturity", "datetime64[D]"),
                ("timestamp", np.float64),
                ("name", "a30"),
                ("par_rate", np.float64),
                ("discount_factor", np.float64),
            ],
        )

        self.date = effective_date
        self.curve_type = "CURVE"
        self.name = name if name is not None else "CURVE"
        self.discount_curve = discount_curve
        self.instruments = []
        self._built = False
        self.allow_extrapolation = allow_extrapolation

    def add_instrument(self, instrument):
        """Add an instrument to the curve
        """
        if isinstance(instrument, qb.Instrument):
            self._built = False
            self.instruments.append(instrument)
        else:
            raise TypeError("Instruments must be a of type Instrument")

    def build(self):
        """Initiate the curve construction procedure
        """
        self.curve = self.curve[0]
        self.instruments.sort(key=operator.attrgetter("maturity"))
        for instrument in self.instruments:
            discount_factor = instrument.discount_factor()
            if not isinstance(instrument, qb.SwapInstrument):
                curve_date = instrument.maturity
            else:
                curve_date = instrument.fixed_schedule.periods[-1][
                    "payment_date"
                ].astype(object)

            if hasattr(instrument, "price"):
                rate = instrument.price
            elif hasattr(instrument, "leg_one_spread"):
                if abs(instrument.leg_one_spread) > abs(instrument.leg_two_spread):
                    rate = instrument.leg_one_spread
                else:
                    rate = instrument.leg_one_spread
            else:
                rate = instrument.rate

            array = np.array(
                [
                    (
                        np.datetime64(curve_date.strftime("%Y-%m-%d")),
                        time.mktime(curve_date.timetuple()),
                        instrument.name,
                        np.float64(rate),
                        discount_factor,
                    )
                ],
                dtype=[
                    ("maturity", "datetime64[D]"),
                    ("timestamp", np.float64),
                    ("name", "a30"),
                    ("par_rate", np.float64),
                    ("discount_factor", np.float64),
                ],
            )

            self.curve = np.append(self.curve, array)

        self._built = True

    def discount_factor(self, date):
        """Returns the interpolated discount factor for an arbitrary date
        """
        if type(date) is not datetime.datetime and type(date) is not np.datetime64:
            raise TypeError("Date must be a datetime.datetime or np.datetime64")
        if type(date) == datetime.datetime:
            date = time.mktime(date.timetuple())

        return np.exp(self.log_discount_factor(date))

    def log_discount_factor(self, date):
        """Returns the natural log of the discount factor for an arbitrary date
        """
        if type(date) == datetime.datetime:
            date = time.mktime(date.timetuple())

        interpolator = scipy.interpolate.PchipInterpolator(
            self.curve["timestamp"],
            self.curve["discount_factor"],
            extrapolate=self.allow_extrapolation,
        )
        return interpolator(date)

    def view(self, ret=False):
        """Prints the discount factor curve
        Optionally return tuple of the maturities and discount factors
        """
        if not self._built:
            self.build()

        maturities = self.curve["maturity"]
        discount_factors = np.exp(self.curve["discount_factor"])
        for i in range(len(self.curve)):
            date = maturities[i].astype(object).strftime("%Y-%m-%d")
            print("{0} {1:.10f}".format(date, discount_factors[i]))

        if ret:
            return maturities, discount_factors

    def zeros(self, ret=False, show=True):
        """Prints the zero rate curve
        Optionally return tuple of the maturities and discount factors
        """
        if not self._built:
            self.build()

        maturities = self.curve["maturity"]
        zero_rates = np.zeros(len(maturities))
        for i in range(1, len(self.curve)):
            days = (
                (self.curve[i]["maturity"] - self.curve[0]["maturity"])
                / np.timedelta64(1, "D")
            ) / 365
            zero_rates[i] = -self.curve[i]["discount_factor"] / days

        if show:
            for i in range(len(self.curve)):
                print("{0} {1:.4f}%".format(maturities[i], zero_rates[i] * 100))

        if ret:
            return maturities, zero_rates

    def summary(self):
        """Returns a summary of the curve"""
        return np.rec.fromarrays(
            [
                self.curve["maturity"],
                self.curve["name"],
                self.curve["par_rate"],
                np.exp(self.curve["discount_factor"]),
            ],
            names=["maturity", "name", "par rate", "discount_factor"],
        )


class LIBORCurve(Curve):
    """Implementation of the Curve class for LIBOR curves.
    Build method is over-written to cause the discount curve to be built
    in the case of a dual bootstrap
    """

    def __init__(self, *args, **kwargs):
        super(LIBORCurve, self).__init__(*args, **kwargs)
        if self.name is "CURVE":
            self.name = "CURVE-LIBOR"

    def build(self):
        """Checks to see if the discount curve has already been built before
        running the base class build method
        """
        if self.discount_curve and self.discount_curve._built is False:
            self.discount_curve.build()

        super(LIBORCurve, self).build()


class OISCurve(Curve):
    """Implementation of the Curve class for OIS curves
    """

    def __init__(self, *args, **kwargs):
        super(OISCurve, self).__init__(*args, **kwargs)
        if self.name is "CURVE":
            self.name = "CURVE-OIS"


class SimultaneousStrippedCurve(Curve):
    """Implementation of the Curve class for a curve that can simultaneously
    bootstrap, such as OIS and LIBOR curves using AverageIndexBasisSwap
    instruments

    Arguments:
        effective_date (datetime)   : Effective date of the curve
        curve_one (Curve)           : First curve to bootstrap. Note that this
                                      should be a curve (one of base Curve,
                                      LIBORCurve, or OISCurve), and should
                                      already include instruments that aren't
                                      simultaneous, such as cash, futures, and
                                      fixed-float swaps
        curve_two (Curve)           : Second curve to bootstrap. Note that this
                                      should be a curve (one of base Curve,
                                      LIBORCurve, or OISCurve), and should
                                      already include instruments that aren't
                                      simultaneous, such as cash, futures, and
                                      fixed-float swaps
        discount_curve (Curve)      : Discount curve for dual-curve stripping.
                                      Note that in the typical case, where one
                                      of the prior two curves is the curve for
                                      dual-stripping the other, the same curve
                                      should be referenced here. This should
                                      not be a copy of one of curve_one or
                                      curve_two.

        kwargs
        ------
        name (str)                  : Curve name
        allow_extrapolation (bool)  : Allow extrapolation in curve
                                      bootstrapping
                                      [default: True]
    """

    def __init__(
        self,
        effective_date,
        curve_one,
        curve_two,
        discount_curve,
        name=None,
        allow_extrapolation=True,
    ):

        if type(effective_date) is not datetime.datetime:
            raise TypeError("Effective date must be of type datetime.datetime")

        if not isinstance(discount_curve, Curve) and discount_curve is not False:
            raise TypeError("Discount curve must of of type Curve")

        if type(allow_extrapolation) is not bool:
            raise TypeError("Allow_extrapolation must be of type 'bool'")

        self.name = name if name is not None else "CURVE-SIMULTANEOUS"
        self.curve_one = curve_one
        self.curve_two = curve_two
        self.discount_curve = discount_curve
        self.curve_one.discount_curve = self.discount_curve
        self.curve_two.discount_curve = self.discount_curve

        self.instruments = []
        self._built = False
        self.allow_extrapolation = allow_extrapolation

    def build(self):
        """Build the underlying curves as much as possible, then build each of
        the simultaneous instruments iteratively.

        Note that the order of the instruments must be strictly earliest to
        last, and the first simultaneous instrument must be after the last
        instrument in each of the projection and discount curves.
        """
        self.curve_one.build()
        self.curve_two.build()

        # TODO figure out some way of sorting these things
        # self.instruments.sort(key=operator.attrgetter('maturity'))

        for instrument in self.instruments:
            df = instrument.discount_factor()

            if df.success:
                leg_one_df, leg_two_df = df.x

                last_date = None
                for attr in [
                    "leg_one_schedule",
                    "leg_two_schedule",
                    "fixed_schedule",
                    "float_schedule",
                ]:
                    if hasattr(instrument.instrument_one, attr):
                        maybe = (
                            getattr(instrument.instrument_one, attr)
                            .periods[-1]["payment_date"]
                            .astype(object)
                        )
                        if last_date is None:
                            last_date = maybe
                        elif maybe > last_date:
                            last_date = maybe

                if hasattr(instrument.instrument_one, "price"):
                    rate = instrument.instrument_one.price
                elif hasattr(instrument.instrument_one, "leg_one_spread"):
                    if abs(instrument.instrument_one.leg_one_spread) > abs(
                        instrument.instrument_one.leg_two_spread
                    ):
                        rate = instrument.instrument_one.leg_one_spread
                    else:
                        rate = instrument.instrument_one.leg_two_spread
                else:
                    rate = instrument.instrument_one.rate

                array = np.array(
                    [
                        (
                            np.datetime64(last_date.strftime("%Y-%m-%d")),
                            time.mktime(last_date.timetuple()),
                            instrument.instrument_one.name,
                            np.float64(rate),
                            leg_one_df,
                        )
                    ],
                    dtype=self.curve_one.curve.dtype,
                )
                self.curve_one.curve = np.append(self.curve_one.curve, array)

                last_date = None
                for attr in [
                    "leg_one_schedule",
                    "leg_two_schedule",
                    "fixed_schedule",
                    "float_schedule",
                ]:
                    if hasattr(instrument.instrument_two, attr):
                        maybe = (
                            getattr(instrument.instrument_two, attr)
                            .periods[-1]["payment_date"]
                            .astype(object)
                        )
                        if last_date is None:
                            last_date = maybe
                        elif maybe > last_date:
                            last_date = maybe

                if hasattr(instrument.instrument_two, "price"):
                    rate = instrument.instrument_two.price
                elif hasattr(instrument.instrument_two, "leg_one_spread"):
                    if abs(instrument.instrument_two.leg_one_spread) > abs(
                        instrument.instrument_two.leg_two_spread
                    ):
                        rate = instrument.instrument_two.leg_one_spread
                    else:
                        rate = instrument.instrument_two.leg_two_spread
                else:
                    rate = instrument.instrument_two.rate

                array = np.array(
                    [
                        (
                            np.datetime64(last_date.strftime("%Y-%m-%d")),
                            time.mktime(last_date.timetuple()),
                            instrument.instrument_two.name,
                            np.float64(rate),
                            leg_two_df,
                        )
                    ],
                    dtype=self.curve_two.curve.dtype,
                )
                self.curve_two.curve = np.append(self.curve_two.curve, array)
            else:
                print("Failed to bootstrap instrument")

        self._built = True

    def view(self):
        raise NotImplementedError(
            "Please view the individual curves using the"
            " self.curve_one and"
            " self.curve_two syntax"
        )

    def zeros(self):
        raise NotImplementedError(
            "Please view the individual curves using the"
            " self.curve_one and"
            " self.curve_two syntax"
        )
