from argparse import ArgumentParser
import sys

from .caada_logging import set_log_level
from .ca_pems.__main__ import parse_ca_pems_agg_args, parse_ca_pems_orgfiles_args


def parse_args():
    p = ArgumentParser(description='Agglomerate various datasets into netCDF files')
    p.add_argument('-v', '--verbose', action='store_const', const=2, default=1,
                   help='Increase verbosity of reports to console (stderr) to maximum')
    p.add_argument('-q', '--quiet', action='store_const', const=0, dest='verbose',
                   help='Reduce reports to console to warnings and errors only')

    subp = p.add_subparsers()
    ca_pems = subp.add_parser('ca-pems', help='Agglomerate Caltrans PEMS station data')
    parse_ca_pems_agg_args(ca_pems)
    ca_pems_org = subp.add_parser('org-pems', help='Organize Caltrans PEMS station data')
    parse_ca_pems_orgfiles_args(ca_pems_org)

    return vars(p.parse_args())


def main():
    cl_args = parse_args()
    driver = cl_args.pop('driver_fxn', None)
    if driver is None:
        print('ERROR: Must specify a subcommand or -h/--help', file=sys.stderr)
        return 1

    log_level = cl_args.pop('verbose')
    set_log_level(log_level)

    driver(**cl_args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
