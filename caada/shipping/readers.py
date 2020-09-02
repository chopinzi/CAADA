import numpy as np
import pandas as pd
import xlrd

from typing import Union
from ..common_utils import secure_open_workbook
from ..caada_typing import stringlike, pathlike
from ..caada_errors import ExcelParsingError


def parse_oakland_excel(excel_file: Union[bytes, pathlike], is_contents=False) -> pd.DataFrame:
    """Parse an Excel sheet with container moves from the Port of Oakland

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
    sheet_dfs = [_parse_oakland_sheet(s, wb.datemode) for s in wb.sheets()]
    return pd.concat(sheet_dfs, axis=0)


def _verify_oakland_sheet(sheet: xlrd.sheet.Sheet):
    """Check that a sheet in the Oakland container workbook is laid out as expected.

    Raises `ExcelParsingError` if not.
    """
    reasons = []
    _cols = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
    # row index, column index, expected contents
    checks = [(4, 1, 'FULL'),
              (4, 4, 'EMPTY'),
              (4, 7, 'Grand'),
              (5, 1, 'Inbound'),
              (5, 2, 'Outbound'),
              (5, 3, 'Total'),
              (5, 4, 'Inbound'),
              (5, 5, 'Outbound'),
              (5, 6, 'Total'),
              (5, 7, 'Total')]
    for r, c, val in checks:
        if sheet.cell_value(r, c) != val:
            msg = '{}{} != {}'.format(_cols[c], r + 1, val)
            reasons.append(msg)

    if len(reasons) > 0:
        msg = 'Unexpected sheet format ({})'.format(', '.join(reasons))
        raise ExcelParsingError(msg)


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
    _verify_oakland_sheet(sheet)

    date_col = sheet.col(0)
    dates = []
    keys = ['Full Imports', 'Full Exports', 'Full Total', 'Empty Imports', 'Empty Exports', 'Empty Total',
            'Grand Total']
    data = {k: [] for k in keys}
    for irow, cell in enumerate(date_col[6:], start=6):
        if isinstance(cell.value, str) and len(cell.value) == 0:
            continue

        this_date = xlrd.xldate_as_datetime(cell.value, datemode)
        if this_date < pd.Timestamp(1990, 1, 1):
            # In the first sheets, there's only proper dates in the first column. However, in
            # the 17-18 sheet, they put the year in the date column for the total row. This gets
            # parsed as an early date, so we skip if the date is before 1990
            continue

        dates.append(this_date)
        for icol, k in enumerate(keys, start=1):
            val = sheet.cell_value(irow, icol)
            if isinstance(val, str) and len(val) == 0:
                data[k].append(np.nan)
            else:
                data[k].append(val)

    dates = pd.DatetimeIndex(dates)
    return pd.DataFrame(data, index=dates)
