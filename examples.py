#! /usr/bin/env python
# vim: set fileencoding=utf-8
"""
Testing for USD OIS and LIBOR qb. Note that these curves are the same
as the NY DVC curves (in terms of instruments). Using the 31 December 2019 data
below.
"""
import datetime
import copy

import qbootstrapper as qb

curve_effective = datetime.datetime(2019, 12, 31)
effective = datetime.datetime(2019, 12, 31)

# Curves
fedfunds = qb.Curve(curve_effective)
usdlibor = qb.LIBORCurve(curve_effective, discount_curve=fedfunds)

fedfunds_short_conventions = {
    "fixed_period_adjustment": "following",
    "float_period_adjustment": "following",
    "fixed_payment_adjustment": "following",
    "float_payment_adjustment": "following",
}

fedfunds_conventions = {
    "fixed_length": 6,
    "float_length": 3,
    "fixed_basis": "Act360",
    "float_basis": "Act360",
    "fixed_period_adjustment": "following",
    "float_period_adjustment": "following",
    "fixed_payment_adjustment": "following",
    "float_payment_adjustment": "following",
}

usdlibor_conventions = {
    "fixed_length": 6,
    "float_length": 3,
    "fixed_basis": "30360",
    "float_basis": "Act360",
    "fixed_period_adjustment": "following",
    "float_period_adjustment": "following",
    "fixed_payment_adjustment": "following",
    "float_payment_adjustment": "following",
    "rate_period": 3,
    "rate_period_length": "months",
}

fedfunds_cash = qb.instruments.LIBORInstrument(
    curve_effective,
    0.0155,
    2,
    fedfunds,
    length_type="days",
    payment_adjustment="following",
)

fedfunds_swap_onew = qb.OISSwapInstrument(
    effective,
    datetime.datetime(2020, 7, 14),
    0.0155,
    fedfunds,
    fixed_length=1,
    float_length=1,
    fixed_period_length="weeks",
    float_period_length="weeks",
    **fedfunds_short_conventions
)

fedfunds_swap_twow = qb.OISSwapInstrument(
    effective,
    datetime.datetime(2020, 1, 22),
    0.0155,
    fedfunds,
    fixed_length=2,
    float_length=2,
    fixed_period_length="weeks",
    float_period_length="weeks",
    **fedfunds_short_conventions
)

fedfunds_swap_threew = qb.OISSwapInstrument(
    effective,
    datetime.datetime(2020, 1, 28),
    0.01551,
    fedfunds,
    fixed_length=3,
    float_length=3,
    fixed_period_length="weeks",
    float_period_length="weeks",
    **fedfunds_short_conventions
)

fedfunds_short_swaps = [
    (datetime.datetime(2020, 2, 5), 0.01553, 1),
    (datetime.datetime(2020, 3, 5), 0.01559, 2),
    (datetime.datetime(2020, 4, 7), 0.01561, 3),
    (datetime.datetime(2020, 5, 6), 0.01559, 4),
    (datetime.datetime(2020, 6, 5), 0.01556, 5),
    (datetime.datetime(2020, 7, 7), 0.01553, 6),
    (datetime.datetime(2020, 10, 7), 0.01537, 9),
]

fedfunds_long_swaps = [
    (datetime.datetime(2021, 1, 5), 0.01516),
    (datetime.datetime(2021, 7, 5), 0.01474),
    (datetime.datetime(2022, 1, 5), 0.01453),
    (datetime.datetime(2023, 1, 5), 0.01449),
    (datetime.datetime(2024, 1, 5), 0.01466),
    (datetime.datetime(2025, 1, 5), 0.01497),
    (datetime.datetime(2026, 1, 5), 0.01532),
    (datetime.datetime(2027, 1, 5), 0.01566),
    (datetime.datetime(2028, 1, 5), 0.01602),
    (datetime.datetime(2029, 1, 5), 0.01635),
    (datetime.datetime(2030, 1, 5), 0.01666),
    (datetime.datetime(2032, 1, 5), 0.01720),
    (datetime.datetime(2035, 1, 5), 0.01777),
    (datetime.datetime(2040, 1, 5), 0.01833),
    (datetime.datetime(2045, 1, 5), 0.01854),
    (datetime.datetime(2050, 1, 5), 0.01859),
    (datetime.datetime(2060, 1, 5), 0.01831),
    (datetime.datetime(2070, 1, 5), 0.01787),
]

usdlibor_cash_instruments = [(3, "months", 0.0190838)]

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
    (datetime.datetime(2024, 1, 3), 0.01701),
    (datetime.datetime(2025, 1, 3), 0.01732),
    (datetime.datetime(2026, 1, 5), 0.01762),
    (datetime.datetime(2027, 1, 4), 0.01795),
    (datetime.datetime(2028, 1, 4), 0.0183),
    (datetime.datetime(2029, 1, 3), 0.01864),
    (datetime.datetime(2030, 1, 3), 0.01893),
    (datetime.datetime(2031, 1, 3), 0.01923),
    (datetime.datetime(2032, 1, 5), 0.01948),
    (datetime.datetime(2035, 1, 3), 0.02009),
    (datetime.datetime(2040, 1, 3), 0.02064),
    (datetime.datetime(2045, 1, 3), 0.02084),
    (datetime.datetime(2050, 1, 3), 0.0209),
    (datetime.datetime(2060, 1, 3), 0.02062),
    (datetime.datetime(2070, 1, 3), 0.0202),
]

fedfunds_libor_swap_data = [
    (datetime.datetime(2026, 1, 5), 0.002175),
    (datetime.datetime(2027, 1, 4), 0.002175),
    (datetime.datetime(2030, 1, 3), 0.002175),
    (datetime.datetime(2032, 1, 5), 0.002188),
    (datetime.datetime(2035, 1, 3), 0.0022),
    (datetime.datetime(2040, 1, 3), 0.002213),
    (datetime.datetime(2045, 1, 3), 0.002213),
    (datetime.datetime(2050, 1, 3), 0.002213),
]

# Fed funds build
fedfunds.add_instrument(fedfunds_cash)
fedfunds.add_instrument(fedfunds_swap_onew)
fedfunds.add_instrument(fedfunds_swap_twow)
fedfunds.add_instrument(fedfunds_swap_threew)

for (maturity, rate, months) in fedfunds_short_swaps:
    inst = qb.OISSwapInstrument(
        effective,
        maturity,
        rate,
        fedfunds,
        fixed_length=months,
        float_length=months,
        **fedfunds_short_conventions
    )
    fedfunds.add_instrument(inst)

for (maturity, rate) in fedfunds_long_swaps:
    inst = qb.OISSwapInstrument(
        effective, maturity, rate, fedfunds, **fedfunds_conventions
    )
    fedfunds.add_instrument(inst)


# USD LIBOR build

for (length, length_type, rate) in usdlibor_cash_instruments:
    inst = qb.LIBORInstrument(
        effective,
        rate,
        length,
        usdlibor,
        length_type=length_type,
        payment_adjustment="following",
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

for (maturity, rate, months) in fedfunds_short_swaps:
    inst = qb.OISSwapInstrument(
        effective,
        maturity,
        rate,
        fedfunds_short,
        fixed_length=months,
        float_length=months,
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
for (length, length_type, rate) in usdlibor_cash_instruments:
    inst = qb.LIBORInstrument(
        effective,
        rate,
        length,
        usdlibor_short,
        length_type=length_type,
        payment_adjustment="following",
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

print("FedFunds")
fedfunds.build()
fedfunds.view()
fedfunds.zeros()
print("3M LIBOR")
usdlibor.build()
usdlibor.view()
usdlibor.zeros()
print("FedFunds LIBOR")
fedfunds_libor.build()
fedfunds_libor.discount_curve.view()
fedfunds_libor.discount_curve.zeros()
fedfunds_libor.projection_curve.view()
fedfunds_libor.projection_curve.zeros()
