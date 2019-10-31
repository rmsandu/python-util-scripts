# -*- coding: utf-8 -*-
"""
Created on June 2019

@author: Raluca Sandu
"""
import os

import pydicom

from anonymization_xml_logs import encode_xml

# %%

if __name__ == '__main__':

    rootdir = r""
    patient_name = "G01"
    patient_id = "G01"
    patient_dob = '19540101'
    # %% XML encoding
    for subdir, dirs, files in os.walk(rootdir):

        for file in sorted(files):  # sort files by date of creation
            fileName, fileExtension = os.path.splitext(file)

            if fileExtension.lower().endswith('.xml'):
                xmlFilePathName = os.path.join(subdir, file)
                xmlfilename = os.path.normpath(xmlFilePathName)
                encode_xml(xmlfilename, patient_id, patient_name, patient_dob)

    # %% DICOM encoding
    for subdir, dirs, files in os.walk(rootdir):
        for file in sorted(files):  # sort files by date of creation
            DcmFilePathName = os.path.join(subdir, file)
            try:
                dcm_file = os.path.normpath(DcmFilePathName)
                dataset = pydicom.read_file(dcm_file)
                dataset.PatientName = patient_name
                dataset.PatientID = patient_id
                # dataset.PatientBirthDate = patient_dob
                dataset.InstitutionName = "None"
                dataset.InstitutionAddress = "None"
                dataset.save_as(dcm_file)

            except Exception as e:
                pass
                print("Cannot parse this file as DICOM:", DcmFilePathName + " - " + repr(e))

print("Patient Folder Segmentations Encoded:", patient_name)
