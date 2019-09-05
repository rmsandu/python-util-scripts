# -*- coding: utf-8 -*-
"""
@author: Raluca Sandu

Idea:
Segment around the tumor a spherical object until the liver margin is reached.
Stop segmentation when contrast changes after a threshold
Seeding point: center of tumor mask.
Expand 10mm in the all directions. if no change in contrast detected stop segmentation
otherwise save liver mask.
Case: what if the tumor centre is already at the border???. that it's not possible
1. identify an example of a subcapsular lesion
2. take the ct scan
"""

import argparse
import pandas as pd
import numpy as np
import SimpleITK as sitk
import DicomReader
from myshow import myshow, myshow3d
import ResampleSegmentations

ap = argparse.ArgumentParser()
ap.add_argument("-m", "--filepath_segm_mask", required=True, help="filepath folder tumor segmentation mask")
ap.add_argument("-s", "--filepath_source_img", required=True, help="filepath folder ablation segmentation mask")
ap.add_argument("-o", "--output_filepath", required=True, help="filepath output folder")

args = vars(ap.parse_args())
mask = DicomReader.read_dcm_series(args["filepath_segm_mask"], False)
img = DicomReader.read_dcm_series(args["filepath_source_img"], False)

print('img size:', img.GetSize())
print('mask size:', mask.GetSize())
resizer = ResampleSegmentations.ResizeSegmentation(img, mask)
mask_resampled = resizer.resample_segmentation()
print('New Resampled Mask Size',  mask_resampled.GetSize())
# extract seeding point
# seeding point should be center of tumor
# apply smoothing
# extract the minimum value along the liver boundary
# extract the gradient in the object region
#%%Plot images
xslices, yslices, zslices = img.GetSize()
myshow(img,  title="Source CT")
# myshow(mask, title='original mask')
myshow(mask_resampled, title='resampled mask')
#%% print img vals

stats = sitk.LabelStatisticsImageFilter()
print(stats.GetLabels())
print(stats.HasLabel(label=0))

stats.Execute(img, mask_resampled)

factor = 3.5
lower_threshold = stats.GetMean(1)-factor*stats.GetSigma(1)
upper_threshold = stats.GetMean(1)+factor*stats.GetSigma(1)
print(lower_threshold, upper_threshold)

#%%

stoppingValue = 1000
seedPosition = [325, 180, 138] # center of the tumor
timeThreshold = 1000
# seedValue = 0

# fastMarching = sitk.FastMarchingImageFilter()
fastMarching = sitk.FastMarchingBaseImageFilter()
trialPoint = (seedPosition[0], seedPosition[1], seedPosition[2])
fastMarching.AddTrialPoint(trialPoint)
fastMarching.SetStoppingValue(stoppingValue)
fastMarchingOutput = fastMarching.Execute(img)


thresholder = sitk.BinaryThresholdImageFilter()
thresholder.SetLowerThreshold(0.0)
# thresholder.SetUpperThreshold(timeThreshold)
thresholder.SetOutsideValue(0)
thresholder.SetInsideValue(255)
result = thresholder.Execute(fastMarchingOutput)

#%%
myshow(sitk.Threshold(fastMarchingOutput,
                    lower=0.0,
                    upper=fastMarching.GetStoppingValue(),
                    outsideValue=fastMarching.GetStoppingValue()+1))
# write result to disk I imagine