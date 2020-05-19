#! /usr/bin/env python
# vim: set fileencoding=utf-8
"""
Testing for USD OIS and LIBOR qb. Note that these curves are the same
as the NY DVC curves (in terms of instruments). Using the 31 December 2019 data
below.
"""
import datetime
import copy
import time

import numpy as np
import scipy.interpolate
import tabulate

import qbootstrapper as qb

curve_effective = datetime.datetime(2019, 12, 31)
effective = datetime.datetime(2020, 1, 3)

# Curves
fedfunds = qb.Curve(curve_effective)
usdlibor = qb.LIBORCurve(curve_effective, discount_curve=fedfunds)

fedfunds_short_conventions = {
    "fixed_period_adjustment": "following",
    "float_period_adjustment": "following",
    "fixed_payment_adjustment": "following",
    "float_payment_adjustment": "following",
    "fixed_basis": "act360",
    "float_basis": "act360",
    "fixed_payment_lag": qb.Tenor("2D"),
    "float_payment_lag": qb.Tenor("2D"),
    "calendar": qb.Calendar("FRB"),
}

fedfunds_conventions = {
    "fixed_tenor": qb.Tenor("6M"),
    "float_tenor": qb.Tenor("3M"),
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
    "fixed_tenor": qb.Tenor("6M"),
    "float_tenor": qb.Tenor("3M"),
    "fixed_basis": "30360",
    "float_basis": "act360",
    "fixed_period_adjustment": "following",
    "float_period_adjustment": "following",
    "fixed_payment_adjustment": "following",
    "float_payment_adjustment": "following",
    "fixed_payment_lag": qb.Tenor("2D"),
    "float_payment_lag": qb.Tenor("2D"),
    "rate_tenor": qb.Tenor("3M"),
    "calendar": qb.Calendar("FRB", "NEWYORK"),
}

fedfunds_cash = qb.instruments.LIBORInstrument(
    curve_effective,
    0.0155,
    qb.Tenor("ON"),
    fedfunds,
    payment_adjustment="following",
    calendar=qb.Calendar("FRB"),
)

fedfunds_swap_onew = qb.OISSwapInstrument(
    effective,
    qb.Tenor("1W"),
    0.0155,
    fedfunds,
    fixed_tenor=qb.Tenor("1W"),
    float_tenor=qb.Tenor("1W"),
    **fedfunds_short_conventions
)

fedfunds_swap_twow = qb.OISSwapInstrument(
    effective,
    qb.Tenor("2W"),
    0.0155,
    fedfunds,
    fixed_tenor=qb.Tenor("2W"),
    float_tenor=qb.Tenor("2W"),
    **fedfunds_short_conventions
)

fedfunds_swap_threew = qb.OISSwapInstrument(
    effective,
    qb.Tenor("3W"),
    0.01551,
    fedfunds,
    fixed_tenor=qb.Tenor("3W"),
    float_tenor=qb.Tenor("3W"),
    **fedfunds_short_conventions
)

fedfunds_short_swaps = [
    (qb.Tenor("1M"), 0.01553),
    (qb.Tenor("2M"), 0.01559),
    (qb.Tenor("3M"), 0.01561),
    (qb.Tenor("4M"), 0.01559),
    (qb.Tenor("5M"), 0.01556),
    (qb.Tenor("6M"), 0.01553),
    (qb.Tenor("9M"), 0.01537),
]

fedfunds_long_swaps = [
    (qb.Tenor("1Y"), 0.01516),
    (qb.Tenor("18M"), 0.01474),
    (qb.Tenor("2Y"), 0.01453),
    (qb.Tenor("3Y"), 0.01449),
    (qb.Tenor("4Y"), 0.01466),
    (qb.Tenor("5Y"), 0.01497),
    (qb.Tenor("6Y"), 0.01532),
    (qb.Tenor("7Y"), 0.01566),
    (qb.Tenor("8Y"), 0.01602),
    (qb.Tenor("9Y"), 0.01635),
    (qb.Tenor("10Y"), 0.01666),
    (qb.Tenor("12Y"), 0.01720),
    (qb.Tenor("15Y"), 0.01777),
    (qb.Tenor("20Y"), 0.01833),
    (qb.Tenor("25Y"), 0.01854),
    (qb.Tenor("30Y"), 0.01859),
    (qb.Tenor("40Y"), 0.01831),
    (qb.Tenor("50Y"), 0.01787),
]

usdlibor_cash_instruments = [(qb.Tenor("3M"), 0.0190838)]

usdlibor_futures_instruments = [
    ("H20", 98.26531667),
    ("M20", 98.31094247),
    ("U20", 98.36682733),
    ("Z20", 98.3829655),
    ("H21", 98.44435054),
    ("M21", 98.44597773),
    ("U21", 98.4428411),
    ("Z21", 98.40493593),
    ("H22", 98.39725544),
    ("M22", 98.3699872),
    ("U22", 98.34777118),
    ("Z22", 98.30552388),
]

usdlibor_swap_instruments = [
    (qb.Tenor("4Y"), 0.01701),
    (qb.Tenor("5Y"), 0.01732),
    (qb.Tenor("6Y"), 0.01762),
    (qb.Tenor("7Y"), 0.01795),
    (qb.Tenor("8Y"), 0.0183),
    (qb.Tenor("9Y"), 0.01864),
    (qb.Tenor("10Y"), 0.01893),
    (qb.Tenor("11Y"), 0.01923),
    (qb.Tenor("12Y"), 0.01948),
    (qb.Tenor("15Y"), 0.02009),
    (qb.Tenor("20Y"), 0.02064),
    (qb.Tenor("25Y"), 0.02084),
    (qb.Tenor("30Y"), 0.0209),
    (qb.Tenor("40Y"), 0.02062),
    (qb.Tenor("50Y"), 0.0202),
]

fedfunds_libor_swap_data = [
    (datetime.datetime(2026, 1, 3), 0.002175),
    (datetime.datetime(2027, 1, 3), 0.002175),
    (datetime.datetime(2030, 1, 3), 0.002175),
    (datetime.datetime(2032, 1, 3), 0.002188),
    (datetime.datetime(2035, 1, 3), 0.0022),
    (datetime.datetime(2040, 1, 3), 0.002213),
    (datetime.datetime(2045, 1, 3), 0.002213),
    (datetime.datetime(2050, 1, 3), 0.002213),
    # (qb.Tenor("6Y"), 0.002175),
    # (qb.Tenor("7Y"), 0.002175),
    # (qb.Tenor("10Y"), 0.002175),
    # (qb.Tenor("12Y"), 0.002188),
    # (qb.Tenor("15Y"), 0.0022),
    # (qb.Tenor("20Y"), 0.002213),
    # (qb.Tenor("25Y"), 0.002213),
    # (qb.Tenor("30Y"), 0.002213),
]

# Fed funds build
fedfunds.add_instrument(fedfunds_cash)
fedfunds.add_instrument(fedfunds_swap_onew)
fedfunds.add_instrument(fedfunds_swap_twow)
fedfunds.add_instrument(fedfunds_swap_threew)

for (tenor, rate) in fedfunds_short_swaps:
    inst = qb.OISSwapInstrument(
        effective,
        tenor,
        rate,
        fedfunds,
        fixed_tenor=tenor,
        float_tenor=tenor,
        **fedfunds_short_conventions
    )
    fedfunds.add_instrument(inst)

for (tenor, rate) in fedfunds_long_swaps:
    inst = qb.OISSwapInstrument(
        effective, tenor, rate, fedfunds, **fedfunds_conventions
    )
    fedfunds.add_instrument(inst)


# USD LIBOR build
for (tenor, rate) in usdlibor_cash_instruments:
    inst = qb.LIBORInstrument(
        effective,
        rate,
        tenor,
        usdlibor,
        payment_adjustment="following",
        fixing_lag=qb.Tenor("2D"),
    )
    usdlibor.add_instrument(inst)

for (code, price) in usdlibor_futures_instruments:
    inst = qb.FuturesInstrumentByIMMCode(code, price, usdlibor)
    usdlibor.add_instrument(inst)

for (maturity, rate) in usdlibor_swap_instruments:
    inst = qb.LIBORSwapInstrument(
        effective, maturity, rate, usdlibor, **usdlibor_conventions
    )
    usdlibor.add_instrument(inst)

# Simultaneous stripped LIBOR and OIS curves
# Short FedFunds curve
fedfunds_short = qb.Curve(curve_effective)

fedfunds_short_short_instruments = [
    fedfunds_cash,
    fedfunds_swap_onew,
    fedfunds_swap_twow,
    fedfunds_swap_threew,
]

for inst in fedfunds_short_short_instruments:
    new_inst = copy.deepcopy(inst)
    new_inst.curve = fedfunds_short
    fedfunds_short.add_instrument(new_inst)

for (tenor, rate) in fedfunds_short_swaps:
    inst = qb.OISSwapInstrument(
        effective,
        tenor,
        rate,
        fedfunds_short,
        fixed_tenor=tenor,
        float_tenor=tenor,
        **fedfunds_short_conventions
    )
    fedfunds_short.add_instrument(inst)

for (maturity, rate) in fedfunds_long_swaps[:6]:
    inst = qb.OISSwapInstrument(
        effective, maturity, rate, fedfunds_short, **fedfunds_conventions
    )
    fedfunds_short.add_instrument(inst)

# Short USD LIBOR curve
usdlibor_short = qb.LIBORCurve(curve_effective, discount_curve=fedfunds_short)
for (tenor, rate) in usdlibor_cash_instruments:
    inst = qb.LIBORInstrument(
        effective, rate, tenor, usdlibor_short, payment_adjustment="following",
    )
    usdlibor_short.add_instrument(inst)

for (code, price) in usdlibor_futures_instruments:
    inst = qb.FuturesInstrumentByIMMCode(code, price, usdlibor_short)
    usdlibor_short.add_instrument(inst)

for (maturity, rate) in usdlibor_swap_instruments[:2]:
    inst = qb.LIBORSwapInstrument(
        effective, maturity, rate, usdlibor_short, **usdlibor_conventions
    )
    usdlibor_short.add_instrument(inst)

# Simultaneous curve instruments
fedfunds_libor = qb.SimultaneousStrippedCurve(
    curve_effective, fedfunds_short, usdlibor_short
)
fedfunds_libor_libor_swaps = usdlibor_swap_instruments[2:4]
fedfunds_libor_libor_swaps.extend([usdlibor_swap_instruments[6]])
fedfunds_libor_libor_swaps.extend(usdlibor_swap_instruments[8:])

for idx, (maturity, rate) in enumerate(fedfunds_libor_swap_data):
    ois_inst = qb.AverageIndexBasisSwapInstrument(
        effective, maturity, fedfunds_libor, leg_one_spread=rate
    )
    libor_inst = qb.LIBORSwapInstrument(
        effective,
        fedfunds_libor_libor_swaps[idx][0],
        fedfunds_libor_libor_swaps[idx][1],
        usdlibor,
        **usdlibor_conventions
    )
    instrument_pair = qb.SimultaneousInstrument(ois_inst, libor_inst, fedfunds_libor)
    fedfunds_libor.add_instrument(instrument_pair)


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
                        (
                            curve_effective + datetime.timedelta(days=int(serial))
                        ).timetuple()
                    )
                )
            except:
                pass

    return scipy.interpolate.PchipInterpolator(np.array(dates), np.array(dfs))


def as_percent(num):
    return "{0:.5f}".format(num * 100)


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
                "{0:.4f}".format(((dvc_zr - qb_zeros[i]) * 10000.0)),
            ]
        )

    print(tabulate.tabulate(records, headers=["Date", "DVC ZR", "QB ZR", "Difference"]))


def main():

    dvc_ois = load_curve("/home/kevindkeogh/Downloads/OIS123119USD.crv")
    dvc_3ml = load_curve("/home/kevindkeogh/Downloads/3MLOIS123119USD.crv")

    print("FedFunds")
    fedfunds.build()
    compare_curves(dvc_ois, fedfunds)
    print("")
    print("3M LIBOR")
    usdlibor.build()
    compare_curves(dvc_3ml, fedfunds_libor.projection_curve)
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
