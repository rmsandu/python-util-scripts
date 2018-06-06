# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 14:09:10 2018

"""


import SimpleITK as sitk
import sys, os

if len ( sys.argv ) < 2:
    print( "Usage: DicomSeriesReader <input_directory> <output_file>" )
    sys.exit ( 1 )


print( "Reading Dicom directory:", sys.argv[1] )
reader = sitk.ImageSeriesReader()

dicom_names = reader.GetGDCMSeriesFileNames( sys.argv[1] )
reader.SetFileNames(dicom_names)

image = reader.Execute()

size = image.GetSize()
print( "Image size:", size[0], size[1], size[2] )


if ( not "SITK_NOSHOW" in os.environ ):
    sitk.Show( image, "Dicom Series", debugOn=True )