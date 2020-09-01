from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re
import urllib3

from typing import Optional

from ..caada_errors import HTMLParsingError, HTMLRequestError


def _convert_la_numbers(val):
    val = re.sub(r'[,%]', '', val.strip())
    try:
        return float(val)
    except ValueError:
        # This will handle empty cells (e.g. that haven't been filled yet) and misformatted cells (e.g. one number was
        # "2,406.662.05" - two decimal points)
        return np.nan


def get_la_port_container_data(year: int, index: str = 'datetime') -> pd.DataFrame:
    """Get Port of LA container data for a given year, return as a dataframe.

    Parameters
    ----------
    year
        The year to get data for. The Port of LA keeps monthly data for 1995 and on; years before 1995 will likely
        fail.

    index
        How to index the returned dataframe. `"datetime"` (the default) will create a datetime index; it will also
        remove the year total rows. `"table"` will keep the table's original index (as strings) and will retain the
        year summary rows.

    Returns
    -------
    pd.DataFrame
        A dataframe containing the data for the requested year.

    """
    if index == 'datetime':
        parse_year = year
    elif index == 'table':
        parse_year = None
    else:
        raise ValueError('"{}" is not one of the allowed values for index'.format(index))

    http = urllib3.PoolManager()
    r = http.request('GET', 'https://www.portoflosangeles.org/business/statistics/container-statistics/historical-teu-statistics-{:04d}'.format(year))
    if r.status == 200:
        return parse_la_port_html(r.data, parse_year)
    elif r.status == 404:
        # Page not found, usually because you asked for a year that isn't online
        raise HTMLRequestError('Failed to retrieve the Port of LA page for {}. Their server may be down, or the '
                               'year you requested may be out of range. Years before 1995 are not available.'.format(year))
    else:
        raise HTMLRequestError('Failed to retrieve the Port of LA page for {}. HTML response code was {}'.format(year, r.status))


def parse_la_port_html(html: str, year: Optional[int] = None):
    """Parse LA port container data from HTML into a dataframe.

    Parameters
    ----------
    html
        The raw HTML from the Port of LA "historical-teu-statistics" page.

    year
        Which year the page is for. If given, the returned dataframe will have a datetime index, and the year summary
        rows are removed. If not given, the dataframe uses the original table row labels (as strings) and retains the
        year summary rows.

    Returns
    -------
    pd.DataFrame
        The dataframe with the container data.
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Should be exactly one table on the page - find it
    table = soup('table')
    if len(table) != 1:
        raise HTMLParsingError('Expected exactly one table, got {}'.format(len(table)))
    else:
        table = table[0]

    # Get the rows of the table - the first will give us the header, the rest will give
    # us the data. Read it into a dict that can be easily converted to a dataframe
    tr_tags = table('tr')
    header = [tag.text.strip() for tag in tr_tags[0]('td')]
    header[-1] = '{} (%)'.format(header[-1])
    index = []
    df_dict = {k: [] for k in header[1:]}
    for row in tr_tags[1:]:
        row_data = [tag.text.strip() if i == 0 else _convert_la_numbers(tag.text) for i, tag in enumerate(row('td'))]
        index.append(row_data[0])

        for i, k in enumerate(header[1:], start=1):
            df_dict[k].append(row_data[i])

    df = pd.DataFrame(df_dict, index=index)

    # Lastly, convert the index to a datetime index if we were given the year. We'll check that the dataframe's first
    # 12 indices are the months
    if year is not None:
        start_date = '{:04d}-01'.format(year)
        end_date = '{:04d}-12'.format(year)
        date_index = pd.date_range(start_date, end_date, freq='MS')
        if index[:12] != date_index.strftime('%B').tolist():
            raise HTMLParsingError('First twelve rows of the table did not have month names as index')
        df = df.iloc[:12, :]
        df.index = date_index

    return df
