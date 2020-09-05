import itertools
import netCDF4 as ncdf
import numpy as np
import pandas as pd
import toml

from jllutils.subutils import ncdf as ncio

from . import readers, _my_dir
from ..caada_logging import logger
from ..caada_typing import pathlike, pathseq, strseq


def summarize_and_merge_covid_files(filenames: pathseq, savename: pathlike):
    """Summarize Strohmeier et al. COVID-19 OpenSky files into a single netCDF file

    This will take a list of .csv files from `Strohmeier et al. <https://essd.copernicus.org/preprints/essd-2020-223/>`_
    and summarize them into a single netCDF file with the number of arrivals and departures from each airport for each
    day, further broken down into international, domestic, and all flights. Additional metadata about the airports
    is retrieved from `Openflights <https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat>`_
    and saved in the netCDF file.

    Parameters
    ----------
    filenames
        The list of .csv files to summarize

    savename
        The name to give the resulting netCDF file. Will be overwritten if already exists!

    Returns
    -------
    None

    Notes
    -----

    Airport information from `Openflights <https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat>`_
    is used to determine whether a flight is domestic or international. If an airport code is not included in the
    Openflights database, then flights to/from it cannot be properly categorized.

    """
    def reorder_list(orig_list, new_order):
        return [orig_list[i] for i in new_order]

    data = {'{}_{}'.format(end, group): [] for end, group in itertools.product(['departures', 'arrivals'], ['all', 'domestic', 'international'])}
    codes = []
    times = []

    for i, f in enumerate(filenames, start=1):
        logger.info('Reading %s (%d of %d)', f, i, len(filenames))
        counts, iaca_codes, these_times = summarize_opensky_covid_file(f, 'day', output='array')
        for end, end_dicts in counts.items():
            for group, group_counts in end_dicts.items():
                key = '{}_{}'.format(end, group)
                data[key].append(group_counts)

        codes.append(iaca_codes)
        times.append(these_times)

    logger.info('Done reading - %d files read', len(filenames))
    # Sort all the outputs by time
    sort_order = np.argsort([t[0] for t in times])
    for k, v in data.items():
        data[k] = reorder_list(v, sort_order)
    codes = reorder_list(codes, sort_order)
    times = reorder_list(times, sort_order)

    # Merge all codes and times
    all_codes = set()
    for some_codes in codes:
        all_codes.update(some_codes)
    all_codes = sorted(all_codes)

    dtindex = pd.DatetimeIndex([])
    for some_time in times:
        dtindex = dtindex.append(pd.DatetimeIndex(some_time))

    # Now simultaneously concatenate the data and account for different codes in different files
    final_data = dict()
    ntimes = dtindex.size
    ncodes = len(all_codes)
    for key, counts in data.items():
        final_data[key] = np.zeros([ntimes, ncodes], dtype=np.int32)
        for i, arr in enumerate(counts):
            code_inds = np.array([all_codes.index(c) for c in codes[i]]).reshape(1, -1)
            time_inds = np.flatnonzero(dtindex.isin(times[i])).reshape(-1, 1)
            final_data[key][time_inds, code_inds] = arr

    logger.info('Saving to %s', savename)
    save_covid_netcdf(savename=savename, data=final_data, times=dtindex, codes=all_codes)


def summarize_opensky_covid_file(filename: pathlike, avg_to: str, output: str = 'array'):
    """Create the summary of a single Strohmeier et al. .csv file

    Parameters
    ----------
    filename
        Path to the .csv file to summarize

    avg_to
        One of the strings "day" or "month", controls whether the summary returned sums up data over individual days
        or months.

    output
        Controls what is returned. Currently "array" is the only valid value here.

    Returns
    -------
    dict
        A dict of dicts, the first level will have keys "departures" and "arrivals" and the second level will have
        keys "all", "domestic", and "international". The values of the second levels are arrays whose first dimensions
        are time and whose second dimensions are airport. These are the number of arrivals or departures for each
        airport in the time frame requested.

    strseq
        The list of ICAO airport codes that correspond to the second dimension of the arrays.

    Sequence[pandas.Timestamp]
        The list of dates that correspond to the first dimension of the arrays. If "month" was given as the value for
        `avg_to`, then these will be the first date of each month.
    """
    df = readers.read_opensky_covid_file(filename)
    all_codes = set(df['origin'].dropna().tolist()).union(df['destination'].dropna().tolist())

    yr, mn = df['day'].iloc[0].year, df['day'].iloc[0].month
    if avg_to == 'day':
        groups = df['day'].dt.dayofyear
        date_fxn = lambda d, y=yr: pd.Timestamp(y - 1, 12, 31) + pd.Timedelta(days=d)
    elif avg_to == 'month':
        groups = df['day'].dt.month
        date_fxn = lambda m, y=yr: pd.Timestamp(y, m, 1)
    else:
        raise ValueError('Bad value for avg_to: {}'.format(avg_to))

    if output == 'dataframe':
        raise NotImplementedError('Summarizing to dataframe not yet implemented')
        #return _summarize_opensky_to_df(df, groups, all_codes, date_fxn)
    elif output == 'array':
        return _summarize_opensky_to_array(df, groups, all_codes, date_fxn)


def _summarize_opensky_to_array(df, groups, all_codes, date_fxn):
    all_codes = sorted(all_codes)

    ncode = len(all_codes)
    ndates = groups.unique().size

    count_arrs = {'departures': {k: np.zeros([ndates, ncode], dtype=np.int32) for k in ('all', 'domestic', 'international')},
                  'arrivals': {k: np.zeros([ndates, ncode], dtype=np.int32) for k in ('all', 'domestic', 'international')}}

    df['counter'] = 1  # use for sum
    xxdom = df['origin_country_name'].fillna('UORIG') == df['dest_country_name'].fillna('UDEST')
    dom_df = df[xxdom]
    intl_df = df[~xxdom]

    counts = {'departures':
                  {'all': df.groupby([groups, 'origin']).sum()['counter'],
                   'domestic': dom_df.groupby([groups, 'origin']).sum()['counter'],
                   'international': intl_df.groupby([groups, 'origin']).sum()['counter']},
              'arrivals':
                  {'all': df.groupby([groups, 'destination']).sum()['counter'],
                   'domestic': dom_df.groupby([groups, 'destination']).sum()['counter'],
                   'international': intl_df.groupby([groups, 'destination']).sum()['counter']}}

    origin_tinds = counts['departures']['all'].index.get_level_values(0)
    dest_tinds = counts['arrivals']['all'].index.get_level_values(0)

    unique_tinds = sorted(set(origin_tinds).union(dest_tinds))
    unique_times = [date_fxn(d) for d in unique_tinds]

    for i, t in enumerate(unique_tinds):
        for end, end_dicts in counts.items():
            for status, status_df in end_dicts.items():
                if status_df.index.get_level_values(0).isin([t]).any():
                    sub_df = status_df.xs(t).reindex(all_codes).fillna(0)
                    count_arrs[end][status][i, :] = sub_df.to_numpy()

    return count_arrs, all_codes, unique_times


def _summarize_opensky_to_df(df, groups, all_codes, date_fxn):
    # Note: not tested. Likely needs reworked.
    mi_tuples = []
    data = dict(origin_count=[], dest_count=[], latitude=[], longitude=[])

    n = groups.unique().size * len(all_codes)
    print(n)
    #pbar = miscutils.ProgressBar(n, prefix='Summarizing', style='bar+percent')
    for _, date_df in df.groupby(groups):
        this_date = date_fxn(date_df['day'].iloc[0])
        for code in all_codes:
            #pbar.print_bar()
            mi_tuples.append((this_date, code))
            this_dict = get_info(date_df, code)
            for k, v in this_dict.items():
                data[k].append(v)

    return pd.DataFrame(data, index=pd.MultiIndex.from_tuples(mi_tuples))


def get_info(df, code):
    def get_info_helper(od):
        key = 'destination' if od == 'dest' else od
        data = dict()

        xx = df[key] == code
        data['count'] = xx.sum()
        if xx.sum() == 0:
            data['latitude'], data['longitude'] = np.nan, np.nan
        else:
            data['latitude'] = df.loc[xx, '{}_latitude'.format(od)].iloc[0]
            data['longitude'] = df.loc[xx, '{}_longitude'.format(od)].iloc[0]

        return data

    origin_dict = get_info_helper('origin')
    dest_dict = get_info_helper('dest')
    lat = dest_dict['latitude'] if np.isnan(origin_dict['latitude']) else origin_dict['latitude']
    lon = dest_dict['longitude'] if np.isnan(origin_dict['longitude']) else origin_dict['longitude']
    return {'origin_count': origin_dict['count'], 'dest_count': dest_dict['count'], 'longitude': lon, 'latitude': lat}


def save_covid_netcdf(savename, data, times, codes):
    # Read in the NC attributes from the TOML file and ancillary data
    with open(_my_dir / 'ncattrs.toml') as f:
        ncatts = toml.load(f)['opensky-covid']

    ancillary_df = readers.read_airport_codes().set_index('icao_code').reindex(codes)
    ancillary_varinfo = {'iata_code': ('iata_code', '', 'U'),
                         'airport_name': ('airport_name', '', 'U'),
                         'city_name': ('airport_city', '', 'U'),
                         'country_name': ('airport_country', '', 'U'),
                         'latitude': ('airport_latitude', np.nan, 'float32'),
                         'longitude': ('airport_longitude', np.nan, 'float32')}

    def get_atts(var):
        return ncatts.get(var, dict())

    with ncdf.Dataset(savename, 'w') as ds:
        # Dimensions first
        timedim = ncio.make_nctimedim_helper(ds, 'time', times)
        apdim = ncio.make_ncdim_helper(ds, 'airport', np.array(codes), **get_atts('airport'))

        # Then regular variables
        for varname, vardata in data.items():
            ncio.make_ncvar_helper(ds, varname, vardata, (timedim, apdim), **get_atts(varname))

        # Finally build up ancillary data: IATA code, airport name, airport lat/lon, etc.
        for colname, (varname, varfill, vartype) in ancillary_varinfo.items():
            logger.debug('Adding ancillary data: %s', varname)
            coldata = ancillary_df[colname].fillna(varfill).to_numpy().astype(vartype)
            ncio.make_ncvar_helper(ds, varname, coldata, ('airport',), **get_atts(varname))
