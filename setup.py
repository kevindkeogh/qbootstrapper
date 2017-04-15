from distutils.core import setup

VERSION = '0.1'
LICENSE = 'MIT'

setup(
        name='qbootstrapper',
        packages=['qbootstrapper'],
        version=VERSION,
        license=LICENSE,
        install_requires=[
            'scipy',
            'numpy',
            'python-dateutil',
            ],
        license=LICENSE,
     )
