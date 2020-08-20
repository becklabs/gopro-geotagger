# gopro-gpx-zipper
- Developed in order to provide telemetry data for underwater gopro footage
- Reads in gopro mp4 and gpx file 
- Matches each gps point in the gpx file to a frame in the gopro video
- Adds latitude, longitude, altitude, and timestamp to each matched image's xxif data

# Usage
- create a dataframe using the concatenate function: df = concatenate(gopro_filename,track_filename)
- use geotag(df) to create a folder of geotagged images or classify(df) to classify each matched image within python

# Notes
- Have to set your own path for subprocess
# Credits
- @iackm for the gopro timestamp extraction executable
 - @KonradIT for gpmf-exract Javascript package
