Command line tool
=================

`caada` includes a command line tool as an entry point to tasks like agglomerating and organizing files. This can be
helpful if you want to take advantage of these features, but do not use Python for your regular research. When you
install the `caada` package, it will also install the `caada-main` command line tool.

.. note:: If you install `caada` to a Python virtual environment or Conda environment, then you will most likely need
          to have that environment activated for `caada-main` to be discoverable on your path. If you want it to be
          always available, simply create a symbolic link to the `caada-main` script somewhere on your `PATH`. Also,
          if you have a :file:`.pydistutils.cfg` file in your home directory that sets a custom binary install directory,
          that will override where `caada-main` is installed. If so, that directory must be on your `PATH` for `caada-main`
          to be discoverable.

`caada-main` divides its functionality up into subcommands. To see a list of all subcommands, you can pass the `-h` or
`--help` flags to `caada-main`. Details on these subcommands are provided below, but the command line help text will
likely be more up-to-date.

.. note:: You will also see several additional flags like `-v` and `-q` listed by `caada-main -h`. Any of these flags
          *must* be given *before* the subcommand: e.g. `caada-main -v ca-pems` and not `caada-main ca-pems -v`.

Available subcommands
---------------------

* `ca-pems` allows you to create a netCDF file of Caltrans PEMS station data.
* `org-pems` will help organize Caltrans PEMS station data into the correct directory structure for `ca-pems`.
* `epa-cems-dl` will help download US EPA CEMS data.
* `os-covid` will create a summary netCDF file of `Strohmeier et al. <https://essd.copernicus.org/preprints/essd-2020-223/>`_
  OpenSky-derived .csv files of aircraft flights.