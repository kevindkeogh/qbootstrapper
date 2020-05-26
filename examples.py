#! /usr/bin/env python
# vim: set fileencoding=utf-8
"""
Testing for USD OIS and LIBOR qb. Note that these curves are the same
as the NY DVC curves (in terms of instruments). Using the 31 December 2019 data
below.
"""
import datetime
import time

import numpy as np
import scipy.interpolate
import tabulate

import qbootstrapper as qb


fedfunds_conventions = {
    "payment_adjustment": "following",
    "calendar": qb.Calendar("FRB"),
}

fedfunds_swap_conventions = {
    "fixed_tenor": qb.Tenor("1Y"),
    "float_tenor": qb.Tenor("1Y"),
    "fixed_basis": "act360",
    "float_basis": "act360",
    "fixed_period_adjustment": "following",
    "float_period_adjustment": "following",
    "fixed_payment_adjustment": "following",
    "float_payment_adjustment": "following",
    "fixed_payment_lag": qb.Tenor("2D"),
    "float_payment_lag": qb.Tenor("2D"),
    "calendar": qb.Calendar("FRB"),
}

usdlibor_conventions = {
    "payment_adjustment": "following",
    "fixing_lag": qb.Tenor("2D"),
}

usdlibor_futures_conventions = {
    "tenor": qb.Tenor("3M"),
    "basis": "act360",
    "calendar": qb.Calendar("NEWYORK"),
}

usdlibor_swap_conventions = {
    "fixed_tenor": qb.Tenor("6M"),
    "float_tenor": qb.Tenor("3M"),
    "fixed_basis": "30360",
    "float_basis": "act360",
    "fixed_period_adjustment": "following",
    "float_period_adjustment": "following",
    "fixed_payment_adjustment": "following",
    "float_payment_adjustment": "following",
    "fixed_payment_lag": qb.Tenor("0D"),
    "float_payment_lag": qb.Tenor("0D"),
    "rate_tenor": qb.Tenor("3M"),
    "calendar": qb.Calendar("FRB", "NEWYORK"),
}

fedfunds_libor_conventions = {
    # leg_one == OIS
    # leg_two == LIBOR
    "leg_one_basis": "act360",
    "leg_two_basis": "act360",
    "leg_one_tenor": qb.Tenor("3M"),
    "leg_two_tenor": qb.Tenor("3M"),
    "leg_one_period_adjustment": "following",
    "leg_two_period_adjustment": "following",
    "leg_one_payment_adjustment": "following",
    "leg_two_payment_adjustment": "following",
    "leg_one_payment_lag": qb.Tenor("2D"),
    "leg_two_payment_lag": qb.Tenor("2D"),
    "leg_two_fixing_lag": qb.Tenor("2D"),
    "leg_one_rate_tenor": qb.Tenor("ON"),
    "leg_one_rate_basis": "act360",
    "leg_two_rate_tenor": qb.Tenor("3M"),
    "leg_two_rate_basis": "act360",
    "calendar": qb.Calendar("FRB", "NEWYORK"),
}

sofr_conventions = {
    "payment_adjustment": "following",
    "calendar": qb.Calendar("FRB"),
}

sofr_futures_conventions = {
    "tenor": qb.Tenor("3M"),
    "basis": "act360",
    "calendar": qb.Calendar("FRB", "NEWYORK"),
}

sofr_fedfunds_conventions = {
    # leg_one == SOFR
    # leg_two == OIS
    "leg_one_basis": "act360",
    "leg_two_basis": "act360",
    "leg_one_tenor": qb.Tenor("3M"),
    "leg_two_tenor": qb.Tenor("3M"),
    "leg_one_period_adjustment": "following",
    "leg_two_period_adjustment": "following",
    "leg_one_payment_adjustment": "following",
    "leg_two_payment_adjustment": "following",
    "leg_one_payment_lag": qb.Tenor("2D"),
    "leg_two_payment_lag": qb.Tenor("2D"),
    "leg_one_rate_tenor": qb.Tenor("ON"),
    "leg_one_rate_basis": "act360",
    "leg_two_rate_tenor": qb.Tenor("ON"),
    "leg_two_rate_basis": "act360",
    "calendar": qb.Calendar("FRB"),
}

fedfunds_instruments = [
    (qb.Tenor("ON"), 0.0155, "CASH", fedfunds_conventions),
    (qb.Tenor("1W"), 0.0155, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("2W"), 0.0155, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("3W"), 0.01551, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("1M"), 0.01553, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("2M"), 0.01559, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("3M"), 0.01561, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("4M"), 0.01559, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("5M"), 0.01556, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("6M"), 0.01553, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("9M"), 0.01537, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("1Y"), 0.01516, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("18M"), 0.01474, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("2Y"), 0.01453, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("3Y"), 0.01449, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("4Y"), 0.01466, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("5Y"), 0.01497, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("6Y"), 0.01532, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("7Y"), 0.01566, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("8Y"), 0.01602, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("9Y"), 0.01635, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("10Y"), 0.01666, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("12Y"), 0.01720, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("15Y"), 0.01777, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("20Y"), 0.01833, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("25Y"), 0.01854, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("30Y"), 0.01859, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("40Y"), 0.01831, "SWAP", fedfunds_swap_conventions),
    (qb.Tenor("50Y"), 0.01787, "SWAP", fedfunds_swap_conventions),
]

usdlibor_instruments = [
    # This fixes the short end of the USD LIBOR curve. It's very unclear to
    # me how numerix comes up with this number. Its higher than 3M LIBOR, but
    # expires earlier, which seems... unlikely?
    # (datetime.datetime(2020, 3, 18), 0.0192704, "CASH", usdlibor_conventions),
    (qb.Tenor("3M"), 0.0190838, "CASH", usdlibor_conventions),
    ("H20", 98.26531667, "FUTURES", usdlibor_futures_conventions),
    ("M20", 98.31094247, "FUTURES", usdlibor_futures_conventions),
    ("U20", 98.36682733, "FUTURES", usdlibor_futures_conventions),
    ("Z20", 98.3829655, "FUTURES", usdlibor_futures_conventions),
    ("H21", 98.44435054, "FUTURES", usdlibor_futures_conventions),
    ("M21", 98.44597773, "FUTURES", usdlibor_futures_conventions),
    ("U21", 98.4428411, "FUTURES", usdlibor_futures_conventions),
    ("Z21", 98.40493593, "FUTURES", usdlibor_futures_conventions),
    ("H22", 98.39725544, "FUTURES", usdlibor_futures_conventions),
    ("M22", 98.3699872, "FUTURES", usdlibor_futures_conventions),
    ("U22", 98.34777118, "FUTURES", usdlibor_futures_conventions),
    ("Z22", 98.30552388, "FUTURES", usdlibor_futures_conventions),
    (qb.Tenor("4Y"), 0.01701, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("5Y"), 0.01732, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("6Y"), 0.01762, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("7Y"), 0.01795, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("8Y"), 0.0183, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("9Y"), 0.01864, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("10Y"), 0.01893, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("11Y"), 0.01923, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("12Y"), 0.01948, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("15Y"), 0.02009, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("20Y"), 0.02064, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("25Y"), 0.02084, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("30Y"), 0.0209, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("40Y"), 0.02062, "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("50Y"), 0.0202, "SWAP", usdlibor_swap_conventions),
]

fedfunds_libor_instruments = [
    (qb.Tenor("6Y"), 0.002175, "OIS-LIBOR-SWAP", {}),
    (qb.Tenor("7Y"), 0.002175, "OIS-LIBOR-SWAP", {}),
    (qb.Tenor("10Y"), 0.002175, "OIS-LIBOR-SWAP", {}),
    (qb.Tenor("12Y"), 0.002188, "OIS-LIBOR-SWAP", {}),
    (qb.Tenor("15Y"), 0.0022, "OIS-LIBOR-SWAP", {}),
    (qb.Tenor("20Y"), 0.002213, "OIS-LIBOR-SWAP", {}),
    (qb.Tenor("25Y"), 0.002213, "OIS-LIBOR-SWAP", {}),
    (qb.Tenor("30Y"), 0.002213, "OIS-LIBOR-SWAP", {}),
]

sofr_fedfunds_instruments = [
    (qb.Tenor("ON"), 0.0155, "CASH", sofr_conventions),
    ("Z19", 98.44, "FUTURES", sofr_futures_conventions),
    ("H20", 98.455, "FUTURES", sofr_futures_conventions),
    ("M20", 98.495, "FUTURES", sofr_futures_conventions),
    ("U20", 98.560, "FUTURES", sofr_futures_conventions),
    ("Z20", 98.610, "FUTURES", sofr_futures_conventions),
    ("H21", 98.625, "FUTURES", sofr_futures_conventions),
    (qb.Tenor("2Y"), -0.0002542, "SOFR-OIS-SWAP", sofr_fedfunds_conventions),
    (qb.Tenor("3Y"), -0.0001957, "SOFR-OIS-SWAP", sofr_fedfunds_conventions),
    (qb.Tenor("4Y"), -0.0002566, "SOFR-OIS-SWAP", sofr_fedfunds_conventions),
    (qb.Tenor("5Y"), -0.0002387, "SOFR-OIS-SWAP", sofr_fedfunds_conventions),
]

curve_date = datetime.datetime(2019, 12, 31)
effective = qb.Calendar("NEWYORK").adjust(curve_date + qb.Tenor("3D"), "following")

# Curves
fedfunds = qb.Curve(curve_date)
usdlibor = qb.LIBORCurve(curve_date, discount_curve=fedfunds)

# Fed funds build
for (tenor, rate, kind, convention) in fedfunds_instruments:
    if kind.upper() == "CASH":
        inst = qb.instruments.LIBORInstrument(
            curve_date, rate, tenor, fedfunds, **convention
        )
    elif kind.upper() == "SWAP":
        inst = qb.OISSwapInstrument(effective, tenor, rate, fedfunds, **convention)
    else:
        raise Exception("Instrument type {} not recognized".format(kind))

    fedfunds.add_instrument(inst)


# USD LIBOR build
for (tenor, rate, kind, convention) in usdlibor_instruments:
    if kind.upper() == "CASH":
        inst = qb.LIBORInstrument(effective, rate, tenor, usdlibor, **convention)
    elif kind.upper() == "FUTURES":
        inst = qb.FuturesInstrumentByIMMCode(tenor, rate, usdlibor, **convention)
    elif kind.upper() == "SWAP":
        inst = qb.LIBORSwapInstrument(effective, tenor, rate, usdlibor, **convention)
    else:
        raise Exception("Instrument type {} not recognized".format(kind))

    usdlibor.add_instrument(inst)

# Simultaneous stripped LIBOR and OIS curves
# Short FedFunds curve
fedfunds_short = qb.Curve(curve_date)
for (tenor, rate, kind, convention) in fedfunds_instruments:
    if kind.upper() == "CASH":
        inst = qb.instruments.LIBORInstrument(
            curve_date, rate, tenor, fedfunds_short, **convention
        )
    elif kind.upper() == "SWAP":
        inst = qb.OISSwapInstrument(
            effective, tenor, rate, fedfunds_short, **convention
        )
    else:
        raise Exception("Instrument type {} not recognized".format(kind))

    if inst.maturity >= (curve_date + fedfunds_libor_instruments[0][0]):
        break

    fedfunds_short.add_instrument(inst)

# Short USD LIBOR curve
usdlibor_short = qb.LIBORCurve(curve_date, discount_curve=fedfunds_short)
for (tenor, rate, kind, convention) in usdlibor_instruments:
    if kind.upper() == "CASH":
        inst = qb.LIBORInstrument(effective, rate, tenor, usdlibor_short, **convention)
    elif kind.upper() == "FUTURES":
        inst = qb.FuturesInstrumentByIMMCode(tenor, rate, usdlibor_short, **convention)
    elif kind.upper() == "SWAP":
        inst = qb.LIBORSwapInstrument(
            effective, tenor, rate, usdlibor_short, **convention
        )
    else:
        raise Exception("Instrument type {} not recognized".format(kind))

    if inst.maturity >= (curve_date + fedfunds_libor_instruments[0][0]):
        break

    usdlibor_short.add_instrument(inst)

# Simultaneous curve instruments
fedfunds_libor = qb.SimultaneousStrippedCurve(
    curve_date, fedfunds_short, usdlibor_short
)

for (tenor, rate, kind, convention) in fedfunds_libor_instruments:
    if kind.upper() == "OIS-LIBOR-SWAP":
        ibor_rate = None

        for idx, inst in enumerate(usdlibor_instruments):
            try:
                if inst[0].name == tenor.name:
                    ibor_rate = inst[1]
                    break
            except AttributeError:
                pass
        else:
            continue

        ois_inst = qb.AverageIndexBasisSwapInstrument(
            effective,
            tenor,
            fedfunds_libor,
            leg_one_spread=rate,
            **fedfunds_libor_conventions
        )

        libor_inst = qb.LIBORSwapInstrument(
            effective, tenor, ibor_rate, usdlibor, **usdlibor_swap_conventions
        )

        instrument_pair = qb.SimultaneousInstrument(
            ois_inst, libor_inst, fedfunds_libor
        )

        fedfunds_libor.add_instrument(instrument_pair)

    else:
        raise Exception("Instrument type {} not recognized".format(kind))


def load_curve(filename):
    dates = []
    dfs = []
    with open(filename, "r", newline="") as fh:
        for row in fh:
            try:
                els = row.strip().split(" ")
                serial = els[0]
                df = els[-1]
                dfs.append(np.log(float(df)))
                dates.append(
                    time.mktime(
                        (curve_date + datetime.timedelta(days=int(serial))).timetuple()
                    )
                )
            except:  # noqa
                pass

    return scipy.interpolate.PchipInterpolator(np.array(dates), np.array(dfs))


def as_percent(num):
    return "{0:.5f}%".format(num * 100)


def compare_curves(dvc_curve, qb_curve):
    records = []
    dates, qb_zeros = qb_curve.zeros(True, False)
    for i, maturity in enumerate(dates):
        years = ((maturity - dates[0]) / np.timedelta64(1, "D")) / 365.0
        if i == 0:
            df = 0
            dvc_zr = 0
        else:
            df = dvc_curve(time.mktime(maturity.astype(object).timetuple()))
            dvc_zr = -df / years
        records.append(
            [
                maturity,
                as_percent(dvc_zr),
                as_percent(qb_zeros[i]),
                "{:.4f}".format(((dvc_zr - qb_zeros[i]) * 10000.0)),
            ]
        )

    print(
        tabulate.tabulate(
            records,
            headers=["Date", "DVC ZR", "QB ZR", "Difference (bps)"],
            floatfmt=".4f",
        )
    )


def main():

    dvc_ois = load_curve("/home/kevindkeogh/Downloads/OIS123119USD.crv")
    dvc_3ml = load_curve("/home/kevindkeogh/Downloads/3MLOIS123119USD.crv")

    print("")
    print("Independently bootstrapped")
    print("    FedFunds")
    fedfunds.build()
    compare_curves(dvc_ois, fedfunds)
    print("")
    print("    3M LIBOR")
    usdlibor.build()
    compare_curves(dvc_3ml, usdlibor)
    print("")
    print("Simultaneously bootstrapped")
    fedfunds_libor.build()
    print("")
    print("    FedFunds")
    compare_curves(dvc_ois, fedfunds_libor.discount_curve)
    print("")
    print("    3M LIBOR")
    compare_curves(dvc_3ml, fedfunds_libor.projection_curve)


if __name__ == "__main__":
    main()
