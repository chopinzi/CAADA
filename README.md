# CAADA - COVID Atmospheric Ancillary Data Agglomerator

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
