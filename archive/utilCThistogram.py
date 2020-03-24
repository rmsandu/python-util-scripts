# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 11:08:02 2018

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

'''normaliza the image, segment the liver''' 
    
def normalize(image):
    MIN_BOUND = 0
    MAX_BOUND = 60.0
    image = (image - MIN_BOUND) / (MAX_BOUND - MIN_BOUND)
    image[image>1] = 1.
    image[image<0] = 0.
    return image

#%%
dirname =  'C:/CT_Scan_Needles_HistTest/Series_28'
files = os.listdir(dirname)
slices = [dicom.read_file(os.path.join(dirname, filename)) for filename in files]
slices.sort(key = lambda x: int(x.InstanceNumber))

imgs = get_pixels_hu(slices)

#%%
''' plot histogram '''
fig, ax = plt.subplots()
col_height1, bins1, patches = ax.hist(imgs.flatten(), bins=50,ec='darkgrey')
plt.xlabel('Hounsfield Units')
plt.ylabel('Frequency')
# it seems that the needle is at 3000