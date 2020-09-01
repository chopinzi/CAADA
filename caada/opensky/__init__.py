from pathlib import Path

_cache_dir = Path(__file__).parent / 'cache'
if not _cache_dir.exists():
    _cache_dir.mkdir()

airport_code_sources = {'openflights': dict(local=_cache_dir / 'openflights_airport_codes.csv', remote='https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat')}
# Other possible sources:
#   http://www.airportcodes.org/
#   https://en.wikipedia.org/wiki/List_of_airports_by_IATA_airport_code:_A
# but will require more careful parsing


def get_airport_code_source(source: str) -> dict:
    """Get source for a particular web resource of airport codes

    Parameters
    ----------
    source
        Name used to refer to the source within CAADA. Only option currently recognized is `"openflights"`.

    Returns
    -------
    dict
        A dictionary keys `"local"` and `"remote"` that contain the local file name and remote URL, respectively.

    Raises
    ------
    ValueError
        If the value for `source` is not one of those allowed.

    Notes
    -----
        In the future, may return types other than a `dict` depending on the needs of specific sources.

    """
    if source in airport_code_sources.keys():
        return airport_code_sources[source]
    else:
        raise ValueError('Unknown airport code source: "{}"'.format(source))
