# CAADA - COVID Atmospheric Ancillary Data Agglomerator

[![DOI](https://zenodo.org/badge/277681678.svg)](https://zenodo.org/badge/latestdoi/277681678)

## Documentation

Full documentation is available at https://joshua-laughner.github.io/CAADA/.

## Terms of use

Only the `master` branch is intended for public use. All other branches represent
work in progress and should not be relied on. 

If you use CAADA in a publication, you must cite it using the DOI listed above. 
A suggested citation is (replacing *vX* with the proper version tag):

J.L. Laughner. *COVID Atmospheric Ancillary Data Agglomerator, vX*. DOI: 10.5281/zenodo.3386652

## Quickstart (Expert)

1. Download and install [JLLUtils](https://github.com/joshua-laughner/JLL-Py-Utils)
2. Download and install CAADA
3. This package is structured as: `caada.<data type>.<module>`, e.g. 
   `caada.ca_pems.readers` is the module for reading Caltrans PEMS data.
   

## Installing in a Conda environment (recommended)

Any `command text` is to be executed in the terminal. 

1. Install [Anaconda Python](https://www.anaconda.com/products/individual) or 
   [Miniconda](https://docs.conda.io/en/latest/miniconda.html) if not already done.
1. Create a directory where you want the CAADA code to be and `cd` to there
1. Clone [CAADA](https://github.com/joshua-laughner/CAADA):
   `git clone https://github.com/joshua-laughner/CAADA.git`
1. Create an environment from the provided "environment.yml" file:
   ```
   cd CAADA
   conda env create -f environment.yml
   ```
1. Activate the environment: `conda activate caada`
1. Install CAADA in this environment, then go back up to your main directory:
   ```
   python setup.py install
   cd ..
   ```
1. Clone the [JLLUtils](https://github.com/joshua-laughner/JLL-Py-Utils) dependency:
   `git clone https://github.com/joshua-laughner/JLL-Py-Utils.git`
1. Install JLLUtils into this environment:
   ```
   cd JLL-Py-Utils
   python setup.py install
   cd ..    
   ```
1. If you wish to use this with a Jupyter notebook, you will need to [install a
   kernel](https://stackoverflow.com/questions/37433363/link-conda-environment-with-jupyter-notebook/53546675#53546675)
   for this Conda environment. With the "caada" environment still active:
   ```
   ipython kernel install --user --name=caada
   ```
   The next time you start Jupyter, "caada" should be available as a kernel option.
   
   
## Installing without a Conda environment (not recommended)

1. Create a directory where you want the CAADA code to be and `cd` to there
1. Clone [CAADA](https://github.com/joshua-laughner/CAADA):
   `git clone https://github.com/joshua-laughner/CAADA.git`
1. Install CAADA, then go back up to your main directory:
   ```
   cd CAADA
   python setup.py install --user
   cd ..
   ``` 
1. Clone the [JLLUtils](https://github.com/joshua-laughner/JLL-Py-Utils) dependency:
   `git clone https://github.com/joshua-laughner/JLL-Py-Utils.git`
1. Install JLLUtils:
   ```
   cd JLL-Py-Utils
   python setup.py install --user
   cd ..    
   ```

## Using CAADA

During the installation, a command line interface program named `caada-main` is
created. If you install into a Conda environment (and do not have a `~/.pydistutils.cfg`
file that alters install paths), that environment *must* be active for `caada-main` to
be on your `PATH` (i.e. findable from the terminal). The various agglomerators are
available as subcommands to this main program. You can see them with the `-h` or
`--help` flags: 

```
$ caada-main --help
usage: __main__.py [-h] {ca-pems} ...

Agglomerate various datasets into netCDF files

positional arguments:
  {ca-pems}
    ca-pems   Agglomerate Caltrans PEMS station data

optional arguments:
  -h, --help  show this help message and exit
```

To see the options for a specific subcommand, pass `-h` or `--help` after that
subcommand:

```
$ caada-main ca-pems --help
usage: __main__.py ca-pems [-h] [-s {county}] pems_root meta_root save_path

Agglomerate Caltrans PEMS station files into a single netCDF file

positional arguments:
  pems_root             The path to the root directory containing the PEMS data. This must be a directory with subdirectories organizing the data by district named "d03", "d04", ..., "d12". DO NOT mix different
                        time resolutions.
  meta_root             The path to the root directory containing the PEMS metadata. This must have the same organization as PEMS_ROOT.
  save_path             The path to save the netCDF file as (including filename).

optional arguments:
  -h, --help            show this help message and exit
  -s {county}, --spatial-resolution {county}
                        What spatial resolution to agglomerate the data to.
```