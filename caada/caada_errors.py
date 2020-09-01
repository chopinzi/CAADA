class DimensionError(Exception):
    """Base error type for errors relating to data dimensions"""
    pass


class HTMLError(Exception):
    """Base error type for errors relating to HTML"""
    pass


class HTMLRequestError(HTMLError):
    """Error type indicating a problem fetching HTML data"""
    pass


class HTMLParsingError(HTMLError):
    """Base error type for errors parsing HTML"""
    pass
