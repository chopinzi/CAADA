CAADA Package Structure
=======================

The `caada` package is divided into subpackages, each of which handles a specific type of data. Some target a specific
type of data (e.g. :mod:`~caada.ca_pems`, :mod:`~caada.streetlight`); others handle a whole category of data
(:mod:`~caada.shipping`). Each package contains modules geared towards specific tasks. The module names are standardized
across the package:

    * `agglomeration` modules handle summing/averaging and merging data into netCDF files for more convenient access.
    * `exceptions` modules have custom exceptions used by the other modules in their package.
    * `readers` modules have functions to read data directly into Python
    * `web` modules have functions for retrieving data directly from the internet.

Some subpackages will have other modules that handle requirements specific to that data type. See the package API
documentation below for details.


.. toctree::
   :maxdepth: 2
   :caption: Package API documentation

   module_docs/ca_pems.rst
   module_docs/eia.rst
   module_docs/opensky.rst
   module_docs/shipping.rst
   module_docs/streetlight.rst