#! /usr/bin/env python
# vim: set fileencoding=utf-8
'''
Testing for USD, EUR, and GBP OIS qb. Note that these curves are the same
as the NY DVC curves (in terms of instruments). Using the 30 June 2016 data
below, we achieved <1bp difference for all points for the EUR and GBP OIS
curves to the Numerix curve. There was a difference of 1-2 bps for the USD OIS
curve, as that uses Average Index swaps, which have not been implemented.
The difference is attributable to that adjustment in instruments.
'''
import datetime

import qbootstrapper as qb

curve_effective = datetime.datetime(2016, 6, 30)
effective = datetime.datetime(2016, 7, 5)

# EUR OIS curve (6/30/2016 data, 6/30/2016 effective date)
eonia = qb.Curve(curve_effective)

eonia_conventions = {'fixed_length': 12,
                     'float_length': 12,
                     'fixed_basis': 'Act360',
                     'float_basis': 'Act360',
                     'fixed_period_adjustment': 'following',
                     'float_period_adjustment': 'following',
                     'fixed_payment_adjustment': 'following',
                     'float_payment_adjustment': 'following'
                     }

eonia_cash = qb.LIBORInstrument(curve_effective,
                                -0.00293,
                                5,
                                eonia,
                                length_type='days',
                                payment_adjustment='following')

eonia_short_instruments = [(datetime.datetime(2016,  8,  5), -0.00339),
                           (datetime.datetime(2016,  9,  5), -0.00347),
                           (datetime.datetime(2016, 10,  5), -0.00357),
                           (datetime.datetime(2016, 11,  5), -0.00367),
                           (datetime.datetime(2016, 12,  5), -0.00376),
                           (datetime.datetime(2017,  1,  5), -0.00385),
                           (datetime.datetime(2017,  2,  5), -0.00394),
                           (datetime.datetime(2017,  3,  5), -0.00400),
                           (datetime.datetime(2017,  4,  5), -0.00406),
                           (datetime.datetime(2017,  5,  5), -0.00412),
                           (datetime.datetime(2017,  6,  5), -0.00418)]

eonia_instruments = [(datetime.datetime(2017,  7,  5), -0.00423),
                     (datetime.datetime(2018,  1,  5), -0.00449),
                     (datetime.datetime(2018,  7,  5), -0.00468),
                     (datetime.datetime(2019,  7,  5), -0.00480),
                     (datetime.datetime(2020,  7,  5), -0.00441),
                     (datetime.datetime(2021,  7,  5), -0.00364),
                     (datetime.datetime(2022,  7,  5), -0.00295),
                     (datetime.datetime(2023,  7,  5), -0.00164),
                     (datetime.datetime(2024,  7,  5), -0.00055),
                     (datetime.datetime(2025,  7,  5),  0.00055),
                     (datetime.datetime(2026,  7,  5),  0.00155),
                     (datetime.datetime(2027,  7,  5),  0.00248),
                     (datetime.datetime(2028,  7,  5),  0.00325),
                     (datetime.datetime(2031,  7,  5),  0.00505),
                     (datetime.datetime(2036,  7,  5),  0.00651),
                     (datetime.datetime(2041,  7,  5),  0.00696),
                     (datetime.datetime(2046,  7,  5),  0.00707),
                     (datetime.datetime(2051,  7,  5),  0.00718),
                     (datetime.datetime(2056,  7,  5),  0.00724),
                     (datetime.datetime(2066,  7,  5),  0.00685)]

eonia.add_instrument(eonia_cash)

for idx, (maturity, rate) in enumerate(eonia_short_instruments):
    inst = qb.OISSwapInstrument(effective,
                                maturity,
                                rate,
                                eonia,
                                fixed_basis='Act360',
                                fixed_length=idx + 1,
                                float_length=idx + 1)
    eonia.add_instrument(inst)

for (maturity, rate) in eonia_instruments:
    inst = qb.OISSwapInstrument(effective,
                                maturity,
                                rate,
                                eonia,
                                **eonia_conventions)
    eonia.add_instrument(inst)


# USD OIS curve (6/30/2016 data, 6/30/2016 effective date)
# Note that these are synthetics, the actual swap rates for 6y+ maturities
# are average OIS + basis v LIBOR
fedfunds = qb.Curve(curve_effective)

fedfunds_short_conventions = {'fixed_period_adjustment': 'following',
                              'float_period_adjustment': 'following',
                              'fixed_payment_adjustment': 'following',
                              'float_payment_adjustment': 'following'}

fedfunds_conventions = {'fixed_length': 6,
                        'float_length': 3,
                        'fixed_basis': 'Act360',
                        'float_basis': 'Act360',
                        'fixed_period_adjustment': 'following',
                        'float_period_adjustment': 'following',
                        'fixed_payment_adjustment': 'following',
                        'float_payment_adjustment': 'following'}

fedfunds_cash = qb.LIBORInstrument(curve_effective,
                                   0.003,
                                   4,
                                   fedfunds,
                                   length_type='days',
                                   payment_adjustment='following')

fedfunds_swap_onew = qb.OISSwapInstrument(effective,
                                          datetime.datetime(2016, 7, 12),
                                          0.00387,
                                          fedfunds,
                                          fixed_length=1,
                                          float_length=1,
                                          fixed_period_length='weeks',
                                          float_period_length='weeks',
                                          **fedfunds_short_conventions)

fedfunds_swap_twow = qb.OISSwapInstrument(effective,
                                          datetime.datetime(2016, 7, 19),
                                          0.00387,
                                          fedfunds,
                                          fixed_length=2,
                                          float_length=2,
                                          fixed_period_length='weeks',
                                          float_period_length='weeks',
                                          **fedfunds_short_conventions)

fedfunds_swap_threew = qb.OISSwapInstrument(effective,
                                            datetime.datetime(2016, 7, 26),
                                            0.00387,
                                            fedfunds,
                                            fixed_length=3,
                                            float_length=3,
                                            fixed_period_length='weeks',
                                            float_period_length='weeks',
                                            **fedfunds_short_conventions)

fedfunds_short_instruments = [(datetime.datetime(2016, 8,  5),  0.00378, 1),
                              (datetime.datetime(2016, 9,  5),  0.00375, 2),
                              (datetime.datetime(2016, 10,  5),  0.00371, 3),
                              (datetime.datetime(2016, 11,  5),  0.00369, 4),
                              (datetime.datetime(2016, 12,  5),  0.00366, 5),
                              (datetime.datetime(2017, 1,  5),  0.00365, 6),
                              (datetime.datetime(2017, 4,  5),  0.00371, 9)]

fedfunds_instruments = [(datetime.datetime(2017, 3,  5),  0.003780),
                        (datetime.datetime(2018, 1,  5),  0.003950),
                        (datetime.datetime(2018, 7,  5),  0.004220),
                        (datetime.datetime(2019, 7,  5),  0.004850),
                        (datetime.datetime(2020, 7,  5),  0.005600),
                        (datetime.datetime(2021, 7,  5),  0.006450),
                        (datetime.datetime(2022, 7,  5),  0.007350),
                        (datetime.datetime(2023, 7,  5),  0.008155),
                        (datetime.datetime(2026, 7,  5),  0.010262),
                        (datetime.datetime(2028, 7,  5),  0.011370),
                        (datetime.datetime(2031, 7,  5),  0.012585),
                        (datetime.datetime(2036, 7,  5),  0.013827),
                        (datetime.datetime(2041, 7,  5),  0.014470),
                        (datetime.datetime(2046, 7,  5),  0.014847),
                        (datetime.datetime(2056, 7,  5),  0.015047),
                        (datetime.datetime(2066, 7,  5),  0.014897)]

fedfunds.add_instrument(fedfunds_cash)
fedfunds.add_instrument(fedfunds_swap_onew)
fedfunds.add_instrument(fedfunds_swap_twow)
fedfunds.add_instrument(fedfunds_swap_threew)

for (maturity, rate, months) in fedfunds_short_instruments:
    inst = qb.OISSwapInstrument(effective,
                                maturity,
                                rate,
                                fedfunds,
                                fixed_length=months,
                                float_length=months,
                                **fedfunds_short_conventions)
    fedfunds.add_instrument(inst)

for (maturity, rate) in fedfunds_instruments:
    inst = qb.OISSwapInstrument(effective,
                                maturity,
                                rate,
                                fedfunds,
                                **fedfunds_conventions)
    fedfunds.add_instrument(inst)

# EUR EURIBOR 6M curve (6/30/2016 data, 6/30/2016 effective date)
euribor = qb.LIBORCurve(curve_effective, discount_curve=eonia)
effective = datetime.datetime(2016, 7, 4)

euribor_short_conventions = {'fixed_period_adjustment': 'following',
                             'float_period_adjustment': 'following',
                             'fixed_payment_adjustment': 'following',
                             'float_payment_adjustment': 'following',
                             'fixed_basis': '30E360'}

euribor_conventions = {'fixed_length': 12,
                       'float_length': 6,
                       'fixed_basis': '30E360',
                       'float_basis': 'Act360',
                       'fixed_period_adjustment': 'following',
                       'float_period_adjustment': 'following',
                       'fixed_payment_adjustment': 'following',
                       'float_payment_adjustment': 'following',
                       'rate_period': 6,
                       'rate_period_length': 'months'}

euribor_cash_instruments = [(1, 'weeks',  -0.00371),
                            (2, 'weeks',  -0.00370),
                            (1, 'months', -0.00364),
                            (2, 'months', -0.00321),
                            (3, 'months', -0.00286),
                            (6, 'months', -0.00179)]

euribor_fra_instruments = [(datetime.datetime(2017,  1,  4), datetime.datetime(2017,  7,  4), -0.00210),
                           (datetime.datetime(2017,  7,  4), datetime.datetime(2018,  1,  4), -0.00222)]

euribor_swap_instruments = [(datetime.datetime(2018,  7,  4), -0.002075),
                            (datetime.datetime(2019,  7,  4), -0.001979),
                            (datetime.datetime(2020,  7,  4), -0.001421),
                            (datetime.datetime(2021,  7,  4), -0.000539),
                            (datetime.datetime(2022,  7,  4),  0.000166),
                            (datetime.datetime(2023,  7,  4),  0.001454),
                            (datetime.datetime(2024,  7,  4),  0.002476),
                            (datetime.datetime(2025,  7,  4),  0.003498),
                            (datetime.datetime(2026,  7,  4),  0.004424),
                            (datetime.datetime(2027,  7,  4),  0.005268),
                            (datetime.datetime(2028,  7,  4),  0.005954),
                            (datetime.datetime(2031,  7,  4),  0.007514),
                            (datetime.datetime(2036,  7,  4),  0.008604),
                            (datetime.datetime(2041,  7,  4),  0.008824),
                            (datetime.datetime(2046,  7,  4),  0.008754),
                            (datetime.datetime(2051,  7,  4),  0.008694),
                            (datetime.datetime(2056,  7,  4),  0.008582),
                            (datetime.datetime(2061,  7,  4),  0.008281),
                            (datetime.datetime(2066,  7,  4),  0.008054)]

for (length, length_type, rate) in euribor_cash_instruments:
    inst = qb.LIBORInstrument(effective,
                              rate,
                              length,
                              euribor,
                              length_type=length_type,
                              payment_adjustment='following')
    euribor.add_instrument(inst)

for (start_date, end_date, rate) in euribor_fra_instruments:
    inst = qb.FRAInstrumentByDates(start_date, end_date, rate, euribor)
    euribor.add_instrument(inst)

for (maturity, rate) in euribor_swap_instruments:
    inst = qb.LIBORSwapInstrument(effective,
                                  maturity,
                                  rate,
                                  euribor,
                                  **euribor_conventions)
    euribor.add_instrument(inst)

# USD LIBOR 3M curve (6/30/2016 data)
usdlibor = qb.LIBORCurve(curve_effective, discount_curve=fedfunds)
effective = datetime.datetime(2016, 7, 5)

usdlibor_conventions = {'fixed_length': 6,
                        'float_length': 3,
                        'fixed_basis': '30360',
                        'float_basis': 'Act360',
                        'fixed_period_adjustment': 'following',
                        'float_period_adjustment': 'following',
                        'fixed_payment_adjustment': 'following',
                        'float_payment_adjustment': 'following',
                        'rate_period': 3,
                        'rate_period_length': 'months'}

usdlibor_cash_instruments = [(1, 'weeks',   0.004402),
                             (1, 'months',  0.004651),
                             (2, 'months',  0.005490),
                             (3, 'months',  0.006541)]

usdlibor_futures_instruments = [(datetime.datetime(2016,  9, 21), datetime.datetime(2016, 12, 21), 99.35562),
                                (datetime.datetime(2016, 12, 21),
                                 datetime.datetime(2017,  3, 21), 99.32671),
                                (datetime.datetime(2017,  3, 15),
                                 datetime.datetime(2017,  6, 15), 99.30839),
                                (datetime.datetime(2017,  6, 21),
                                 datetime.datetime(2017,  9, 21), 99.27554),
                                (datetime.datetime(2017,  9, 20),
                                 datetime.datetime(2017, 12, 20), 99.23812),
                                (datetime.datetime(2017, 12, 20),
                                 datetime.datetime(2018,  3, 20), 99.18614),
                                (datetime.datetime(2018,  3, 21),
                                 datetime.datetime(2018,  6, 21), 99.14960),
                                (datetime.datetime(2018,  6, 20),
                                 datetime.datetime(2018,  9, 20), 99.10847),
                                (datetime.datetime(2018,  9, 19),
                                 datetime.datetime(2018, 12, 19), 99.06277),
                                (datetime.datetime(2018, 12, 19),
                                 datetime.datetime(2019,  3, 19), 99.00748),
                                (datetime.datetime(2019,  3, 20),
                                 datetime.datetime(2019,  6, 20), 98.96757),
                                (datetime.datetime(2019,  6, 19), datetime.datetime(2019,  9, 19), 98.92307)]

usdlibor_swap_instruments = [(datetime.datetime(2020,  7,  5),  0.00898),
                             (datetime.datetime(2021,  7,  5),  0.00985),
                             (datetime.datetime(2022,  7,  5),  0.01075),
                             (datetime.datetime(2023,  7,  5),  0.01158),
                             (datetime.datetime(2024,  7,  5),  0.01241),
                             (datetime.datetime(2025,  7,  5),  0.01311),
                             (datetime.datetime(2026,  7,  5),  0.01375),
                             (datetime.datetime(2027,  7,  5),  0.01435),
                             (datetime.datetime(2028,  7,  5),  0.01487),
                             (datetime.datetime(2031,  7,  5),  0.01611),
                             (datetime.datetime(2036,  7,  5),  0.01739),
                             (datetime.datetime(2041,  7,  5),  0.01807),
                             (datetime.datetime(2046,  7,  5),  0.01846),
                             (datetime.datetime(2056,  7,  5),  0.01866),
                             (datetime.datetime(2066,  7,  5),  0.01851)]

for (length, length_type, rate) in usdlibor_cash_instruments:
    inst = qb.LIBORInstrument(effective,
                              rate,
                              length,
                              usdlibor,
                              length_type=length_type,
                              payment_adjustment='following')
    usdlibor.add_instrument(inst)

for (start_date, end_date, price) in usdlibor_futures_instruments:
    inst = qb.FuturesInstrumentByDates(start_date, end_date, price, usdlibor)
    usdlibor.add_instrument(inst)

for (maturity, rate) in usdlibor_swap_instruments:
    inst = qb.LIBORSwapInstrument(effective,
                                  maturity,
                                  rate,
                                  usdlibor,
                                  **usdlibor_conventions)
    usdlibor.add_instrument(inst)

# GBP OIS curve (6/30/2016 data, 6/30/2016 effective date)
sonia = qb.Curve(curve_effective)

sonia_short_conventions = {'fixed_period_adjustment': 'following',
                           'float_period_adjustment': 'following',
                           'fixed_payment_adjustment': 'following',
                           'float_payment_adjustment': 'following',
                           'rate_basis': 'Act365',
                           'fixed_basis': 'Act365',
                           'float_basis': 'Act365'
                           }

sonia_conventions = {'fixed_length': 12,
                     'float_length': 12,
                     'fixed_basis': 'Act360',
                     'float_basis': 'Act360',
                     'fixed_period_adjustment': 'following',
                     'float_period_adjustment': 'following',
                     'fixed_payment_adjustment': 'following',
                     'float_payment_adjustment': 'following',
                     'rate_basis': 'Act365',
                     'fixed_basis': 'Act365',
                     'float_basis': 'Act365'
                     }

sonia_cash = qb.LIBORInstrument(curve_effective,
                                0.004416,
                                1,
                                sonia,
                                length_type='days',
                                payment_adjustment='following')
sonia_swap_onew = qb.OISSwapInstrument(curve_effective,
                                       datetime.datetime(2016, 7, 7),
                                       0.00443,
                                       sonia,
                                       fixed_length=1,
                                       float_length=1,
                                       fixed_period_length='weeks',
                                       float_period_length='weeks',
                                       **sonia_short_conventions)
sonia_swap_twow = qb.OISSwapInstrument(curve_effective,
                                       datetime.datetime(2016, 7, 14),
                                       0.00448,
                                       sonia,
                                       fixed_length=2,
                                       float_length=2,
                                       fixed_period_length='weeks',
                                       float_period_length='weeks',
                                       **sonia_short_conventions)
sonia_swap_threew = qb.OISSwapInstrument(curve_effective,
                                         datetime.datetime(2016, 7, 21),
                                         0.004042,
                                         sonia,
                                         fixed_length=3,
                                         float_length=3,
                                         fixed_period_length='weeks',
                                         float_period_length='weeks',
                                         **sonia_short_conventions)
sonia_swap_onem = qb.OISSwapInstrument(curve_effective,
                                       datetime.datetime(2016, 7, 29),
                                       0.0038,
                                       sonia,
                                       fixed_length=1,
                                       float_length=1,
                                       **sonia_short_conventions)
sonia_swap_twom = qb.OISSwapInstrument(curve_effective,
                                       datetime.datetime(2016, 8, 31),
                                       0.003017,
                                       sonia,
                                       fixed_length=2,
                                       float_length=2,
                                       **sonia_short_conventions)
sonia_swap_threem = qb.OISSwapInstrument(curve_effective,
                                         datetime.datetime(2016, 9, 30),
                                         0.002653,
                                         sonia,
                                         fixed_length=3,
                                         float_length=3,
                                         **sonia_short_conventions)
sonia_swap_fourm = qb.OISSwapInstrument(curve_effective,
                                        datetime.datetime(2016, 10, 31),
                                        0.002425,
                                        sonia,
                                        fixed_length=4,
                                        float_length=4,
                                        **sonia_short_conventions)
sonia_swap_fivem = qb.OISSwapInstrument(curve_effective,
                                        datetime.datetime(2016, 11, 30),
                                        0.002213,
                                        sonia,
                                        fixed_length=5,
                                        float_length=5,
                                        **sonia_short_conventions)
sonia_swap_sixm = qb.OISSwapInstrument(curve_effective,
                                       datetime.datetime(2016, 12, 30),
                                       0.002053,
                                       sonia,
                                       fixed_length=6,
                                       float_length=6,
                                       **sonia_short_conventions)
sonia_swap_sevenm = qb.OISSwapInstrument(curve_effective,
                                         datetime.datetime(2017, 1, 31),
                                         0.001925,
                                         sonia,
                                         fixed_length=7,
                                         float_length=7,
                                         **sonia_short_conventions)
sonia_swap_eightm = qb.OISSwapInstrument(curve_effective,
                                         datetime.datetime(2017, 2, 28),
                                         0.001812,
                                         sonia,
                                         fixed_length=8,
                                         float_length=8,
                                         **sonia_short_conventions)
sonia_swap_ninem = qb.OISSwapInstrument(curve_effective,
                                        datetime.datetime(2017, 3, 31),
                                        0.001716,
                                        sonia,
                                        fixed_length=9,
                                        float_length=9,
                                        **sonia_short_conventions)
sonia_swap_tenm = qb.OISSwapInstrument(curve_effective,
                                       datetime.datetime(2017, 4, 28),
                                       0.00164,
                                       sonia,
                                       fixed_length=10,
                                       float_length=10,
                                       **sonia_short_conventions)
sonia_swap_elevenm = qb.OISSwapInstrument(curve_effective,
                                          datetime.datetime(2017, 5, 31),
                                          0.001564,
                                          sonia,
                                          fixed_length=11,
                                          float_length=11,
                                          **sonia_short_conventions)

sonia_short_swaps = [sonia_cash, sonia_swap_onew, sonia_swap_twow,
                     sonia_swap_threew, sonia_swap_onem, sonia_swap_twom,
                     sonia_swap_threem, sonia_swap_fourm, sonia_swap_fivem,
                     sonia_swap_sixm, sonia_swap_sevenm, sonia_swap_eightm,
                     sonia_swap_ninem, sonia_swap_tenm, sonia_swap_elevenm]

sonia_swap_data = [(datetime.datetime(2017, 6, 30), 0.001499),
                   (datetime.datetime(2017, 12, 29), 0.001223),
                   (datetime.datetime(2018, 6, 30), 0.001076),
                   (datetime.datetime(2019, 6, 30), 0.001106),
                   (datetime.datetime(2020, 6, 30), 0.001444),
                   (datetime.datetime(2021, 6, 30), 0.002058),
                   (datetime.datetime(2022, 6, 30), 0.00284),
                   (datetime.datetime(2023, 6, 30), 0.003749),
                   (datetime.datetime(2024, 6, 30), 0.004668),
                   (datetime.datetime(2025, 6, 30), 0.005532),
                   (datetime.datetime(2026, 6, 30), 0.006322),
                   (datetime.datetime(2027, 6, 30), 0.007016),
                   (datetime.datetime(2028, 6, 30), 0.007609),
                   (datetime.datetime(2031, 6, 30), 0.008891),
                   (datetime.datetime(2036, 6, 30), 0.009792),
                   (datetime.datetime(2041, 6, 30), 0.009916),
                   (datetime.datetime(2046, 6, 30), 0.009869),
                   (datetime.datetime(2056, 6, 30), 0.009242),
                   (datetime.datetime(2066, 6, 30), 0.009003)]

for inst in sonia_short_swaps:
    sonia.add_instrument(inst)

for maturity, rate in sonia_swap_data:
    sonia.add_instrument(qb.OISSwapInstrument(curve_effective,
                                              maturity,
                                              rate,
                                              sonia,
                                              **sonia_conventions))
remove = '''
fedfunds_short = qb.Curve(curve_effective)

fedfunds_short_instruments = [
    fedfunds_cash,
    fedfunds_swap_onew,
    fedfunds_swap_twow,
    fedfunds_swap_threew,
    fedfunds_swap_onem,
    fedfunds_swap_twom,
    fedfunds_swap_threem,
    fedfunds_swap_fourm,
    fedfunds_swap_fivem,
    fedfunds_swap_sixm,
    fedfunds_swap_ninem,
    fedfunds_swap_oney,
    fedfunds_swap_eighteenm,
    fedfunds_swap_twoy,
    fedfunds_swap_threey,
    fedfunds_swap_foury,
    fedfunds_swap_fivey]

for inst in fedfunds_short_instruments:
    inst.curve = fedfunds_short
    fedfunds_short.add_instrument(inst)

usdlibor_short = qb.LIBORCurve(curve_effective, discount_curve=fedfunds_short)

usdlibor_short_instruments = [
    usdlibor_cash_onew,
    usdlibor_cash_onem,
    usdlibor_cash_twom,
    usdlibor_cash_threem,
    usdlibor_future_one,
    usdlibor_future_two,
    usdlibor_future_three,
    usdlibor_future_four,
    usdlibor_future_five,
    usdlibor_future_six,
    usdlibor_future_seven,
    usdlibor_future_eight,
    usdlibor_future_nine,
    usdlibor_future_ten,
    usdlibor_future_eleven,
    usdlibor_future_twelve,
    usdlibor_swap_foury,
    usdlibor_swap_fivey]

for inst in usdlibor_short_instruments:
    inst.curve = usdlibor_short
    usdlibor_short.add_instrument(inst)

fedfunds_libor = qb.SimultaneousStrippedCurve(curve_effective,
                                                  fedfunds_short,
                                                  usdlibor_short)

fedfunds_libor_swap_data = [(datetime.datetime(2022, 7,  5), 0.003400),
                            (datetime.datetime(2023, 7,  5), 0.003425),
                            (datetime.datetime(2026, 7,  5), 0.003488),
                            (datetime.datetime(2028, 7,  5), 0.003500),
                            (datetime.datetime(2031, 7,  5), 0.003525),
                            (datetime.datetime(2036, 7,  5), 0.003563),
                            (datetime.datetime(2041, 7,  5), 0.003600),
                            (datetime.datetime(2046, 7,  5), 0.003613),
                            (datetime.datetime(2056, 7,  5), 0.003613),
                            (datetime.datetime(2066, 7,  5), 0.003613)]

usdlibor_simultaneous_insts = [usdlibor_swap_sixy,
                               usdlibor_swap_seveny,
                               usdlibor_swap_teny,
                               usdlibor_swap_twelvey,
                               usdlibor_swap_fifteeny,
                               usdlibor_swap_twentyy,
                               usdlibor_swap_twentyfivey,
                               usdlibor_swap_thirtyy,
                               usdlibor_swap_fortyy,
                               usdlibor_swap_fiftyy]

for idx, (maturity, rate) in enumerate(fedfunds_libor_swap_data):
    ois_inst = qb.AverageIndexBasisSwapInstrument(effective,
                                                     maturity,
                                                     fedfunds_libor,
                                                     leg_one_spread=rate)
    libor_inst = usdlibor_simultaneous_insts[idx]
    instrument_pair = qb.SimultaneousInstrument(ois_inst,
                                                   libor_inst,
                                                   fedfunds_libor)
    fedfunds_libor.add_instrument(instrument_pair)
'''

# eonia.build()
# eonia.view()
# eonia.zeros()
# fedfunds.build()
# fedfunds.view()
# fedfunds.zeros()
# sonia.build()
# sonia.view()
# sonia.zeros()
# euribor.build()
# euribor.view()
# euribor.zeros()
# usdlibor.build()
# usdlibor.view()
# usdlibor.zeros()
# fedfunds_libor.build()
# fedfunds_libor.discount_curve.view()
# fedfunds_libor.discount_curve.zeros()
# fedfunds_libor.projection_curve.view()
# fedfunds_libor.projection_curve.zeros()
