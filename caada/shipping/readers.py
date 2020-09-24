import numpy as np
import pandas as pd
import re
import xlrd

from typing import Union
from ..common_utils import secure_open_workbook
from ..caada_typing import stringlike, pathlike
from ..caada_errors import ExcelParsingError


def parse_oakland_excel(excel_file: Union[bytes, pathlike], is_contents=False) -> pd.DataFrame:
    """Parse an Excel sheet with container moves from the Port of Oakland

    This parses the Excel file found on the `Port of Oakland page <https://www.oaklandseaport.com/performance/facts-figures/>`_
    (as of 2020-09-04). You can use this if you've downloaded that file manually, but it is automatically downloaded
    by :func:`~caada.shipping.web.get_oakland_container_data` and parsed with this function, so you usually do not
    need to do so.

    Parameters
    ----------
    excel_file
        The path to the Excel file; alternatively, the binary content of the file (must set `is_contents` to `True`).

    is_contents
        Whether the value of `excel_file` is a path to a file to open (`is_contents = False`, default), or the actual
        contents of the file (`True`).

    Returns
    -------
    pandas.DataFrame
        The monthly container moves as a Pandas Dataframe. Some rows may have NaNs if they were included in the Excel
        workbook but did not have any moves listed.
    """
    if is_contents:
        wb = secure_open_workbook(file_contents=excel_file)
    else:
        wb = secure_open_workbook(excel_file)
    if len(wb.sheets()) != 1:
        raise ExcelParsingError('Oakland Excel file does not consist of a single sheet - the format may have changed')
    else:
        return _parse_oakland_sheet(wb.sheets()[0], wb.datemode)


def _verify_oakland_sheet(sheet: xlrd.sheet.Sheet):
    """Check that a sheet in the Oakland container workbook is laid out as expected.

    Raises `ExcelParsingError` if not.
    """
    keys = dict()
    reasons = []
    _cols = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
    # row index, column index, expected contents, whether this column is a column name for the dataframe
    checks = [(2, 0, 'Year', False),
              (2, 1, 'Month', False),
              (2, 2, 'Import Full', True),
              (2, 3, 'Export Full', True),
              (2, 4, 'Total Full', True),
              (2, 5, 'Import Empty', True),
              (2, 6, 'Export Empty', True),
              (2, 7, 'Total Empty', True),
              (2, 8, 'Grand Total', True)]
    for r, c, val, is_key in checks:
        # Replace any whitespace with a single space (e.g. newlines)
        sheet_val = re.sub(r'\s+', ' ', sheet.cell_value(r, c))
        if sheet_val != val:
            msg = '{}{} != {}'.format(_cols[c], r + 1, val)
            reasons.append(msg)
        elif is_key:
            keys[sheet_val] = c

    if len(reasons) > 0:
        msg = 'Unexpected sheet format ({})'.format(', '.join(reasons))
        raise ExcelParsingError(msg)
    else:
        return keys


def _parse_oakland_sheet(sheet: xlrd.sheet.Sheet, datemode: int):
    """Parse a single sheet of the Oakland excel file into a dataframe.

    Parameters
    ----------
    sheet
        The Sheet object from the Book of the Oakland container moves.

    datemode
        The Book's datemode value (usually 0 or 1).

    Returns
    -------
    pandas.DataFrame
        The DataFrame containing all the sheets concatenated together.
    """
    # Assume the first 6 rows are just header, and verify that the columns are in order
    # date, full imports, full exports, total full, empty imports, empty expots, total empty
    # grand total
    keys = _verify_oakland_sheet(sheet)

    nrow = len(sheet.col(0))
    dates = []
    data = {k: [] for k in keys}
    for irow in range(3, nrow):
        year = sheet.cell_value(irow, 0)
        month = sheet.cell_value(irow, 1)
        if isinstance(month, str) and month == 'Annual Total':
            continue

        this_date = pd.to_datetime('{} {:.0f}'.format(month, year))
        if this_date < pd.Timestamp(1990, 1, 1) or this_date > pd.Timestamp.now():
            # This may catch some bad date parsing. I haven't had a problem with this, but want to check (in case they
            # change the format unexpectedly).
            raise ExcelParsingError('Unexpected date parsed (pre-1990)')

        dates.append(this_date)
        for k, icol in keys.items():
            val = sheet.cell_value(irow, icol)
            if isinstance(val, str) and len(val) == 0:
                data[k].append(np.nan)
            else:
                data[k].append(val)

    dates = pd.DatetimeIndex(dates)
    colname_mapping = {'Import Full': 'Full Imports', 'Export Full': 'Full Exports',
                       'Import Empty': 'Empty Imports', 'Export Empty': 'Empty Exports',
                       'Grand Total': 'Total TEUs'}
    return pd.DataFrame(data, index=dates).drop(columns=['Total Full', 'Total Empty']).rename(columns=colname_mapping)
