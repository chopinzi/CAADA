import pandas as pd
from pathlib import Path
import re
from typing import Sequence

from . import readers, exceptions

from ..caad_typing import \
    datetimelike as _datetimelike, \
    pathlike as _pathlike


def _get_avail_metadata(metadata_dir: _pathlike) -> pd.Series:
    metadata_dir = Path(metadata_dir)
    metadata_files = [f for f in metadata_dir.iterdir() if f.is_file() and f.suffix == '.txt']
    metadata_dates = [pd.to_datetime(re.search(r'\d{4}_\d{2}_\d{2}', f.stem).group(), format='%Y_%m_%d') for f in metadata_files]
    return pd.Series(metadata_files, index=pd.DatetimeIndex(metadata_dates)).sort_index()


def get_metadata_for_date(metadata_dir: _pathlike, date: _datetimelike) -> pd.DataFrame:
    # I don't totally understand how to match metadata up. For now I'm going to assume the file with the most recent
    # date before the given date is the one we want
    all_meta = _get_avail_metadata(metadata_dir)
    the_date = all_meta.index[all_meta.index <= date].max()
    return readers.read_pems_station_meta(all_meta[the_date])


def get_metadata_for_site_on_date(metadata_dir: _pathlike, site_id: int, date: _datetimelike):
    metadata_files = _get_avail_metadata(metadata_dir)
    possible_dates = metadata_files.index[metadata_files.index <= date]
    for mdate in reversed(possible_dates):
        meta_df = readers.read_pems_station_meta(metadata_files[mdate])
        if site_id in meta_df.index:
            meta = meta_df.loc[site_id, :].copy()
            meta['file'] = metadata_files[mdate]
            return meta

    raise exceptions.SiteMetadataError('Could not find site ID {} in any of the metadata files in {}'
                                       .format(site_id, metadata_dir))


def get_metadata_for_site_over_dates(metadata_dir: _pathlike, site_id: int, dates: Sequence[_datetimelike]):
    # Go through all the available metadata. Find all of the files that contain the requested site ID. Stash those
    # rows
    rows = []
    for file_date, file_name in _get_avail_metadata(metadata_dir).iteritems():
        meta_df = readers.read_pems_station_meta(file_name)
        if site_id in meta_df.index:
            rows.append((file_date, meta_df.loc[site_id, :]))
    row_dates, row_series = zip(*rows)
    meta_df = pd.concat(row_series, axis=1).T.reset_index(drop=True)
    row_dates = pd.DatetimeIndex(row_dates)
    meta_df.index = row_dates

    # interpolate to the requested dates, filling forward. Make sure to use the date before the start of the sequence
    # if it exists
    dates = pd.DatetimeIndex(dates)
    xx = row_dates < dates.min()
    if not xx.any():
        meta_df = meta_df.reindex(dates)
        meta_df.fillna(method='ffill', inplace=True)
    else:
        tmp_dates = pd.DatetimeIndex([row_dates[xx].max()] + dates.to_list())
        meta_df = meta_df.reindex(tmp_dates)
        meta_df.fillna(method='ffill', inplace=True)
        meta_df = meta_df.loc[dates, :]
    return meta_df


def get_metadata_for_multi_sites_on_date(metadata_dir: _pathlike, site_ids: Sequence[int], date: _datetimelike) -> pd.DataFrame:
    meta = get_metadata_for_date(metadata_dir, date)
    return meta[site_ids]
