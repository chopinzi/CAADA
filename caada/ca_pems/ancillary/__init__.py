import os
import pandas as pd
from pathlib import Path

_mydir = Path(os.path.dirname(__file__))
_ca_counties = pd.read_csv(_mydir / 'st06_ca_cou.txt', header=None)
_ca_counties.columns = ['state', 'state_id', 'county_id', 'county', '?']


def get_county_name(county_id: int):
    xx = _ca_counties['county_id'] == county_id
    if not xx.any():
        raise KeyError('No county found with ID={}'.format(county_id))
    else:
        return _ca_counties[xx]['county'].item()
