import geopandas as gpd
import netCDF4 as ncdf
import numpy as np
import os
import pandas as pd
from typing import Sequence, Optional, Union
from ..caada_typing import intseq

from jllutils.subutils import ncdf as ncio

_county_shapefile = os.path.join(os.path.dirname(__file__), 'county_shp_files', 'cb_2018_us_county_20m.shp')
_county_gdf = gpd.read_file(_county_shapefile)
_county_gdf.rename(columns=lambda s: s.lower(), inplace=True)
_county_gdf['statefp'] = _county_gdf['statefp'].astype('int')
_county_gdf['countyfp'] = _county_gdf['countyfp'].astype('int')

_state_shapefile = os.path.join(os.path.dirname(__file__), 'state_shp_files', 'cb_2018_us_state_20m.shp')
_state_gdf = gpd.read_file(_state_shapefile)
_state_gdf.rename(columns=lambda s: s.lower(), inplace=True)
_state_gdf.sort_values('name', inplace=True)
_state_gdf['statefp'] = _state_gdf['statefp'].astype('int')

conus_states = ('AL', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'ID',
                'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI',
                'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY',
                'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN',
                'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY')


def _standardize_input_ids(county_ids, state_ids):
    if county_ids is None and state_ids is None:
        county_ids = [county_ids]
        state_ids = [state_ids]
    elif isinstance(county_ids, (int, type(None))):
        county_ids = [county_ids]
        if state_ids is not None and not isinstance(state_ids, int):
            county_ids *= len(state_ids)
    if state_ids is None or isinstance(state_ids, int):
        state_ids = [state_ids] * len(county_ids)
    elif len(state_ids) != len(county_ids):
        raise ValueError('Either provide a single state ID for all counties (as an integer) or a sequence the same '
                         'length as county_ids')
    return county_ids, state_ids


def get_county_polygons(county_ids: Optional[intseq], state_ids: Union[int, intseq]):
    """Get a dataframe with the polygons or multipolygons representing county borders

    The returned dataframe will have the county polygons for each county listed. `county_ids` and `state_ids` may both
    be scalar integers or lists of integers. If both are lists, then then must be the same length. Each county is drawn
    from the corresponding state in the list. If one is a scalar, it will be used for every element in the other, e.g.
    if `state_ids = 6` then 6 will be used as the state for every county listed in `county_ids`. If you want two
    counties from state 1 and three from state 2, then you would pass `county_ids = [a1, b1, c1, a2, b2]` and
    `state_ids = [1, 1, 1, 2, 2]`.

    Parameters
    ----------
    county_ids
        The numeric census IDs of counties to get polygons for. May be an integer, `None`, or sequence of both. If
        `None`, then all counties for each state listed will be returned. If `None` is given as an element of the
        list, then all counties for the corresponding state are returned.

    state_ids
        The numeric census IDs of states that each county belongs in. These may not be `None` and must be an integer
        or list of integers.

    Returns
    -------
    List[Polygons]
        The list of Shapely polygons corresponding to the counties requested.

    """
    gdf_subset = get_poly_gdf_subset(county_ids, state_ids)
    return gdf_subset['geometry'].tolist()


def get_poly_gdf_subset(county_ids: Optional[intseq], state_ids: Union[int, intseq]):
    county_ids, state_ids = _standardize_input_ids(county_ids, state_ids)
    polys = []
    for cid, sid in zip(county_ids, state_ids):
        if sid is None:
            xx = (_county_gdf['statefp'] > -99)
        else:
            xx = (_county_gdf['statefp'] == sid)
        if cid is not None:
            xx &= (_county_gdf['countyfp'] == cid)

        polys.append(_county_gdf.loc[xx, :])
    return pd.concat(polys, axis=0)


def get_state_polygons(state_ids, as_gdf=False):
    if isinstance(state_ids, int) or state_ids is None:
        state_ids = [state_ids]

    polys = []
    for sid in state_ids:
        if sid is None:
            continue

        xx = _state_gdf['statefp'] == sid
        if xx.sum() != 1:
            raise IndexError('Expected 1 match for state ID = {}, instead got {}'.format(sid, xx.sum()))
        elif as_gdf:
            polys.append(_state_gdf.index[xx].item())
        else:
            polys.append(_state_gdf.loc[xx, 'geometry'].item())
    if as_gdf and len(polys) > 0:
        return _state_gdf.loc[polys, :]
    elif as_gdf:
        return _state_gdf
    elif len(polys) > 0:
        return polys
    else:
        return _state_gdf['geometry'].tolist()


def geometry_to_lat_lon(geo):
    if geo.geom_type == 'MultiPolygon':
        lats = []
        lons = []
        for g in geo.geoms:
            y, x = geometry_to_lat_lon(g)
            lons.append(x)
            lats.append(y)
            lons.append(np.array([np.nan]))
            lats.append(np.array([np.nan]))
        # There will always be an extra NaN at the end we don't need to concatenate
        lats = np.concatenate(lats[:-1], axis=0)
        lons = np.concatenate(lons[:-1], axis=0)
    elif geo.geom_type == 'Polygon':
        lons, lats = zip(*geo.exterior.coords)
        lons = np.array(lons)
        lats = np.array(lats)
    else:
        raise NotImplementedError('Cannot convert geometry of type "{}"'.format(geo.geom_type))

    return lats, lons


def add_county_polys_to_ncdf(nch: ncdf.Dataset, county_ids: Sequence[int], state_ids: Sequence[int],
                             county_dimension: str = 'county'):
    polys = get_county_polygons(county_ids, state_ids)

    # Convert to an array of lat/lon
    poly_latlon = np.empty([len(polys), 2], object)
    for i, p in enumerate(polys):
        lat, lon = geometry_to_lat_lon(p)
        poly_latlon[i, 0] = lat.astype('float32')
        poly_latlon[i, 1] = lon.astype('float32')

    # Create 2 variables: one for the county bounds lat/lon as numbers and one for the "well known text" representation
    vlen_t = nch.createVLType(np.float32, 'county_bounds_vlen')
    ncio.make_ncdim_helper(nch, 'bounds_coord', np.array([0, 1]),
                           description='Index for shape bounds. 0 = latitude, 1 = longitude.')
    bounds_var = nch.createVariable("county_bounds", vlen_t, (county_dimension, 'bounds_coord'))
    bounds_var[:] = poly_latlon
    bounds_var.setncattr('crs', str(_county_gdf.crs))
    bounds_var.setncattr('description', "The latitude and longitude of each county's boundaries")
    bounds_var.setncattr('note', 'If fill values are present, they indicate breaks between coordinates for unconnected polygons')

    wkt_var = nch.createVariable('county_bounds_wkt', str, county_dimension)
    for i, p in enumerate(polys):
        # assume the polys are in the same order as the county IDs - the county IDs MUST be given in the order they
        # are in the netCDF file
        wkt_var[i] = p.to_wkt()
    wkt_var.setncattr('crs', str(_county_gdf.crs))
    wkt_var.setncattr('description', 'The county shape described in the CRS well known text format')
