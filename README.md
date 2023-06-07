# FTP - Fault To Parameter

FTP is a Qgis model to calculate parameter for seismic hazard estimation starting from fault traces and seismicity. It applies empirical scale relationship by Donald L. Wells and Kevin J. Coppersmith (1994) to estimate magnitude, rupture length, rupture width, rupture area, and surface displacement. This *readme.md* file provides a comprehensive overview of the tool in its current release. Furthermore, quick commands and relevant information are also available within the model window.

## *Hardware and software specification*

FTP works on both Linux and Windows operative systems having Qgis software installed. It is originally created in Qgis 3.22.6, tested in Qgis 3.28.5 LTR. and modified in Qgis 3.30. FTP does not requires any additional toolboxes respect the default installation of the software. 

## *How it works*

FTP is composed of a *.model* and a *.py* files that are equivalent: the first one is the graphical model builded in Qgis and the other is the export in python language.

It starts from a shapefile of fault traces and another of earthquakes. After flipping the traces that are constructed from north to south, the model creates a buffer for each fault in the dipping direction. The buffer dimension depends on the length, the kinematics and the dip angle of each fault:

- for transcurrent faults the buffer dimension is 1/10 of trace length

- for normal faults the buffer dimension is half of the trace length

- for reverse faults the buffer dimension is equal to trace length

Through a spatial join, FTP correlates seismicity to the faults (events included in the buffer area). The depth distribution of each grup of earthquakes allow to estimate the seismogenic layer thickness as the depths included between 10% and 90% of seismicity. Finally it applies Weels and Coppersmith relationship using fault trace length and fault width calculated as the projection of seismogenic thickness on the fault plane.

## *Usage: input - output*

FTP requires a shapefile of fault traces and a shapefile of earthquakes:

- Fault traces - linear shapefile; it **must** have *dip angle*, *dip direction* and *kinematic* fileds (names can be different), moreover, lines that are not phisically joined **must not** be merged (have to be separated features).

- Earthquakes - shapefile of points used for seismogenic thickness estimation; it must have a *depth* field in kilometers (name can be different).

As a result it produce a shapefile of polygon corrisponding to the buffers. The attribute table contains original fault trace data and the following fields:

- *TO_FLIP* - values are *FLIP* or *NO_FLIP* indicating if the original trace has been flipped or not.

- *Length(km)* - length of fault trace.

- *BuffDim* - dimension of created buffer.

- *Depth min* - minimum depth of associated earthquakes.

- *Depth max* - maximum depth of associated earthquakes.

- *Seis_thick* - calculated thickness of seimogenic layer.

- *Width* - length of the fault along dip direction; it is calculated as the projection of seimogenic thickness on the fault plane (extrusion of the trace with available dip and dip direction).

- *Rupt_area* - estimated maximum rupture area in case of earthquake caused by the fault.

- *M (length)* - maximum magnitude in case of earthquake caused by the fault, estimated from trace length.

- *M (r_area)* - maximum magnitude in case of earthquake caused by the fault, estimated from rupture area.

- *M (width)* - maximum magnitude in case of earthquake caused by the fault, estimated from width.

- *max_dis(m)* - estimated maximum displacement in case of earthquake caused by the fault.

- *av_disp(m)* - estimated average displacement in case of earthquake caused by the fault.

By default the output is a Qgis temporary file but, the operator can decide to save it on a permanent shapefile.

## *Usage: tool*

For using FTP simply double-click on one of the two available files (*.model* or *.py*) by the *browser* panel of Qgis software. Like a classical tool, a pop-up window will appear; the user can find quick information about input and usage at the rigth side of the window.

## *Bugs and upgrades*

One known bug regard the traces that are merged without been joined (see *Usage: input - output* chapter). We are testing a tool to solve the bug that will be updated in the future.

Another future update will include other empirical relationship for parametrization of faults.
