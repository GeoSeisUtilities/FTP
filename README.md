# Wells_and_Coppersmith_estimation
Empirical relationship among magnitude, rupture length, rupture width, rupture area, and surface displacement

This is a QGIS model. It starts from a shapefile of fault traces and another of earthquakes, to apply the empirical scale relationship by Donald L. Wells and Kevin J. Coppersmith (1994). The model creates a buffer for each fault and uses it for a spatial selection of associated earthquakes. Then the model estimates the seismogenic layer using the earthquake distribution in depth (depths included between 10% and 90% of seismicity). Finally, it applies empirical relationship using fault trace length and fault width calculated as the projection of seismogenic thickness on the fault plane.

# Input parameters
Faults: shapefile of fault traces having "dip angle", "dip direction" and "kinematic" fields (names of fields can be different).

Eqs: shapefile of earthquakes that will be used for the seismogenic thickness estimation. It must have a "Depth" field in km.

# How to use
Download the model (.model3) or the Python script (.py). In the "browser" panel of QGIS software, find the model and double-click to open it. Like a classical tool, a pop-up window will appear and it contains the information to use the model.

# Alert
The model is created on QGIS 3.22.6 and tested also in QGIS 3.28.5 LTR.
