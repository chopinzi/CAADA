from argparse import ArgumentParser
import sys

from .caada_logging import set_log_level
from .ca_pems.__main__ import parse_ca_pems_agg_args, parse_ca_pems_orgfiles_args
from .opensky.__main__ import parse_opensky_covid_agg_args
from .epa_cems.__main__ import parse_cems_download_args

def parse_args():
    p = ArgumentParser(description='Agglomerate various datasets into netCDF files')
    p.add_argument('-v', '--verbose', action='store_const', const=2, default=1,
                   help='Increase verbosity of reports to console (stderr) to maximum')
    p.add_argument('-q', '--quiet', action='store_const', const=0, dest='verbose',
                   help='Reduce reports to console to warnings and errors only')
    p.add_argument('--pdb', action='store_true', help='Launch Python debugger immediately')

    subp = p.add_subparsers()
    ca_pems = subp.add_parser('ca-pems', help='Agglomerate Caltrans PEMS station data')
    parse_ca_pems_agg_args(ca_pems)
    ca_pems_org = subp.add_parser('org-pems', help='Organize Caltrans PEMS station data')
    parse_ca_pems_orgfiles_args(ca_pems_org)

    os_covid = subp.add_parser('os-covid', help='Agglomerate OpenSky-derived COVID .csvs into one netCDF')
    parse_opensky_covid_agg_args(os_covid)

    epa_cems_dl = subp.add_parser('epa-cems-dl', help='Download US EPA CEMS data')
    parse_cems_download_args(epa_cems_dl)

    return vars(p.parse_args())


def main():
    cl_args = parse_args()
    driver = cl_args.pop('driver_fxn', None)
    if driver is None:
        print('ERROR: Must specify a subcommand or -h/--help', file=sys.stderr)
        return 1

    log_level = cl_args.pop('verbose')
    set_log_level(log_level)

    if cl_args.pop('pdb'):
        import pdb
        pdb.set_trace()

    driver(**cl_args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
