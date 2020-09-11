.. COVID Atmospheric Ancillary Data Agglomerator (CAADA) documentation master file, created by
   sphinx-quickstart on Fri Sep  4 17:09:08 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CAADA's documentation!
=================================================================================

The `caada` package is designed to help read or reformat a variety of datasets useful to understanding how the
change in human activity during the COVID-19 pandemic has impacted the atmosphere, particularly in regards to
air quality and the carbon cycle.

There are two sides to this. First, there are the various subpackages which can be imported as part of a larger
Python project to help with reading this data. Second, installing this package will also install a command line
program, `caada-main`, which allows you to convert various datasets into a standardized netCDF format from the
command line.


.. toctree::
   :maxdepth: 1
   :caption: Introduction:

   package_structure.rst
   caada_cl.rst

.. toctree::
   :maxdepth: 2
   :caption: API documentation:

   module_docs/ca_pems.rst
   module_docs/eia.rst
   module_docs/epa.rst
   module_docs/opensky.rst
   module_docs/shipping.rst
   module_docs/streetlight.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
