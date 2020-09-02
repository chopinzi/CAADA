import netCDF4 as ncdf
import os
import defusedxml
from defusedxml.common import EntitiesForbidden
import xlrd

from jllutils import vcs
from . import __version__

defusedxml.defuse_stdlib()


def add_caada_info(ds: ncdf.Dataset):
    ds.setncattr('caada_version', __version__)
    repo = vcs.Git(os.path.dirname(__file__))
    commit, branch, _ = repo.commit_info()
    is_clean = repo.is_repo_clean()
    clean_str = 'clean' if is_clean else 'uncommitted changes'
    ds.setncattr('caada_git_info', 'Commit {commit} on {branch} ({clean})'.format(commit=commit, branch=branch, clean=clean_str))


# As recommended by https://xlrd.readthedocs.io/en/latest/vulnerabilities.html
def secure_open_workbook(*args, **kwargs) -> xlrd.Book:
    """Open an Excel workbook safely, protecting against embedded XML attacks.

    Parameters
    ----------
    args
        Positional arguments, passed through to :func:`xlrd.open_workbook`

    kwargs
        Keyword arguments, passed through to :func:`xlrd.open_workbook`

    Returns
    -------
    xlrd.Book
        Excel workbook.
    """
    try:
        return xlrd.open_workbook(*args, **kwargs)
    except EntitiesForbidden:
        raise ValueError('Please use a xlsx file without XEE')