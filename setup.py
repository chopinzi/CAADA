from setuptools import setup, find_packages

setup(
    name='CAADA',
    version='0.1',
    packages=find_packages(),
    license='',
    author='Joshua Laughner',
    author_email='jllacct119@gmail.com',
    install_requires=['geopandas',
                      'netCDF4',
                      'numpy',
                      'pandas'],
    include_package_data=True,
    entry_points={
            'console_scripts': ['caada-main=caada.__main__:main']
        },
    description='COVID Atmospheric Ancillary Data Agglomerator'
)
