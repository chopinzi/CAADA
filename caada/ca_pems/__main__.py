from argparse import ArgumentParser
from .agglomeration import cl_dispatcher


def parse_ca_pems_agg_args(p: ArgumentParser):
    p.description = 'Agglomerate Caltrans PEMS station files into a single netCDF file'

    p.add_argument('pems_root', help='The path to the root directory containing the PEMS data. This must '
                                               'be a directory with subdirectories organizing the data by district '
                                               'named "d03", "d04", ..., "d12". DO NOT mix different time resolutions.')
    p.add_argument('meta_root', help='The path to the root directory containing the PEMS metadata. This must '
                                               'have the same organization as PEMS_ROOT.')
    p.add_argument('save_path', help='The path to save the netCDF file as (including filename).')
    p.add_argument('-s', '--spatial-resolution', default='county', choices=('county',),
                   help='What spatial resolution to agglomerate the data to.')
    p.set_defaults(driver_fxn=cl_dispatcher)
