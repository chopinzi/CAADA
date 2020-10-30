"""
This module contains custom exceptions specific to Caltrans PEMS data.
"""


class SiteMetadataError(Exception):
    """Error type to use for problems with site metadata.
    """
    pass


class NoSiteMetadataError(SiteMetadataError):
    """Error type to use if no metadata can be found for a site
    """
    pass
