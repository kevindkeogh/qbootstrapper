#! /usr/bin/env python
# vim: set fileencoding=utf-8
"""
Bulk testing harness for USD OIS and LIBOR qb.
"""
import csv
import datetime
import time

import numpy as np
import requests
import scipy.interpolate
import tabulate

import qbootstrapper as qb


fedfunds_conventions = {
    "payment_adjustment": "following",
    "calendar": qb.Calendar("FRB"),
    "spot_lag": qb.Tenor("0BD"),
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
    "spot_lag": qb.Tenor("2BD"),
}

usdlibor_conventions = {
    "payment_adjustment": "following",
    "calendar": qb.Calendar("NEWYORK"),
    "spot_lag": qb.Tenor("2BD"),
}

usdlibor_futures_conventions = {
    "tenor": qb.Tenor("3M"),
    "basis": "act360",
    "calendar": qb.Calendar("NEWYORK"),
    "spot_lag": qb.Tenor("0BD"),
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
    "spot_lag": qb.Tenor("2BD"),
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
    "spot_lag": qb.Tenor("2BD"),
}

sofr_conventions = {
    "payment_adjustment": "following",
    "calendar": qb.Calendar("FRB"),
    "spot_lag": qb.Tenor("0BD"),
}

sofr_futures_conventions = {
    "tenor": qb.Tenor("3M"),
    "basis": "act360",
    "calendar": qb.Calendar("FRB", "NEWYORK"),
    "spot_lag": qb.Tenor("0BD"),
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
    "spot_lag": qb.Tenor("2BD"),
}

fedfunds_instruments = [
    (qb.Tenor("ON"), "IR.USD-FEDFUNDS.CASH-ON.MID", "CASH", fedfunds_conventions),
    (
        qb.Tenor("1W"),
        "IR.USD-FEDFUNDS-ON.SWAP-1W.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("2W"),
        "IR.USD-FEDFUNDS-ON.SWAP-2W.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("3W"),
        "IR.USD-FEDFUNDS-ON.SWAP-3W.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("1M"),
        "IR.USD-FEDFUNDS-ON.SWAP-1M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("2M"),
        "IR.USD-FEDFUNDS-ON.SWAP-2M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("3M"),
        "IR.USD-FEDFUNDS-ON.SWAP-3M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("4M"),
        "IR.USD-FEDFUNDS-ON.SWAP-4M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("5M"),
        "IR.USD-FEDFUNDS-ON.SWAP-5M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("6M"),
        "IR.USD-FEDFUNDS-ON.SWAP-6M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("9M"),
        "IR.USD-FEDFUNDS-ON.SWAP-9M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("1Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-12M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("18M"),
        "IR.USD-FEDFUNDS-ON.SWAP-18M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("2Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-24M.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("3Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-3Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("4Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-4Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("5Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-5Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("6Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-6Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("7Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-7Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("8Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-8Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("9Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-9Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("10Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-10Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("12Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-12Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("15Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-15Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("20Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-20Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("25Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-25Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("30Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-30Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("40Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-40Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
    (
        qb.Tenor("50Y"),
        "IR.USD-FEDFUNDS-ON.SWAP-50Y.MID",
        "SWAP",
        fedfunds_swap_conventions,
    ),
]

usdlibor_instruments = [
    (qb.Tenor("3M"), "IR.USD-LIBOR.CASH-3M.MID", "CASH", usdlibor_conventions),
    (1, 1, "FUTURES", usdlibor_futures_conventions),
    (2, 2, "FUTURES", usdlibor_futures_conventions),
    (3, 3, "FUTURES", usdlibor_futures_conventions),
    (4, 4, "FUTURES", usdlibor_futures_conventions),
    (5, 5, "FUTURES", usdlibor_futures_conventions),
    (6, 6, "FUTURES", usdlibor_futures_conventions),
    (7, 7, "FUTURES", usdlibor_futures_conventions),
    (8, 8, "FUTURES", usdlibor_futures_conventions),
    (9, 9, "FUTURES", usdlibor_futures_conventions),
    (10, 10, "FUTURES", usdlibor_futures_conventions),
    (11, 11, "FUTURES", usdlibor_futures_conventions),
    (12, 12, "FUTURES", usdlibor_futures_conventions),
    (qb.Tenor("4Y"), "IR.USD-LIBOR-3M.SWAP-4Y.MID", "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("5Y"), "IR.USD-LIBOR-3M.SWAP-5Y.MID", "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("6Y"), "IR.USD-LIBOR-3M.SWAP-6Y.MID", "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("7Y"), "IR.USD-LIBOR-3M.SWAP-7Y.MID", "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("8Y"), "IR.USD-LIBOR-3M.SWAP-8Y.MID", "SWAP", usdlibor_swap_conventions),
    (qb.Tenor("9Y"), "IR.USD-LIBOR-3M.SWAP-9Y.MID", "SWAP", usdlibor_swap_conventions),
    (
        qb.Tenor("10Y"),
        "IR.USD-LIBOR-3M.SWAP-10Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
    (
        qb.Tenor("11Y"),
        "IR.USD-LIBOR-3M.SWAP-11Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
    (
        qb.Tenor("12Y"),
        "IR.USD-LIBOR-3M.SWAP-12Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
    (
        qb.Tenor("15Y"),
        "IR.USD-LIBOR-3M.SWAP-15Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
    (
        qb.Tenor("20Y"),
        "IR.USD-LIBOR-3M.SWAP-20Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
    (
        qb.Tenor("25Y"),
        "IR.USD-LIBOR-3M.SWAP-25Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
    (
        qb.Tenor("30Y"),
        "IR.USD-LIBOR-3M.SWAP-30Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
    (
        qb.Tenor("40Y"),
        "IR.USD-LIBOR-3M.SWAP-40Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
    (
        qb.Tenor("50Y"),
        "IR.USD-LIBOR-3M.SWAP-50Y.MID",
        "SWAP",
        usdlibor_swap_conventions,
    ),
]

fedfunds_libor_instruments = [
    (
        qb.Tenor("6Y"),
        "IR.USD-LIBOR-3M/USD-FEDFUNDS-ON.BASIS-6Y.MID",
        "OIS-LIBOR-SWAP",
        {},
    ),
    (
        qb.Tenor("7Y"),
        "IR.USD-LIBOR-3M/USD-FEDFUNDS-ON.BASIS-7Y.MID",
        "OIS-LIBOR-SWAP",
        {},
    ),
    (
        qb.Tenor("10Y"),
        "IR.USD-LIBOR-3M/USD-FEDFUNDS-ON.BASIS-10Y.MID",
        "OIS-LIBOR-SWAP",
        {},
    ),
    (
        qb.Tenor("12Y"),
        "IR.USD-LIBOR-3M/USD-FEDFUNDS-ON.BASIS-12Y.MID",
        "OIS-LIBOR-SWAP",
        {},
    ),
    (
        qb.Tenor("15Y"),
        "IR.USD-LIBOR-3M/USD-FEDFUNDS-ON.BASIS-15Y.MID",
        "OIS-LIBOR-SWAP",
        {},
    ),
    (
        qb.Tenor("20Y"),
        "IR.USD-LIBOR-3M/USD-FEDFUNDS-ON.BASIS-20Y.MID",
        "OIS-LIBOR-SWAP",
        {},
    ),
    (
        qb.Tenor("25Y"),
        "IR.USD-LIBOR-3M/USD-FEDFUNDS-ON.BASIS-25Y.MID",
        "OIS-LIBOR-SWAP",
        {},
    ),
    (
        qb.Tenor("30Y"),
        "IR.USD-LIBOR-3M/USD-FEDFUNDS-ON.BASIS-30Y.MID",
        "OIS-LIBOR-SWAP",
        {},
    ),
]

sofr_instruments = [
    (qb.Tenor("ON"), None, "CASH", sofr_conventions),
    (1, None, "COMPOUND-FUTURES", sofr_futures_conventions),
    (2, None, "COMPOUND-FUTURES", sofr_futures_conventions),
    (3, None, "COMPOUND-FUTURES", sofr_futures_conventions),
    (4, None, "COMPOUND-FUTURES", sofr_futures_conventions),
    (5, None, "COMPOUND-FUTURES", sofr_futures_conventions),
    (6, None, "COMPOUND-FUTURES", sofr_futures_conventions),
]

sofr_fedfunds_instruments = [
    (qb.Tenor("2Y"), None, "SOFR-OIS-SWAP", sofr_fedfunds_conventions),
    (qb.Tenor("3Y"), None, "SOFR-OIS-SWAP", sofr_fedfunds_conventions),
    (qb.Tenor("4Y"), None, "SOFR-OIS-SWAP", sofr_fedfunds_conventions),
    (qb.Tenor("5Y"), None, "SOFR-OIS-SWAP", sofr_fedfunds_conventions),
]


def create_sofr_fixings():
    sofr = qb.Fixings("SOFR")
    with open("sofr-fixings.csv", "r") as fh:
        reader = csv.reader(fh)
        next(reader)
        for row in reader:
            sofr.add_fixings([[row[0], row[1]]], scale=100)

    return sofr


def get_rate(code, date):
    dt = date.strftime("%Y-%m-%d")
    url = f"https://data.derivatives.center/market-data/market_data.json?key__exact={code}&date__exact={dt}"
    req = requests.get(url, auth=("dvc", "data"))
    try:
        return req.json()["rows"][0][2]
    except:
        print("An error occurred getting data")
        print(url)
        print(req.json())


def next_imm_code(code):
    letter = code[0]
    year = code[1:]
    if letter == "H":
        next_code = "M"
    elif letter == "M":
        next_code = "U"
    elif letter == "U":
        next_code = "Z"
    elif letter == "Z":
        next_code = "H"
    else:
        raise Exception(f"Code not recogized {code}")

    if next_code == "H":
        return next_code + str(int(year) + 1)
    else:
        return next_code + year


def next_imm_date(date):
    if type(date) == datetime.datetime:
        date = date.date()
    year = date.year
    if date.month % 3:
        month = date.month + (3 - (date.month % 3))
    else:
        month = date.month
    imm = datetime.date(year, month, 15)
    w = imm.weekday()
    if w != 2:
        imm = imm.replace(day=(15 + (2 - w) % 7))

    if date > imm:
        if date.month == 12:
            imm = imm.replace(year=imm.year + 1, month=1)
        else:
            imm = imm.replace(month=imm.month + 1)
        return next_imm_date(imm)
    else:
        letter = {3: "H", 6: "M", 9: "U", 12: "Z"}[imm.month]
        year = str(imm.year)[-2:]
        return letter + year


def load_curve(filename, curve_date):
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


def build_curves(curve_date):
    # Curves
    fedfunds = qb.OISCurve(curve_date)
    usdlibor = qb.LIBORCurve(curve_date, discount_curve=fedfunds)

    fedfunds_short = qb.OISCurve(curve_date)
    usdlibor_short = qb.LIBORCurve(curve_date, discount_curve=fedfunds_short)
    fedfunds_libor = qb.SimultaneousStrippedCurve(
        curve_date, fedfunds_short, usdlibor_short, fedfunds_short
    )

    # sofr_short = qb.OISCurve(curve_date)
    # fedfunds_sofr_short = qb.Curve(curve_date)
    # sofr_fedfunds = qb.SimultaneousStrippedCurve(
    # curve_date, sofr_short, fedfunds_sofr_short, fedfunds_sofr_short
    # )

    # Fed funds build
    for (tenor, code, kind, convention) in fedfunds_instruments:
        rate = get_rate(code, curve_date)
        if kind.upper() == "CASH":
            inst = qb.instruments.LIBORInstrument(
                curve_date, rate, tenor, fedfunds, **convention
            )
        elif kind.upper() == "SWAP":
            inst = qb.OISSwapInstrument(curve_date, tenor, rate, fedfunds, **convention)
        else:
            raise Exception("Instrument type {} not recognized".format(kind))

        fedfunds.add_instrument(inst)

    # USD LIBOR build
    for (tenor, code, kind, convention) in usdlibor_instruments:
        if kind.upper() == "CASH":
            rate = get_rate(code, curve_date)
            inst = qb.LIBORInstrument(curve_date, rate, tenor, usdlibor, **convention)
        elif kind.upper() == "FUTURES":
            imm = next_imm_date(curve_date)
            for i in range(code - 1):
                imm = next_imm_code(imm)
            # This should be included, but the DVC curves have been built
            # incorrectly for the last 2Y
            # if (curve_date.month % 3):
            #     imm = next_imm_code(imm)
            # FIXME
            rate = 99  # get_futures(code, curve_date)
            inst = qb.FuturesInstrumentByIMMCode(imm, rate, usdlibor, **convention)
        elif kind.upper() == "SWAP":
            rate = get_rate(code, curve_date)
            inst = qb.LIBORSwapInstrument(
                curve_date, tenor, rate, usdlibor, **convention
            )
        else:
            raise Exception("Instrument type {} not recognized".format(kind))

        usdlibor.add_instrument(inst)

    # Simultaneous stripped LIBOR and OIS curves
    # Short FedFunds curve
    for (tenor, code, kind, convention) in fedfunds_instruments:
        rate = get_rate(code, curve_date)
        if kind.upper() == "CASH":
            inst = qb.instruments.LIBORInstrument(
                curve_date, rate, tenor, fedfunds_short, **convention
            )
        elif kind.upper() == "SWAP":
            inst = qb.OISSwapInstrument(
                curve_date, tenor, rate, fedfunds_short, **convention
            )
        else:
            raise Exception("Instrument type {} not recognized".format(kind))

        if inst.maturity >= (curve_date + fedfunds_libor_instruments[0][0]):
            break

        fedfunds_short.add_instrument(inst)

    # Short USD LIBOR curve
    for (tenor, code, kind, convention) in usdlibor_instruments:
        if kind.upper() == "CASH":
            rate = get_rate(code, curve_date)
            inst = qb.LIBORInstrument(
                curve_date, rate, tenor, usdlibor_short, **convention
            )
        elif kind.upper() == "FUTURES":
            imm = next_imm_date(curve_date)
            for i in range(code):
                imm = next_imm_code(imm)
            # if (curve_date.month % 3):
            #     imm = next_imm_code(imm)
            # FIXME
            rate = 99  # get_futures(code, curve_date)
            inst = qb.FuturesInstrumentByIMMCode(
                imm, rate, usdlibor_short, **convention
            )
        elif kind.upper() == "SWAP":
            rate = get_rate(code, curve_date)
            inst = qb.LIBORSwapInstrument(
                curve_date, tenor, rate, usdlibor_short, **convention
            )
        else:
            raise Exception("Instrument type {} not recognized".format(kind))

        if inst.maturity >= (curve_date + fedfunds_libor_instruments[0][0]):
            break

        usdlibor_short.add_instrument(inst)

    # Simultaneous curve instruments
    for (tenor, code, kind, convention) in fedfunds_libor_instruments:
        rate = get_rate(code, curve_date)
        if kind.upper() == "OIS-LIBOR-SWAP":
            ibor_rate = None

            for idx, inst in enumerate(usdlibor_instruments):
                try:
                    if inst[0].name == tenor.name:
                        ibor_rate = get_rate(inst[1], curve_date)
                        break
                except AttributeError:
                    pass
            else:
                continue

            ois_inst = qb.AverageIndexBasisSwapInstrument(
                curve_date,
                tenor,
                fedfunds_libor,
                leg_one_spread=rate,
                **fedfunds_libor_conventions,
            )

            libor_inst = qb.LIBORSwapInstrument(
                curve_date,
                tenor,
                ibor_rate,
                fedfunds_libor,
                **usdlibor_swap_conventions,
            )

            instrument_pair = qb.SimultaneousInstrument(
                ois_inst, libor_inst, fedfunds_libor
            )

            fedfunds_libor.add_instrument(instrument_pair)

        else:
            raise Exception("Instrument type {} not recognized".format(kind))

    # Simultaneous stripped OIS and SOFR curves
    # Short FedFunds curve
    # for (tenor, code, kind, convention) in fedfunds_instruments:
    #     rate = get_rate(code, curve_date)
    #     if kind.upper() == "CASH":
    #         inst = qb.instruments.LIBORInstrument(
    #             curve_date, rate, tenor, fedfunds_sofr_short, **convention
    #         )
    #     elif kind.upper() == "SWAP":
    #         inst = qb.OISSwapInstrument(
    #             curve_date, tenor, rate, fedfunds_sofr_short, **convention
    #         )
    #     else:
    #         raise Exception("Instrument type {} not recognized".format(kind))

    #     if inst.maturity >= (curve_date + sofr_fedfunds_instruments[0][0]):
    #         break

    #     fedfunds_sofr_short.add_instrument(inst)

    # Short SOFR curve
    #     sofr_fixings = create_sofr_fixings()
    #     for (tenor, rate, kind, convention) in sofr_instruments:
    #         if kind.upper() == "CASH":
    #             inst = qb.LIBORInstrument(curve_date, rate, tenor, sofr_short, **convention)
    #         elif kind.upper() == "COMPOUND-FUTURES":
    #             inst = qb.CompoundFuturesInstrumentByIMMCode(
    #                 tenor, rate, sofr_short, fixings=sofr_fixings, **convention
    #             )
    #         else:
    #             raise Exception("Instrument type {} not recognized".format(kind))
    #
    #         if inst.maturity >= (curve_date + sofr_fedfunds_instruments[0][0]):
    #             break
    #
    #         sofr_short.add_instrument(inst)

    # Simultaneous curve instruments
    # for (tenor, rate, kind, convention) in sofr_fedfunds_instruments:
    #     if kind.upper() == "SOFR-OIS-SWAP":
    #         ois_rate = None

    #         for idx, inst in enumerate(fedfunds_instruments):
    #             try:
    #                 if inst[0].name == tenor.name:
    #                     ois_rate = inst[1]
    #                     break
    #             except AttributeError:
    #                 pass
    #         else:
    #             continue

    #         sofr_inst = qb.CompoundIndexBasisSwapInstrument(
    #             curve_date, tenor, sofr_fedfunds, leg_one_spread=rate, **convention,
    #         )

    #         ois_inst = qb.OISSwapInstrument(
    #             curve_date,
    #             tenor,
    #             ois_rate,
    #             fedfunds_sofr_short,
    #             **fedfunds_swap_conventions,
    #         )

    #         instrument_pair = qb.SimultaneousInstrument(
    #             sofr_inst, ois_inst, sofr_fedfunds
    #         )

    #         sofr_fedfunds.add_instrument(instrument_pair)

    #     else:
    #         raise Exception("Instrument type {} not recognized".format(kind))

    dvc_ois = load_curve("/home/kevindkeogh/Downloads/OIS123119USD.crv", curve_date)
    dvc_3ml = load_curve("/home/kevindkeogh/Downloads/3MLOIS123119USD.crv", curve_date)
    # dvc_sofr = load_curve("/home/kevindkeogh/Downloads/SOF123119USD.crv", curve_date)

    # print("")
    # print("Simultaneously bootstrapped SOFR-FedFunds")
    # sofr_fedfunds.build()
    # print("")
    # print("    SOFR")
    # compare_curves(dvc_sofr, sofr_fedfunds.curve_one)
    # print("")
    # print("    FedFunds")
    # compare_curves(dvc_ois, sofr_fedfunds.curve_two)

    print("")
    print("Simultaneously bootstrapped FedFunds-LIBOR")
    fedfunds_libor.build()
    print("")
    print("    3M LIBOR")
    compare_curves(dvc_3ml, fedfunds_libor.curve_two)
    print("")
    print("    FedFunds")
    compare_curves(dvc_ois, fedfunds_libor.curve_one)

    print("")
    print("Independently bootstrapped")
    fedfunds.build()
    usdlibor.build()
    print("")
    print("    3M LIBOR")
    compare_curves(dvc_3ml, usdlibor)
    print("")
    print("    FedFunds")
    compare_curves(dvc_ois, fedfunds)


if __name__ == "__main__":
    dates = [
        "2018-01-31",
        "2018-02-28",
        "2018-03-29",
        "2018-04-30",
        "2018-05-31",
        "2018-06-29",
        "2018-07-31",
        "2018-08-31",
        "2018-09-28",
        "2018-10-31",
        "2018-11-30",
        "2018-12-31",
        "2019-01-31",
        "2019-02-28",
        "2019-03-29",
        "2019-04-30",
        "2019-05-31",
        "2019-06-28",
        "2019-07-31",
        "2019-08-30",
        "2019-09-30",
        "2019-10-31",
        "2019-11-29",
        "2019-12-31",
    ]
    for date in dates:
        dt = datetime.datetime.strptime(date, "%Y-%m-%d")
        build_curves(dt)
