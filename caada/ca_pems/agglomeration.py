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
_county_id_fill = -99
_variable_info = {'samples': ('num_samples', dict(units='#',
                                                  pems_description='Total number of samples received for all lanes',
                                                  description='Total number of samples summed over all stations in each county.')),
                  'total flow': ('num_vehicles', dict(units='vehicles/day',
                                                      pems_description='Sum of hourly flows over the day. Note that the basic 5-minute rollup normalizes flow by the number of good samples received from the controller.',
                                                      description='Total number of vehicles per day summed over all stations in each county.'),)}


def agglomerate_by_country(pems_root: _pathlike, meta_root: _pathlike, save_path: _pathlike, time_res: str,
                           min_percent_observed: _scalarnum = 75, variables: _strseq = ('samples', 'total flow')):
    pems_root = Path(pems_root)
    meta_root = Path(meta_root)
    save_path = Path(save_path)

    began_at = time.time()
    with ncdf.Dataset(save_path, 'w') as nh:
        time_index, county_index = _init_county_file(nh, pems_root=pems_root, variables=variables, time_res=time_res,
                                                     min_percent_observed=min_percent_observed)

        #pmsg = ProgressMessage(format='Loading file {idx}, {filename}: {action}', auto_advance=False)
        file_idx = 0
        for stn_file, meta_dir in _iter_pems_files(pems_root, meta_root):
            #pmsg.print_message(file_idx, filename=stn_file.name, action='')
            stn_sum, stn_dates, stn_counties = _agglomerate_district_to_counties(
                stn_file, meta_dir, time_res=time_res, variables=variables, min_percent_observed=min_percent_observed)
            _insert_data_in_nc_file(nh=nh, data_dict=stn_sum, stn_times=stn_dates, stn_counties=stn_counties,
                                    nc_times=time_index, nc_counties=county_index, stn_file=stn_file)
        #pmsg.finish()

        time_elapsed = pd.Timedelta(seconds=time.time() - began_at)
        print('Finished writing traffic data to {} in {}'.format(save_path, time_elapsed))


def _iter_pems_files(pems_root: Path, meta_root: Path):
    for district_data_dir in pems_root.iterdir():
        if not re.match(r'd\d\d$', district_data_dir.name) or not district_data_dir.is_dir():
            continue

        district_meta_dir = meta_root / district_data_dir.name
        for stn_file in district_data_dir.iterdir():
            if not re.match(r'd\d\d.*\.txt', stn_file.name) or not stn_file.is_file():
                continue

            yield stn_file, district_meta_dir


def _create_datetime_index(pems_root: Path, time_res: str):
    start_datetime = None
    end_datetime = None
    for data_file, _ in _iter_pems_files(pems_root, Path('n/a')):
        # Read the first and last lines of the file
        with open(data_file, 'r') as robj:
            start_line = robj.readline()
            for end_line in robj:
                pass

            file_start = pd.Timestamp(start_line.split(',')[0])
            file_end = pd.Timestamp(end_line.split(',')[0])

            if start_datetime is None or file_start < start_datetime:
                start_datetime = file_start
            if end_datetime is None or file_end > end_datetime:
                end_datetime = file_end

    start_datetime = start_datetime.floor(time_res)
    end_datetime = end_datetime.floor(time_res)
    return pd.date_range(start_datetime, end_datetime, freq=time_res)


def _agglomerate_district_to_counties(stn_file: Path, meta_district_root: Path, time_res: str, variables: _strseq,
                                      min_percent_observed: _scalarnum = 75, pmsg: Optional[ProgressMessage] = None):

    if pmsg is None:
        pmsg = ProgressMessage(format='Loading file {filename}: {action}')
        finish_msg = True
    else:
        finish_msg = False

    pmsg.print_message(filename=stn_file.name, action='reading file')
    df = readers.read_pems_station_csv(stn_file)

    # Eliminate rows with a percent observed less that allowed
    xx = df['percent observed'] >= min_percent_observed
    df = df[xx]

    pmsg.print_message(filename=stn_file.name, action='matching counties')
    _add_county_ids(df, meta_district_root)

    pmsg.print_message(filename=stn_file.name, action='summing to counties')
    df['timestamp'] = pd.DatetimeIndex(df['timestamp']).floor(time_res)
    sum_dict, dates, counties = _sum_data_to_counties(df, variables)

    if finish_msg:
        pmsg.print_message(filename=stn_file.name, action='complete.')
        pmsg.finish()

    return sum_dict, dates, counties


def _add_county_ids(df: pd.DataFrame, metadata_dir: _pathlike):
    df['county id'] = _county_id_fill
    for sid, sid_df in df.groupby('station'):
        times = sid_df['timestamp'].unique()
        meta_df = metadata.get_metadata_for_site_over_dates(metadata_dir, sid, times)
        df.loc[df['station'] == sid, 'county id'] = meta_df.loc[sid_df['timestamp'], 'county'].to_numpy()

    # Make sure that NaNs are fill values
    xx = df['county id'].isna()
    df.loc[xx, 'county id'] = _county_id_fill
    df['county id'] = df['county id'].astype('int16')


def _sum_data_to_counties(full_df, variables):
    dates = full_df['timestamp'].unique()
    dates.sort()
    counties = full_df['county id'].unique()
    counties.sort()

    shape = [counties.size, dates.size]
    sum_dict = {var: np.full(shape, np.nan) for var in variables}
    mean_dict = {var: np.full(shape, np.nan) for var in variables}

    sum_df = full_df.groupby(['timestamp', 'county id']).sum()
    for i, d in enumerate(dates):
        sub_sum = sum_df.xs(d).reindex(counties)
        for var in variables:
            sum_dict[var][:, i] = sub_sum[var].to_numpy()

    return sum_dict, dates, counties


def _init_county_file(nh: ncdf.Dataset, pems_root, variables, time_res, min_percent_observed):
    # Get all counties in California (state_id = 6) and write the county bounds in both numeric and WKT format after
    # initializing dimensions. Time will be an unlimited dimension so that it can grow as needed with each file read in.
    time_index = _create_datetime_index(pems_root, time_res)
    county_gdf = common_ancillary.get_poly_gdf_subset(None, 6)
    county_gdf.sort_values('name', inplace=True)
    county_ids = county_gdf['countyfp'].to_numpy().astype('int16')

    time_dim = ncio.make_nctimedim_helper(nh, 'time', time_index, time_units='hours')
    county_dim = ncio.make_ncdim_helper(nh, 'county_id', county_ids,
                                        description='County that the traffic counts belong to, represented by census ID')

    # Add the county names
    county_names = nh.createVariable('county_name', str, county_dim.name)
    for i, c in enumerate(county_ids):
        county_names[i] = ancillary.get_county_name(c)

    # Add county bounds. Use state ID = 6 for California - this function is only intended for CA PEMS
    # If used for other states, this will need updated.
    common_ancillary.add_county_polys_to_ncdf(nh, county_ids=county_ids, state_ids=6, county_dimension=county_dim.name)

    # Create empty data variables that will expand as we add times
    for varkey in variables:
        varname, varattrs = _variable_info[varkey]
        this_var = nh.createVariable(varname, 'double', (county_dim.name, time_dim.name))
        this_var.setncatts(varattrs)

    # Add global attributes
    nh.setncattr('min_percent_observed_required', float(min_percent_observed))
    nh.setncattr('variable_attr_help', "The `pems_description` attribute contains the description of that variable's"
                                       "raw form in the Caltrans PEMS online database. The `description` attribute "
                                       "describes the calculations done to aggregate it for this file.")
    common_utils.add_caada_info(nh)

    return time_index, county_ids


def _match_subset_with_nc_dims(stn_times: np.ndarray, stn_counties: np.ndarray, nc_times: pd.DatetimeIndex,
                               nc_counties: np.ndarray, filename: Path):
    xx_time = nc_times.isin(stn_times)
    if xx_time.sum() != stn_times.size:
        raise DimensionError('Failed to match times from {} to the netCDF time dimension'.format(filename.name))

    xx_county = np.isin(nc_counties, stn_counties)
    if xx_county.sum() != stn_counties.size:
        raise DimensionError('Failed to match counties from {} to the netCDF county ID dimension'.format(filename.name))

    return xx_county, xx_time


def _insert_data_in_nc_file(nh: ncdf.Dataset, data_dict: dict, stn_times: np.ndarray, stn_counties: np.ndarray,
                            nc_times: pd.DatetimeIndex, nc_counties: np.ndarray, stn_file: Path):

    xx_county, xx_time = _match_subset_with_nc_dims(stn_times=stn_times, stn_counties=stn_counties,
                                                    nc_times=nc_times, nc_counties=nc_counties,
                                                    filename=stn_file)
    for varkey, vararray in data_dict.items():
        varname, _ = _variable_info[varkey]
        nh.variables[varname][xx_county, xx_time] = vararray
