from argparse import ArgumentParser
from .agglomeration import summarize_and_merge_covid_files


def parse_opensky_covid_agg_args(p: ArgumentParser):
    p.description = "Agglomerate the OpenSky-derived datasets from Strohmeier et al. 2020 (doi: 10.5194/essd-2020-223) " \
                    "into netCDF files summed by day."
    p.add_argument('savename', help='Name to give the output netCDF file')
    p.add_argument('filenames', nargs='+', help='Paths .csv files from Strohmeier et al. to agglomerate')
    p.set_defaults(driver_fxn=summarize_and_merge_covid_files)
