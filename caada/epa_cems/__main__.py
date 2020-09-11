from argparse import ArgumentParser
from .web import download_cl_driver


def parse_cems_download_args(p: ArgumentParser):
    p.description = 'Downlowd continuous emissions data from the US EPA FTP server'
    p.add_argument('time_res', choices=('daily', 'hourly'), help='Which time resolution of data to download')
    p.add_argument('start_time', help='Beginning of time period to download, in YYYY-MM-DD format.')
    p.add_argument('stop_time', help='End of time period to download, in YYYY-MM-DD format.')
    p.add_argument('-s', '--save-dir', default='.',
                   help='Where to save the downloaded files. Default is the current directory.')
    p.add_argument('-c', '--no-decompress', action='store_false', dest='unzip',
                   help='By default the .zip files downloaded are unzipped into their .csv file. Pass this flag to '
                        'skip that and leave them as .zip files.')
    p.add_argument('-k', '--keep-zip', action='store_false', dest='delete_zip',
                   help='If the .zip files are decompresses, they are by default deleted. Pass this flag to skip '
                        'deleting them. This has no effect either way if --no-decompress is set.')
    p.set_defaults(driver_fxn=download_cl_driver)
    p.epilog = 'A note on the start and stop time: the hourly data is provided in monthly files and the daily data ' \
               'in quarterly files. The start/stop time given filter based on the first date of the files. That is, ' \
               'if you specify a start date of 15 Jan 2020 and an end date of 15 Feb 2020 for the hourly data, the ' \
               'file for February will be downloaded because 15 Jan <= 1 Feb <= 15 Feb, but the file for January will ' \
               'NOT be downloaded.'
