import os
from pandas import Timedelta
import requests
import time

from . import get_airport_code_source
from ..caada_errors import HTMLRequestError
from ..caada_typing import pathlike
from ..caada_logging import logger


def _download_airport_codes(source='openflights', update='never'):
    """Download geographic data linked to airport codes.

    Parameters
    ----------
    source
        Which web source to pull data from. Currently the only allowed option is `"openflights"`.

    update
        Controls whether CAADA redownloads the needed data or not. Possible values are:

            * `"never"` - only download if no local copy is available.
            * `"periodically"` - only download if the local copy is more than a week old.
            * `"always"` - always redownloads

    Returns
    -------
    None
    """
    entry = get_airport_code_source(source)
    local_file = entry['local']
    remote_url = entry['remote']
    _download_airport_code_data(source, local_file, remote_url, update)


def _download_airport_code_data(source_name: str, local_file: pathlike, remote_url: str, update: str = 'never'):
    """General driver for geographic airport data in .csv format.

    Parameters
    ----------
    source_name
        Name the user passes to identify this source.

    local_file
        Path to where the local file is or should be

    remote_url
        URL to where the data is on the web

    update
        Controls whether CAADA redownloads the needed data or not. Possible values are:

            * `"never"` - only download if no local copy is available.
            * `"periodically"` - only download if the local copy is more than a week old.
            * `"always"` - always redownloads

    Returns
    -------
    None
        Returns nothing, downloads the file to `local_file`.
    """
    if update == 'never':
        if local_file.exists():
            logger.debug('%s already exists', local_file)
            return
        else:
            logger.info('%s does not exist, must download', local_file)
    elif update == 'periodically':
        if local_file.exists():
            mtime = os.path.getmtime(local_file)
            age = time.time() - mtime
            td = str(Timedelta(seconds=age))
            if age < 7*24*3600:
                # don't update if it's been modified within the last week
                logger.debug('%s recently updated (%s old), not updating', local_file, td)
                return
            else:
                logger.debug('%s more than 7 days old (%s old), will update', local_file, td)
    elif update != 'always':
        raise ValueError('Bad value for update: "{}". Options are "never", "periodically", and "always".'.format(update))

    logger.info('Downloading %s to %s', remote_url, local_file)
    r = requests.get(remote_url)
    if r.status_code != 200:
        raise HTMLRequestError('Error retrieving {} airport codes. HTTP status code was {}'.format(source_name, r.status_code))

    with open(local_file, 'wb') as wobj:
        wobj.write(r.content)
    logger.info('Download successful.')
