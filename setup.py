from setuptools import setup, Extension
from configparser import RawConfigParser

# Get some values from the setup.cfg
conf = RawConfigParser()
conf.read(['setup.cfg'])
metadata = dict(conf.items('metadata'))

PACKAGENAME = metadata.get('package_name', 'packagename')
DESCRIPTION = metadata.get('description', '')
AUTHOR = metadata.get('author', '')
AUTHOR_EMAIL = metadata.get('author_email', '')
VERSION = metadata.get('version', '')
LICENSE = metadata.get('license', 'unknown')

rgbtohex_module = Extension('chec_operator.utils.rgbtohex',
                            sources=['chec_operator/utils/rgbtohex.cc'])

setup(
    name=PACKAGENAME,
    packages=['chec_operator'],
    version=VERSION,
    description=DESCRIPTION,
    install_requires=['astropy', 'scipy', 'numpy', 'matplotlib',
                      'scikit-learn', 'traitlets', 'tqdm', 'bokeh', 'pandas'],
    setup_requires=['pytest-runner', ],
    tests_require=['pytest', ],
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    classifiers=[
                'Intended Audience :: Science/Research',
                'License :: OSI Approved :: BSD License',
                'Operating System :: OS Independent',
                'Programming Language :: C',
                'Programming Language :: Cython',
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: Implementation :: CPython',
                'Topic :: Scientific/Engineering :: Astronomy',
                'Development Status :: 3 - Alpha',
    ],

    ext_modules=[rgbtohex_module],
)
