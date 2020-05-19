from datetime import datetime
from pandas import Timestamp
from pathlib import Path
from typing import Sequence, Union

datetimelike = Union[datetime, Timestamp]
pathlike = Union[str, Path]
scalarnum = Union[int, float]
strseq = Sequence[str]
