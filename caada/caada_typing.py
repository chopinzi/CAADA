from datetime import datetime
from pandas import Timestamp
from pathlib import Path
from typing import Sequence, Union

datetimelike = Union[datetime, Timestamp]
pathlike = Union[str, Path]
scalarnum = Union[int, float]
intseq = Sequence[int]
floatseq = Sequence[float]
numseq = Sequence[scalarnum]
strseq = Sequence[str]
