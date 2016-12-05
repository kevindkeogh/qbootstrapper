# qBootstrapper

The repository contains objects that allow the fast and efficient creation of a zero-coupon yield curve. The package requires Scipy, for numerical optimization and spline fitting, and Numpy, for efficient matrix mathematics. It works with both python 2.7 and python3!

# Usage
A complete demonstration of the construction of USD, EUR, and GBP OIS and LIBOR swap curves is in examples.py. In short, however, a yield curve can be constructed like this:
```python
import qbootstrapper as qb
import datetime

curve_date = datetime.datetime(2016, 6, 30)
eonia = qb.Curve(curve_date)
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

for (maturity, rate) in eonia_instruments:
    inst = qb.OISSwapInstrument(effective,
                                maturity,
                                rate,
                                eonia,
                                **eonia_conventions)
    eonia.add_instrument(inst)
    
eonia.view()
eonia.zeros()
```

## Dependencies
The project tries to maintain few external dependences. As of now, it is limited to Scipy, Numpy, and dateutil.

## Installation
I won't put this on pypa until there is a lot more functionality. In order to install, just clone the repository.
```sh
git clone https://github.com/kevindkeogh/qbootstrapper.git
cd qbootstrapper
pyvenv qb
source qb/bin/activate
pip3 install -r requirements.txt
python3 -i examples.py
>>> eonia.zeros()
```

## Development Plan
There are a lot of instruments that are not currently available, so to start my plan is to implement basis curve instruments (both tenor-basis and cross-currency-basis adjusted curves). The plan is also includes implementation of a convexity adjustment for IR futures.

I also have 0 tests, so...

License
-------
MIT
