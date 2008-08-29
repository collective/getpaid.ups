"""
$Id: setup.py 1868 2008-08-22 22:00:38Z fairwinds.dp $

Copyright (c) 2007 - 2008 ifPeople, Kapil Thangavelu, and Contributors
All rights reserved. Refer to LICENSE.txt for details of distribution and use.

Distutils setup
 
"""

import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name="getpaid.ups",
    version="0.3",
    author='getpaid community',
    author_email='getpaid-dev@googlegroups.com',
    description='Get paid UPS functionality',
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['getpaid'],
    include_package_data=True,
    install_requires = [ 'setuptools',
                         'getpaid.core',
                         'elementtree',
                         'zope.formlib',
                         'zope.schema',
                         'ore.viewlet',
                         'Products.PloneGetPaid',
                         ],
    zip_safe = False,
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Framework :: Zope3",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries",
    ],
    long_description = (
        read('README.txt')
        + '\n' +
        read('CHANGES.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('src', 'getpaid', 'ups', 'readme.txt')
        + '\n' +
        'Download\n'
        '**********************\n'
        ),
    )
