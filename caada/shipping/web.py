from bs4 import BeautifulSoup, element as bs4_element
import numpy as np
import pandas as pd
import re
import requests

from typing import Optional

from .readers import parse_oakland_excel

from ..caada_typing import stringlike
from ..caada_errors import HTMLParsingError, HTMLRequestError
from ..caada_logging import logger

##############
# PORT OF LA #
##############


def _convert_la_numbers(val):
    # If there happens to be a ',' two characters from the end, it should probably be a decimal point.
    val = re.sub(r',\d\d$', '.', val.strip())
    # Then just remove the remaining commas plus any percent signs
    val = re.sub(r'[,%]', '', val)
    try:
        return float(val)
    except ValueError:
        # This will handle empty cells (e.g. that haven't been filled yet) and misformatted cells (e.g. one number was
        # "2,406.662.05" - two decimal points)
        return np.nan


def get_all_la_port_container_data(index: str = 'datetime') -> pd.DataFrame:
    this_year = pd.Timestamp.now().year
    dfs = []
    for yr in range(1995, this_year+1):
        dfs.append( get_la_port_container_data(yr, index=index) )

    return pd.concat(dfs, axis=0)


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

    r = requests.get('https://www.portoflosangeles.org/business/statistics/container-statistics/historical-teu-statistics-{:04d}'.format(year))
    if r.status_code == 200:
        return parse_la_port_html(r.content, parse_year)
    elif r.status_code == 404:
        # Page not found, usually because you asked for a year that isn't online
        raise HTMLRequestError('Failed to retrieve the Port of LA page for {}. Their server may be down, or the '
                               'year you requested may be out of range. Years before 1995 are not available.'.format(year))
    else:
        raise HTMLRequestError('Failed to retrieve the Port of LA page for {}. HTML response code was {}'.format(year, r.status_code))


def parse_la_port_html(html: stringlike, year: Optional[int] = None) -> pd.DataFrame:
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
    header = [_stdize_la_table_header(tag.text) for tag in tr_tags[0]('td')]
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

    _check_la_sums(df, year)

    return df


def _stdize_la_table_header(column_header: str):
    parts = column_header.strip().split()
    if len(parts) == 0:
        return ''
    elif len(parts) == 2:
        if re.search(r'load', parts[0], re.IGNORECASE):
            parts[0] = 'Full'
        elif re.search(r'empty', parts[0], re.IGNORECASE):
            parts[0] = 'Empty'
        elif re.search(r'total', parts[0], re.IGNORECASE):
            parts[0] = 'Total'
        else:
            raise HTMLParsingError('Unknown LA container table header: {}'.format(parts[0]))

        if re.search(r'import', parts[1], re.IGNORECASE):
            parts[1] = 'Imports'
        elif re.search(r'export', parts[1], re.IGNORECASE):
            parts[1] = 'Exports'
        elif re.search(r'teu', parts[1], re.IGNORECASE):
            parts[1] = 'TEUs'
        else:
            raise HTMLParsingError('Unknown LA container table header: {}'.format(parts[0]))

        return ' '.join(parts)
    elif len(parts) == 3 and re.search(r'change', column_header, re.IGNORECASE):
        return 'Prior Year Change (%)'
    else:
        raise HTMLParsingError('Unexpected LA container table header: {}'.format(column_header))


def _check_la_sums(la_df: pd.DataFrame, year):
    def check(total_col, col1, col2):
        return (la_df[total_col] - (la_df[col1] + la_df[col2])).abs().max() <= 1
    # The 1995 LA container table erroneously put "Total TEUs" in the header but then meant "Total Exports". So check
    # their sums for parity, and fix that year
    if year == 1995:
        logger.warning('1995 LA container table has known issue of mislabeled Total Exports and Total TEUs - fixing')
        _fix_la_1995(la_df)

    if not check('Total Imports', 'Full Imports', 'Empty Imports'):
        logger.warning('%d LA container table - total imports do not match sum of full and empty imports', year)
    if not check('Total Exports', 'Full Exports', 'Empty Exports'):
        logger.warning('%d LA container table - total exports do not match sum of full and empty exports', year)
    if not check('Total TEUs', 'Total Imports', 'Total Exports'):
        logger.warning('%d LA container table - total TEUs do not match sum of imports and exports', year)


def _fix_la_1995(la_df: pd.DataFrame):
    la_df.rename(columns={'Total TEUs': 'Total Exports'}, inplace=True)
    la_df['Total TEUs'] = la_df['Total Exports'] + la_df['Total Imports']


###################
# PORT OF OAKLAND #
###################

def get_oakland_container_data(url: str = 'https://www.oaklandseaport.com/performance/facts-figures/') -> pd.DataFrame:
    """Download the full record of Oakland container data

    Parameters
    ----------
    url
        The URL to retrieve from. Usually does not need to change.

    Returns
    -------
    pandas.DataFrame
        A dataframe containing the historical data (extracted from their Excel sheet) and this years data (extracted
        directly from the web page).

    Notes
    -----
    This will actually fetch the data from the Port of Oakland webpage. It is best to fetch this data once and reuse
    the returned dataframe, rather than requesting it repeatedly.
    """
    r = requests.get(url)
    if r.status_code != 200:
        raise HTMLRequestError('Failed to retrieve Oakland container web page (URL = {})'.format(url))
    soup = BeautifulSoup(r.content, features='html.parser')

    # First try to find the link to the Excel sheet and download it
    xlsx_url = None
    for el in soup('a'):
        if 'href' in el.attrs and 'xlsx' in el.attrs['href']:
            if xlsx_url is None:
                xlsx_url = el.attrs['href']
            else:
                raise HTMLParsingError('Multiple links to Excel files found on Oakland container page')

    if xlsx_url is None:
        raise HTMLParsingError('No links to Excel files found on Oakland container page')

    # The link in the page usually doesn't include the HTTP/HTTPS, so prepend it if needed
    if not xlsx_url.startswith('http'):
        schema = url.split('//')[0]
        xlsx_url = '{}{}'.format(schema, xlsx_url)
    r_wb = requests.get(xlsx_url)
    if r_wb.status_code != 200:
        raise HTMLRequestError('Failed to retrieve Oakland container xlsx file (URL = {})'.format(xlsx_url))

    # Parse the Excel file contents first, then append the most recent data from the web page
    df = parse_oakland_excel(r_wb.content, is_contents=True)
    df_recent = _parse_oakland_page(r.content)

    df = pd.concat([df, df_recent], axis=0)
    df['Total Imports'] = df['Full Imports'] + df['Empty Imports']
    df['Total Exports'] = df['Full Exports'] + df['Empty Exports']
    df['Total TEUs'] = df['Total Exports'] + df['Total Imports']
    return df


def _parse_oakland_page(content: bytes):
    """Parse the Oakland facts & figures page to extract a dataframe of container moves"""
    soup = BeautifulSoup(content, features='html.parser')

    # Try to find the year in the page headings. Usually the first <h2> element
    # is something like: <h2 style="text-align: center;">2020 Container Activity (TEUs)</h2>
    year = None
    for heading in soup.find_all('h2'):
        m = re.search(r'\d{4}', heading.text)
        if m:
            year = int(m.group())
            break
    if year is None:
        raise HTMLParsingError('Could not identify year in Oakland port data page')

    charts = soup.find_all('div', attrs={'class': 'chart-wrapper'})
    chart_data = dict()

    # The last chart is a summary of past years' total TEUs so we skip it
    for c in charts[:-1]:
        category, months, teus = _parse_one_oakland_chart(c)
        dtind = pd.DatetimeIndex([pd.Timestamp(year, m, 1) for m in months])
        chart_data[category] = pd.Series(teus, index=dtind)

    # Compute the total for convenience and make sure the totals are in order
    return pd.DataFrame(chart_data)
    # col_order = df.columns.tolist()
    # df['Total Imports'] = df['Full Imports'] + df['Empty Imports']
    # df['Total Exports'] = df['Full Exports'] + df['Empty Exports']
    # df['Total TEUs'] = df['Total Imports'] + df['Total Exports']
    # col_order.append('Total Imports')
    # col_order.append('Total Exports')
    # col_order.append('Total TEUs')
    # return df[col_order]


def _parse_one_oakland_chart(chart: bs4_element):
    """Parse one of the charts on the Oakland page"""
    title_el = chart.find('div', attrs={'class': 'chart-vertical-title'})
    title = title_el.text

    data_els = [el for el in chart.find_all('li') if 'title' in el.attrs]
    months = []
    teus = []
    for el in data_els:
        month = pd.to_datetime(el.attrs['title'], format='%b').month
        num_el = el.find('span', attrs={'class': 'number'})
        num = np.nan if len(num_el.text) == 0 else np.float(num_el.text.replace(',', ''))
        months.append(month)
        teus.append(num)

    return title, months, teus
