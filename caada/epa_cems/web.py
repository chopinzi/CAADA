import ftplib
import os
import pandas as pd
from pathlib import Path
import re
from zipfile import ZipFile

from ..common_ancillary import conus_states
from ..caada_logging import logger
from ..caada_typing import datetimelike, pathlike


class EPAFTP(ftplib.FTP):
    """Class that manages a connection to the EPA FTP server.

    This wraps the standard :class:`ftplib.FTP` class but supplies the URLs by default and contains a helper
    :meth:`download` method to support batch downloading of Continuous Emission Monitoring System (CEMS) files.

    This can be used as a context manager::

        with EPAFTP() as ftp:
            ftp.download(...)

    This is encouraged because it ensures that the FTP connection is closed whether or not an error occurs.
    """
    def __init__(self, url: str = 'newftp.epa.gov', *args, **kwargs):
        """Instantiate a connection to the EPA FTP server

        Parameters
        ----------
        url
            The URL of the FTP server. Should not need changed.

        args, kwargs
            Additional positional and keyword arguments are passed through to :class:`ftplib.FTP`. No additional
            arguments should be required.
        """
        super(EPAFTP, self).__init__(url, *args, **kwargs)
        self.login()

    def download(self, time_res: str, start_time: datetimelike, stop_time: datetimelike, save_dir: pathlike,
                 states: str = 'all', unzip: bool = True, delete_zip: bool = True):
        """Download a collection of EPA CEMS files.

        Parameters
        ----------
        time_res
            Which time resolution of files to get. Options are "daily" or "hourly".

        start_time, stop_time
            Beginning and end of the time period to download data for. See Notes, below. This may be any format that
            :class:`pandas.Timestamp` recognizes as a valid input.

        save_dir
            Path to save the CEMS files to.

        states
            Which states to download data for. The string `"all"` will download all states, and `"conus"` will download
            only continental US states. If you want to limit to specific states, pass a sequence of state abbreviations,
            e.g. `("ca", "or", "wa")`.

        unzip
            Whether to unzip the .zip files after downloading.

        delete_zip
            Whether to delete the .zip files after extracting the contained .csv file. Has no effect if `unzip` is
            `False`.

        Notes
        -----
        Time filtering is done based on the start time of each file. Since the hourly data is organized into monthly
        files and the daily data in organized into quarterly files, a time range from 2020-03-15 to 2020-04-15 would
        download the April 2020 hourly file or Q2 daily file (because April 1, 2020 is the start date for both files),
        however it will *not* download the March 2020 hourly or Q1 2020 daily file, even though the first part of the
        date range overlaps those files.
        """
        save_dir = Path(save_dir)
        start_time = pd.Timestamp(start_time)
        stop_time = pd.Timestamp(stop_time)

        if not save_dir.is_dir():
            raise IOError('Save directory ({}) either does not exist or is a file.'.format(save_dir))

        if time_res == 'hourly':
            files = self._hourly_file_list(start_time, stop_time, states)
        elif time_res == 'daily':
            files = self._daily_file_list(start_time, stop_time, states)
        else:
            raise ValueError('Unknown option for time_res: "{}". Allowed values are "hourly", "daily".')

        for dir_url, fnames in files.items():
            logger.info('Downloading {} files from {}'.format(len(fnames), dir_url))
            self.cwd(dir_url)
            for f in fnames:
                cmd = 'RETR {}'.format(f)
                logger.debug('Downloading {} (command is {})'.format(f, cmd))
                with open(save_dir / f, 'wb') as wobj:
                    self.retrbinary(cmd, wobj.write)
                if unzip:
                    self._unzip_file(save_dir / f, delete_zip=delete_zip)

    def _hourly_file_list(self, start_time, stop_time, states='all'):
        url = '/DMDnLoad/emissions/hourly/monthly/'
        all_files = []
        for year in range(start_time.year, stop_time.year+1):
            self.cwd('{}{}'.format(url, year))
            all_files += self.nlst()

        file_info = []
        for f in all_files:
            fname = f.split('/')[-1]
            m = re.search(r'(\d{4})([a-z]{2})(\d{2})', fname, re.IGNORECASE)
            year, month, state = int(m.group(1)), int(m.group(3)), m.group(2)
            file_info.append({'name': fname, 'date': pd.Timestamp(year, month, 1), 'state': state.lower()})

        return self._filter_files(url, file_info, start_time, stop_time, states)

    def _daily_file_list(self, start_time, stop_time, states='all'):
        url = '/DMDnLoad/emissions/daily/quarterly/'
        all_files = []
        for year in range(start_time.year, stop_time.year+1):
            dir_url = '{}{}'.format(url, year)
            logger.debug('Changing remote directory to {}'.format(dir_url))
            self.cwd(dir_url)
            all_files += self.nlst()

        file_info = []
        for f in all_files:
            fname = f.split('/')[-1]
            m = re.search(r'(\d{4})([a-z]{2})(Q\d)', fname)
            year, quarter, state = int(m.group(1)), m.group(3), m.group(2)
            file_info.append({'name': fname, 'date': self._q_to_date(year, quarter), 'state': state.lower()})

        return self._filter_files(url, file_info, start_time, stop_time, states)

    @staticmethod
    def _filter_files(base_url, file_info, start_time, stop_time, states):
        if not base_url.endswith('/'):
            base_url += '/'
        if states == 'all':
            states = set([f['state'] for f in file_info])
        elif states == 'conus':
            states = conus_states
        states = [s.lower() for s in states]
        file_info = [f for f in file_info if start_time <= f['date'] <= stop_time and f['state'] in states]

        # Group the files by FTP directory so that we only have to cd to a directory once
        file_dict = dict()
        for f in file_info:
            dir_url = '{}{}'.format(base_url, f['date'].year)
            if dir_url not in file_dict:
                file_dict[dir_url] = []
            file_dict[dir_url].append(f['name'])

        return file_dict

    @staticmethod
    def _q_to_date(year, q):
        if q.lower() == 'q1':
            return pd.Timestamp(year, 1, 1)
        elif q.lower() == 'q2':
            return pd.Timestamp(year, 4, 1)
        elif q.lower() == 'q3':
            return pd.Timestamp(year, 7, 1)
        elif q.lower() == 'q4':
            return pd.Timestamp(year, 10, 1)
        else:
            return ValueError('Unknown value for quarter. Expected "qN" or "QN" where N is 1, 2, 3, or 4.')

    @staticmethod
    def _unzip_file(zip_path: Path, delete_zip):
        logger.debug('Decompressing {}'.format(zip_path))
        with ZipFile(zip_path) as z:
            for mem in z.infolist():
                if os.sep in mem.filename:
                    raise IOError('A member of {} contains path separators. This is unexpected and potentially unsafe.'.format(zip_path))
                out_path = z.extract(mem, path=zip_path.parent)
                logger.debug('Created {}'.format(out_path))

        if delete_zip:
            os.remove(zip_path)
            logger.debug('Deleted {}'.format(zip_path))


def download_cl_driver(time_res, start_time, stop_time, save_dir='.', unzip=True, delete_zip=True):
    with EPAFTP() as ftp:
        ftp.download(time_res=time_res, start_time=start_time, stop_time=stop_time, save_dir=save_dir,
                     unzip=unzip, delete_zip=delete_zip)
