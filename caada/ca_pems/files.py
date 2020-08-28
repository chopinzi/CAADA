import gzip
from pathlib import Path
import os
import re
import shutil

from typing import Sequence
from ..caada_logging import logger
from ..caada_typing import pathlike


def sort_pems_files(pems_root: pathlike, meta_root: pathlike, pems_files: Sequence[pathlike], delete_orig=False,
                    decompress=True, dry_run=False):
    pems_root = Path(pems_root)
    meta_root = Path(meta_root)

    for pemsf in pems_files:
        pemsf = Path(pemsf)
        district = re.search(r'^d\d\d', pemsf.name).group()
        if 'meta' in pemsf.name:
            destdir = meta_root / district
        else:
            destdir = pems_root / district

        if not destdir.is_dir():
            if dry_run:
                print('mkdir {}'.format(destdir))
            else:
                logger.info('Created directory: %s', destdir)
                destdir.mkdir()

        _copy_one_file(pemsf, destdir, delete_orig=delete_orig, decompress=decompress, dry_run=dry_run)


def _copy_one_file(srcfile: Path, destdir: Path, delete_orig=False, decompress=True, dry_run=False):
    if dry_run:
        print('cp {} -> {}'.format(srcfile, destdir))
    else:
        shutil.copy2(srcfile, destdir)
        logger.debug('Copied %s to %s', srcfile, destdir)
    if delete_orig:
        if dry_run:
            print('rm {}'.format(srcfile))
        else:
            os.remove(srcfile)
            logger.debug('Deleted %s', srcfile)
    destfile = destdir / srcfile.name
    if destfile.suffix == '.gz' and decompress:
        new_file = destfile.with_suffix('')
        if dry_run:
            print('gunzip {} -> {}'.format(destfile, new_file))
        else:
            with open(new_file, 'wb') as wobj, gzip.open(destfile, 'rb') as robj:
                wobj.write(robj.read())
            logger.debug('Decompressed %s', destfile)
        if delete_orig:
            if dry_run:
                print('rm {}'.format(destfile))
            else:
                os.remove(destfile)
                logger.debug('Deleted %s', destfile)
