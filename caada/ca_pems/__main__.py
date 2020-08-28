from argparse import ArgumentParser
from .agglomeration import cl_dispatcher
from .files import sort_pems_files


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


def parse_ca_pems_orgfiles_args(p: ArgumentParser):
    p.description = 'Organize downloaded Caltrans PEMS stations files into directories needed by the agglomerator'
    p.add_argument('pems_root', help='The path to the directory where you want the actual data stored.')
    p.add_argument('meta_root', help='The path to the directory where you want the metadata stored.')
    p.add_argument('pems_files', nargs='+', help='All PEMS station and station metadata files to organize.')
    p.add_argument('-x', '--delete-orig', action='store_true', help='Delete original files as they are moved.')
    p.add_argument('-c', '--no-decompress', action='store_false', dest='decompress',
                   help='Do not decompress any .gz files as they are moved. By default, .gz files are decompressed '
                        'and, if --delete-orig is specified, deleted.')
    p.add_argument('-d', '--dry-run', action='store_true', help='Print what would be done, but do not actually do it.')
    p.set_defaults(driver_fxn=sort_pems_files)
