from argparse import ArgumentParser
import sys

from .ca_pems.__main__ import parse_ca_pems_agg_args, parse_ca_pems_orgfiles_args


def parse_args():
    p = ArgumentParser(description='Agglomerate various datasets into netCDF files')

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

    driver(**cl_args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
