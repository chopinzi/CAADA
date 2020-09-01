import numpy as np
import pandas as pd
from jllutils import miscutils


def _load_google_mobility(mobility_file):
    df = pd.read_csv(mobility_file)
    for k in ('country_region_code', 'country_region', 'sub_region_1', 'sub_region_2', 'date'):
        df[k].fillna('', inplace=True)
    return df


def _get_matching_google_rows(google, sub_df):
    country = sub_df['administrative_area_level_1'].unique().item()
    key_parts = [p.strip() for p in key.split(',')]
    xx = (google['country_region'] == country) & (google['sub_region_1'] == key_parts[0])
    if len(key_parts) == 2:
        xx &= google['sub_region_2'] == key_parts[1]
    elif len(key_parts) > 2:
        raise NotImplementedError('Case where google mobility key has >2 parts is not implemented')

    # Get the relevant lines from the google dataframe, index by date, then reindex to match the restriction
    # order
    sub_google = google[xx].copy()
    restr_dates = pd.DatetimeIndex(sub_df['date'])
    sub_google.index = pd.DatetimeIndex(sub_google['date'])
    sub_google = sub_google.reindex(restr_dates)
    return sub_google


def _match_restr_to_google(restr, google):
    restr['key_google_mobility'].fillna('', inplace=True)
    unit = 'percent_change_from_baseline'
    google_data_keys = {k: k.replace(unit, 'google') for k in google.columns if 'percent_change_from_baseline' in k}
    restr['google_match_flag'] = -1
    for new_key in google_data_keys.values():
        restr[new_key] = np.nan

    pbar = miscutils.ProgressBar(restr['key_google_mobility'].unique().size, prefix='Matching')
    for key, sub_df in restr.groupby('key_google_mobility'):
        pbar.print_bar()
        xx_main = restr.index.isin(sub_df.index)
        if len(key) == 0:
            # No google mobility key - cannot match
            restr.loc[xx_main, 'google_match_flag'] = 1
            continue

        sub_google = _get_matching_google_rows(google, sub_df)

        if sub_google.shape[0] == 0:
            restr.loc[xx_main, 'google_match_flag'] = 2
            continue

        restr.loc[xx_main, 'google_match_flag'] = 0
        for orig_key, new_key in google_data_keys.items():
            restr.loc[xx_main, new_key] = sub_google[orig_key].to_numpy()

    pbar.finish()


def _apple_region_mobility_transpose(sub_df):
    if sub_df['transportation_type'].unique().size != sub_df['transportation_type'].size:
        raise ValueError('transportation_types are not unique')

    # Find the first date column.
    found_dates = False
    for icol, col in enumerate(sub_df.columns):
        if re.match(r'\d\d\d\d-\d\d-\d\d', col):
            found_dates = True
            break
    if not found_dates:
        raise ValueError('Did not find date columns')
    dates = pd.DatetimeIndex(sub_df.columns[icol:])
    data = dict()
    for col in sub_df.columns[:icol]:
        if col != 'transportation_type':
            # This should error if the values differ across the rows
            try:
                data[col] = sub_df[col].unique().item()
            except ValueError:
                raise ValueError('{} was not the same for all rows of the sub dataframe'.format(col))

    for _, row in sub_df.iterrows():
        data[row['transportation_type']] = row.iloc[6:].to_numpy()

    return pd.DataFrame(data, index=dates)


def merge_datahub_and_mobility(datahub_csv, apple_csv, google_csv):
    datahub_df = pd.read_csv(datahub_csv)
    apple_df = pd.read_csv(apple_csv)
    google_df = _load_google_mobility(google_csv)

    _match_restr_to_google(datahub_df, google_df)
    # TODO: log unmatched rows?
