from datetime import datetime
from pandas import Timestamp
from pathlib import Path
from typing import Sequence, Union

datetimelike = Union[datetime, Timestamp]
pathlike = Union[str, Path]
stringlike = Union[str, bytes]
scalarnum = Union[int, float]
intseq = Sequence[int]
floatseq = Sequence[float]
numseq = Sequence[scalarnum]
pathseq = Sequence[pathlike]
strseq = Sequence[str]
