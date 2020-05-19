import netCDF4 as ncdf
import os

from jllutils import vcs
from . import __version__


def add_caad_info(ds: ncdf.Dataset):
    ds.setncattr('caad_version', __version__)
    repo = vcs.Git(os.path.dirname(__file__))
    commit, branch, _ = repo.commit_info()
    is_clean = repo.is_repo_clean()
    clean_str = 'clean' if is_clean else 'uncommitted changes'
    ds.setncattr('caad_git_info', 'Commit {commit} on {branch} ({clean})'.format(commit=commit, branch=branch, clean=clean_str))
