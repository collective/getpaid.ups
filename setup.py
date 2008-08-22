from setuptools import setup, find_packages

setup(
    name="getpaid.ups",
    version="0.2",
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
    )
