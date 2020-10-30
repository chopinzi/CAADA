# CAADA Version History

## v0.1.0
First public release. Includes support for:

* Caltrans PeMS vehicle count data
* Energy Information Agency monthly electricity consumption data
* Opensky-derived flight data from [Strohmeier et al. 2020](https://doi.org/10.5194/essd-2020-223)
* Shipping (total container moves) from the Port of LA and Port of Oakland
* [Streetlight COVID VMT data](https://www.streetlightdata.com/)

Known issues:

* Agglomerating 5-minute PeMS data is hugely memory inefficient. Fix under development.