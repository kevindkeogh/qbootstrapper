#! /usr/bin/env python
# vim: set fileencoding=utf-8
"""
Copyright (c) Kevin Keogh

Implements the Schedule object that creates a NumPy rec.array of
accrual, fixing, and payments dates for an interest rate swap.
"""

import dateutil.relativedelta
import numpy as np

from qbootstrapper.utils import Calendar, Tenor


class Schedule:
    """Swap fixing, accrual, and payment dates

    The Schedule class can be used to generate the details for periods
    for swaps.

    Arguments:
        effective (datetime)              : effective date of the swap
        maturity (datetime)               : maturity date of the swap
        tenor (Tenor)                     : frequency of the schedule

        kwargs
        ------
        second (datetime, optional)       : second accrual date of the swap
        penultimate (datetime, optional)  : penultimate accrual date of the swap
        period_adjustment (str, optional) : date adjustment type for the accrual
                                            dates
                                            available: following,
                                                       modified following,
                                                       preceding
                                                       unadjusted
                                            [default: unadjusted]
        payment_adjustment (str, optional): date adjustment type for the
                                            payment dates
                                            available: following,
                                                       modified following,
                                                       preceding
                                                       unadjusted
                                            [default: unadjusted]
        fixing_lag (Tenor, optional)      : fixing lag for fixing dates
                                            [default: 2D]
        calendar (Calendar, optional)     : calendar used for creating schedule
                                            [default: "weekends"]


    Attributes:
        periods (np.recarray)             : numpy record array of period data
                                            takes the form
                                              [fixing_date, accrual_start,
                                               accrual_end, accrual_period,
                                               payment_date, cashflow, PV]
                                            note that cashflow and PV are
                                            empty arrays

    """

    def __init__(
        self,
        effective,
        maturity,
        tenor,
        second=False,
        penultimate=False,
        period_adjustment="unadjusted",
        payment_adjustment="unadjusted",
        fixing_lag=Tenor("-2D"),
        calendar=Calendar("weekends"),
    ):

        # variable assignment
        self.effective = effective
        self.maturity = maturity
        self.tenor = tenor
        self.period_adjustment = period_adjustment
        self.payment_adjustment = payment_adjustment
        self.second = second
        self.penultimate = penultimate
        self.fixing_lag = fixing_lag
        self.calendar = calendar

        # date generation routine
        self._gen_periods()
        self._create_schedule()

    def _gen_periods(self):
        """Private method to generate the date series
        """

        if bool(self.second) ^ bool(self.penultimate):
            raise Exception(
                "If specifying second or penultimate dates, must select both"
            )

        if self.second:
            self._period_ends = self._gen_dates(
                self.second, self.penultimate, self.tenor, self.period_adjustment
            )
            self._period_ends = [self.second] + self._period_ends + [self.maturity]
        else:
            self._period_ends = self._gen_dates(
                self.effective, self.maturity, self.tenor, self.period_adjustment
            )

        self._period_starts = [self.effective] + self._period_ends[:-1]
        self._fixing_dates = self._gen_date_adjustments(
            self._period_starts, self.fixing_lag, adjustment="preceding"
        )
        self._payment_dates = self._gen_date_adjustments(
            self._period_ends, Tenor("0D"), adjustment=self.payment_adjustment
        )

    def _create_schedule(self):
        """Private function to merge the lists of periods to a np recarray
        """
        arrays = self._np_dtarrays(
            self._fixing_dates,
            self._period_starts,
            self._period_ends,
            self._payment_dates,
        )
        arrays = (
            arrays
            + (np.zeros(len(self._fixing_dates), dtype=np.float64),)
            + (np.zeros(len(self._fixing_dates), dtype=np.float64),)
        )
        self.periods = np.rec.fromarrays(
            (arrays),
            dtype=[
                ("fixing_date", "datetime64[D]"),
                ("accrual_start", "datetime64[D]"),
                ("accrual_end", "datetime64[D]"),
                ("payment_date", "datetime64[D]"),
                ("cashflow", np.float64),
                ("PV", np.float64),
            ],
        )

        if bool(self.second) ^ bool(self.penultimate):
            raise Exception(
                "If specifying second or penultimate dates," "must select both"
            )

    def _gen_dates(self, effective, maturity, tenor, adjustment):
        """Private function to backward generate a series of dates starting
        from the maturity to the effective.

        Note that the effective date is not returned.
        """
        dates = []
        current = maturity
        counter = 0
        while current > effective:
            dates.append(self.calendar.adjust(current, adjustment))
            current = self.calendar.reverse(current, tenor, "unadjusted")
        return dates[::-1]

    def _gen_date_adjustments(self, dates, tenor, adjustment="unadjusted"):
        """Private function to take a list of dates and adjust each for a number
        of days. It will also adjust each date for a business day adjustment if
        requested.
        """
        adjusted_dates = []
        for date in dates:
            adjusted_date = self.calendar.advance(date, tenor, adjustment)
            adjusted_dates.append(adjusted_date)
        return adjusted_dates

    def _np_dtarrays(self, *args):
        """Converts a series of lists of dates to a tuple of np arrays of
        np.datetimes
        """
        fmt = "%Y-%m-%d"
        arrays = []
        for arg in args:
            arrays.append(
                np.asarray([np.datetime64(date.strftime(fmt)) for date in arg])
            )
        return tuple(arrays)
