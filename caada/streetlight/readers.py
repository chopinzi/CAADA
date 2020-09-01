import geopandas as gpd
import pandas as pd

from .. import common_ancillary
from ..caada_typing import pathlike

# TODO: allow directly loading the Streetlight XLSX file if the excel package is installed


def load_streetlight_csv(filename: pathlike) -> gpd.GeoDataFrame:
    """Load the Streetlight VMT data from a .csv file as a Geodataframe with county geometry included

    Parameters
    ----------
    filename
        Path to the Streetlight VMT file. Note that at present it MUST be converted to a .csv file - directly loading
        the Excel file is not yet supported.

    Returns
    -------
    geopandas.GeoDataFrame
        A geodataframe with the VMT data, joined with the county geometry 
    """
    df = pd.read_csv(filename)
    df['datetime'] = pd.DatetimeIndex(df['ref_dt'])
    df.drop(columns=['ref_dt'], inplace=True)
    return _join_streetlight_with_geometry(df)


def _join_streetlight_with_geometry(st_df):
    gdf = common_ancillary.get_poly_gdf_subset(None, None)[['statefp', 'countyfp', 'geometry']]
    return gpd.GeoDataFrame(st_df.merge(gdf, on=['statefp', 'countyfp'], how='left'), crs=str(gdf.crs))