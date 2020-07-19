import os
import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import base64
from PIL import Image
import io
import time
import pandas as pd
import numpy as np
import re
import datetime
import subprocess
from tqdm import tqdm
import gpxpy
from dateutil.parser import *
import pytz
import piexif
import pyexiv2
from GPSPhoto import gpsphoto

def gp_extract(filename, gp_timezone = 'US/Eastern'):
    """Returns a dataframe containing the name of each frame in the gopro video and its respective timestamp"""
    frames = []
    path = 'frames/'
    video = cv2.VideoCapture(filename)
    total = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    print('Writing '+str(total)+' frames from ' + filename + ' to '+ path+ '...')
    start=datetime.datetime.now()
    cap = cv2.VideoCapture(filename)
    i=0
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            break
        frames.append(str(i)+'.jpg')
        cv2.imwrite(path +str(i)+'.jpg',frame)
        #print('\b'*((1+len(str(i))+len(str(total)))*i)+ str(i)+'/'+ str(total))
        i+=1
    cap.release()
    cv2.destroyAllWindows()
    delta = datetime.datetime.now()- start
    print('Done in '+str(delta))
    
    #add timestamps to each frame
    subprocess.call([r'C:\Users\beck\Documents\CSCR\gpmf-extract\forallTimeExtraction.bat'])
    time.sleep(3)
    filename.replace('mp4','MP4')
    gp_telem = pd.read_csv(filename+'.csv')
    i = 0
    for date in gp_telem['date']:
        gp_telem.loc[i,'date'] = datetime.datetime.strptime(gp_telem['date'][i][:-1],'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=pytz.timezone(gp_timezone)) 
        i+=1
    gopro_df = pd.DataFrame()
    gopro_df['frame'] = frames[:len(gp_telem['date'])]
    gopro_df['timestamp'] = gp_telem['date']
    return gopro_df
#gp_extract = gp_extract('GH010001.MP4')

def track_extract(gpx_filename, gp_timezone = 'US/Eastern'):
    """Returns a dataframe containing the telemetry collected from the gpx file"""
    print('Parsing '+ gpx_filename + '...')
    begin_time = datetime.datetime.now()
    points = list()
    with open('tracks/'+ gpx_filename,'r') as gpxfile:
        gpx = gpxpy.parse(gpxfile)
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    dict = {'timestamp': point.time,
                            'latitude': point.latitude,
                            'longitude': point.longitude,
                            'elevation': point.elevation
                                }
                    points.append(dict)
    gps_telem = pd.DataFrame.from_dict(points)
    i = 0
    for timestamp in gps_telem['timestamp']:
        gps_telem.loc[i,'timestamp'] = gps_telem.loc[i,'timestamp'].to_pydatetime().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(gp_timezone))
        i+=1
    print('Done in '+ str(datetime.datetime.now() - begin_time))
    return gps_telem
#track_extract(gpx_filename = 'track-71520-23237pm.gpx')

def concatenate(gopro_filename, gpx_filename, gp_timezone = 'US/Eastern'):
    track_ex = track_extract(gpx_filename, gp_timezone)
    gp_ex = gp_extract(gopro_filename)
    concatenate_df = track_ex
    i = 0
    for gpstime in track_ex['timestamp']:
        timedeltas = []
        for gptime in gp_ex['timestamp']:
            delta = gpstime-gptime
            timedeltas.append(delta.total_seconds())
        ix = gp_ex.loc[timedeltas.index(min(timedeltas)), 'frame']
        concatenate_df.loc[i, 'frame'] = ix
        i += 1
    return concatenate_df

def geotag(df):
    print('Geotagging '+ str(len(concatenate_df['frame'])) + ' frames to path:/geotagged/')
    start=datetime.datetime.now()
    i = 0
    for frame in concatenate_df['frame']:
        photo = gpsphoto.GPSPhoto('frames/'+frame)
        info = gpsphoto.GPSInfo((concatenate_df.loc[i, 'latitude'], 
                                 concatenate_df.loc[i, 'longitude']), 
                                alt=int(concatenate_df.loc[i, 'elevation']), 
                                timeStamp=concatenate_df.loc[i, 'timestamp'])
        photo.modGPSData(info, 'geotagged/'+ frame)
        i+=1
    delta = datetime.datetime.now()- start
    print('Done in '+str(delta))
