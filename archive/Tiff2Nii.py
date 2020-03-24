# -*- coding: utf-8 -*-imp
"""
Created on Mon Aug 28 10:08:30 2017

@author: Raluca Sandu
"""

from skimage import io
import nibabel as nib
import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt
#%%
source_tif = "SL_41868_0003_tumor_source_0.tif" # 'LW_0009935045_0000010.tif'
source_dcm = "SL_41868_0000_source.dcm"
outfile1 = "SL_41868_0003_tumor_source_0.nii" #'test.nii'
outfile2 = "SL_41868_0003001_tumor_mask.nii"

source_mask = "SL_41868_0003001_tumor_mask.tif"

img = io.imread(source_tif)
mask = io.imread(source_mask)
print('read file')
imgfile = nib.Nifti1Image(img, np.eye(4))
maskfile = nib.Nifti1Image(mask, np.eye(4))
print('saving file')
imgfile.to_filename(outfile1)
maskfile.to_filename(outfile2)
print('finished')

#source_metadata = sitk.ReadImage(source_dcm,  sitk.sitkUInt8)
#%%
"'"'plot the slices""'
plt.figure(1)
plt.imshow(img[200,:,:], cmap='gray')
plt.figure(2)
plt.imshow(mask[160,:,:])