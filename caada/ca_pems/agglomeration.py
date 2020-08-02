import netCDF4 as ncdf
import numpy as np
import pandas as pd
from pathlib import Path
import re
import time

from jllutils.subutils import ncdf as ncio
from jllutils.miscutils import ProgressMessage

from . import readers, metadata, ancillary
from .. import common_utils, common_ancillary
from typing import Optional
from ..caada_errors import \
    DimensionError
from ..caada_typing import \
    pathlike as _pathlike, \
    scalarnum as _scalarnum, \
    strseq as _strseq


# TODO: deal with missing days/days with below the min_percent_observed. Need to normalize the data in some way so that
#  counties that happened to have more days/stations that fell below this threshold aren't undercounted.
# TODO: make this its own repo and record commit info in the netCDF file. I wrote a VCS module somewhere, use that.

def agglomerate_by_country(pems_root: _pathlike, meta_root: _pathlike, save_path: _pathlike,
                           min_percent_observed: _scalarnum = 75, variables: _strseq = ('samples', 'total flow')):
    pems_root = Path(pems_root)
    meta_root = Path(meta_root)
    save_path = Path(save_path)

    # Iterate over districts; each county should be entirely contained within districts
    data = []
    for district_data_dir in pems_root.iterdir():
        if not re.match(r'd\d\d', district_data_dir.name):
            continue
        district_meta_dir = meta_root / district_data_dir.name
        print('Agglomerating data from {}'.format(district_data_dir))
        print('Using metadata from {}'.format(district_meta_dir))
        this_data = _agglomerate_district_to_counties(district_data_dir, district_meta_dir, min_percent_observed=min_percent_observed)
        if this_data is not None:
            data.append(this_data)

    # Memory wasteful, but much easier to implement
    all_district_df = pd.concat(data, axis=0)
    data_arrays, dates, counties = _sum_data_to_counties(all_district_df, variables)
    _save_county_file(data_dict=data_arrays, dates=dates, county_ids=counties, save_path=save_path,
                      min_percent_observed=min_percent_observed)


def _agglomerate_district_to_counties(pems_district_root: _pathlike, meta_district_root: _pathlike,
                                      min_percent_observed: _scalarnum = 75):
    # Load all the individual month's files
    full_df = []
    print('Loading files...', end=' ')
    for stn_file in pems_district_root.iterdir():
        if not re.match(r'd\d\d.*\.txt', stn_file.name):
            continue

        this_df = readers.read_pems_station_csv(stn_file)
        # Eliminate rows with a percent observed less that allowed
        xx = this_df['percent observed'] >= min_percent_observed
        full_df.append(this_df[xx])

    print('{} files loaded.'.format(len(full_df)))
    if len(full_df) == 0:
        return None

    full_df = pd.concat(full_df, axis=0)

    print('Adding county IDs...', end=' ')
    _add_county_ids(full_df, meta_district_root)
    print('Done.')

    # Group by counties, compute both the total vehicles/day
    xx = full_df['county id'] >= 0
    full_df = full_df[xx]
    return full_df


def _add_county_ids(df: pd.DataFrame, metadata_dir: _pathlike):
    df['county id'] = -99
    for sid, sid_df in df.groupby('station'):
        times = sid_df['timestamp'].unique()
        meta_df = metadata.get_metadata_for_site_over_dates(metadata_dir, sid, times)
        df.loc[df['station'] == sid, 'county id'] = meta_df.loc[sid_df['timestamp'], 'county'].to_numpy()

    # Make sure that NaNs are fill values
    xx = df['county id'].isna()
    df.loc[xx, 'county id'] = -99
    df['county id'] = df['county id'].astype('int16')


def _sum_data_to_counties(full_df, variables):
    dates = full_df['timestamp'].unique()
    dates.sort()
    counties = full_df['county id'].unique()
    counties.sort()

    shape = [counties.size, dates.size]
    data_dict = {var: np.full(shape, np.nan) for var in variables}

    sum_df = full_df.groupby(['timestamp', 'county id']).sum()
    for i, d in enumerate(dates):
        sub = sum_df.xs(d).reindex(counties)
        for var in variables:
            data_dict[var][:, i] = sub[var].to_numpy()

    return data_dict, dates, counties


def _save_county_file(data_dict: dict, dates: np.ndarray, county_ids: np.ndarray, save_path: _pathlike,
                      min_percent_observed: _scalarnum):
    variable_info = {'samples': ('num_samples', dict(units='#',
                                                     pems_description='Total number of samples received for all lanes',
                                                     description='Total number of samples summed over all stations in each county.')),
                     'total flow': ('num_vehicles', dict(units='vehicles/day',
                                                         pems_description='Sum of hourly flows over the day. Note that the basic 5-minute rollup normalizes flow by the number of good samples received from the controller.',
                                                         description='Total number of vehicles per day summed over all stations in each county.'),)}
    with ncdf.Dataset(save_path, 'w') as ds:
        # Start with the dimensions - time and counties
        time = ncio.make_nctimedim_helper(ds, 'time', dates, time_units='hours')
        county = ncio.make_ncdim_helper(ds, 'county_id', county_ids,
                                        description='County that the traffic counts belong to, represented by '
                                                    'the census ID')

        # Add the county names
        county_names = ds.createVariable('county_name', str, county.name)
        for i, c in enumerate(county_ids):
            county_names[i] = ancillary.get_county_name(c)

        # Add county bounds. Use state ID = 6 for California - this function is only intended for CA PEMS
        # If used for other states, this will need updated.
        common_ancillary.add_county_polys_to_ncdf(ds, county_ids=county_ids, state_ids=6, county_dimension='county_id')

        # Add the data variables
        for varkey, vararray in data_dict.items():
            varname, varattrs = variable_info[varkey]
            ncio.make_ncvar_helper(ds, varname, vararray, [county, time], **varattrs)

        # Add global attributes
        ds.setncattr('min_percent_observed_required', float(min_percent_observed))
        ds.setncattr('variable_attr_help', "The `pems_description` attribute contains the description of that variable's"
                                           "raw form in the Caltrans PEMS online database. The `description` attribute "
                                           "describes the calculations done to aggregate it for this file.")
        common_utils.add_caad_info(ds)
