# -*- coding: utf-8 -*-
"""
Created on Tue Feb 07 11:34:48 2019

@author: Raluca Sandu
"""
import os
import pydicom
from pydicom import uid
import readInputKeyboard
import xml.etree.ElementTree as ET
# from generate_sop_uid_dicom import make_uid
#%%


def encode_xml(filename, patient_id, patient_name, patient_dob):

    try:
        xmlobj = ET.parse(filename)
    except Exception as e:
        print(repr(e))
        print('This file cannot be parsed: ', filename)
        return None

    root = xmlobj.getroot()

    try:
        CT_info = root.findall('CTInfo')
        root.remove(CT_info)
        surgery_date = root.findall('SurgeryInfo')
        root.remove(surgery_date)
    except Exception as e:
        pass  # elements not found in XML
    try:
        # for patient information XML
        for pat in root.findall('PatientInfo'):
            pat.set('ID', patient_id)
            pat.set('Initial', patient_name)
            pat.set('DOB', patient_dob + '-01-01')
    except Exception as e:
        pass  # the xml elements not existent in this XML
    # Plan and Validation XML
    try:
        for pat in root.findall('PatientData'):
            pat.set('seriesPath', " ")
            try:
                pat.set('patientID', patient_id)
            except Exception as e:
                pass
    except Exception as e:
        pass  # elements not found in XML

    # re-write the XML and save it
    xmlobj.write(filename)

#%%


if __name__ == '__main__':
    # rootdir = os.path.normpath(readInputKeyboard.getNonEmptyString("Root Directory FilePath with Patient Folder"))
    # patient_name = readInputKeyboard.getNonEmptyString("New Patient Name, eg MAV-STO-M06")
    # patient_id = readInputKeyboard.getNonEmptyString("New Patient ID, eg. MAV-M06 ")
    # patient_dob = readInputKeyboard.getNonEmptyString("Patient's BirthDate, format eg. 19540101 ")
    rootdir = r"C:\MAVERRIC_STOCK_I\Pat_M6"
    patient_name = "MAV-STO-M06"
    patient_id = "MAV-M06"
    patient_dob = '19600101'
    #%% XML encoding
    for subdir, dirs, files in os.walk(rootdir):

        for file in sorted(files):  # sort files by date of creation
            fileName, fileExtension = os.path.splitext(file)

            if fileExtension.lower().endswith('.xml'):
                xmlFilePathName = os.path.join(subdir, file)
                xmlfilename = os.path.normpath(xmlFilePathName)
                encode_xml(xmlfilename, patient_id, patient_name, patient_dob)

    #%% DICOM encoding
    for subdir, dirs, files in os.walk(rootdir):
        if 'SeriesNo_' and 'Segmentations' in subdir:
            for file in sorted(files):  # sort files by date of creation
                DcmFilePathName = os.path.join(subdir, file)
                try:
                    k = 1
                    # modify only the segmentation files --> if the files are in the "Segmentations" files
                    # InstanceNumber, SliceLocation, SOPInstanceUID
                    dcm_file = os.path.normpath(DcmFilePathName)
                    dataset = pydicom.read_file(dcm_file)
                    dataset.PatientName = patient_name
                    dataset.PatientID = patient_id
                    dataset.PatientBirthDate = patient_dob
                    dataset.InstitutionName = "None"
                    dataset.InstitutionAddress = "None"
                    # dataset.SOPInstanceUID = make_uid()
                    dataset.SliceLocation = dataset.ImagePositionPatient[2]
                    dataset.SOPInstanceUID = uid.generate_uid()
                    dataset.InstanceNumber = k
                    k += 1
                    dataset.save_as(dcm_file)

                except Exception as e:
                    pass
                    print(repr(e))

print("Patient Folder Segmentations Fixed:", patient_name)


