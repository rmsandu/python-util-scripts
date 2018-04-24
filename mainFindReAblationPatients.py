# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 11:56:30 2018

@author: Raluca Sandu
"""


import numpy as np
import dicom
import os
import matplotlib.pyplot as plt

#%%

def get_pixels_hu(scans):
    image = np.stack([s.pixel_array for s in scans])
    # Convert to int16 (from sometimes int16), 
    # should be possible as values should always be low enough (<32k)
    image = image.astype(np.int16)

    # Set outside-of-scan pixels to 1
    # The intercept is usually -1024, so air is approximately 0
    image[image == -2000] = 0
    
    # Convert to Hounsfield units (HU)
    intercept = scans[0].RescaleIntercept
    slope = scans[0].RescaleSlope
    
    if slope != 1:
        image = slope * image.astype(np.float64)
        image = image.astype(np.int16)
        
    image += np.int16(intercept)
    
    return np.array(image, dtype=np.int16)

def read_dicom_dir(dirname):
    files = os.listdir(dirname)
    slices = [dicom.read_file(os.path.join(dirname, filename)) for filename in files]
    slices.sort(key = lambda x: int(x.InstanceNumber))
    return slices

#%%

rootdir = "\\\\cochlea.artorg.unibe.ch\IGT\Projects\LIVER\_Clinical_Data\Interventions\Bern\\2017\\17-08-25 "

for dirpath, dirnames, filenames in os.walk(rootdir):
    rootpath, studyName = os.path.split(dirpath)
    if studyName == 'IR Data':
        for dirname in dirnames:
            dirStudy = os.path.join(dirpath, dirname)
            print('dirstudy', dirStudy)
            for series in os.listdir(dirStudy):
                seriesPath = os.path.join(dirStudy, series)
                slices = read_dicom_dir(seriesPath)
                break
#                print('series',series)

