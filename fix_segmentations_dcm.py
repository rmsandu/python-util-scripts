# -*- coding: utf-8 -*-
"""
Created on Tue Feb 07 11:34:48 2019

@author: Raluca Sandu
"""
import os
import pydicom
import pandas as pd
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
    # for subdir, dirs, files in os.walk(rootdir):
    #     for file in sorted(files):  # sort files by date of creation
    #         fileName, fileExtension = os.path.splitext(file)
    #         if fileExtension.lower().endswith('.xml'):
    #             xmlFilePathName = os.path.join(subdir, file)
    #             xmlfilename = os.path.normpath(xmlFilePathName)
    #             encode_xml(xmlfilename, patient_id, patient_name, patient_dob)

    #%% DICOM encoding
    list_all_ct_series = []
    for subdir, dirs, files in os.walk(rootdir):
        # study_0, study_1 case?
        path, foldername = os.path.split(subdir)
        if 'Series_' in foldername:
            # get the source image sequence attribute - SOPClassUID
            for file in sorted(files):
                try:
                    dcm_file = os.path.join(subdir, file)
                    dataset_source_ct = pydicom.read_file(dcm_file)
                except Exception:
                    # not dicom file so continue until you find one
                    continue
                source_series_instance_uid = dataset_source_ct.SeriesInstanceUID
                source_series_number = dataset_source_ct.SeriesNumber
                source_SOP_class_uid = dataset_source_ct.SOPClassUID
                dict_series_folder = {"SeriesNumber":  source_series_number,
                                      "SeriesInstanceNumber": source_series_instance_uid,
                                      "SOPClassUID": source_SOP_class_uid
                                      }
                list_all_ct_series.append(dict_series_folder)
                break  # exit loop, we only need the first file

    for subdir, dirs, files in os.walk(rootdir):
        k = 1
        if 'SeriesNo_' and 'Segmentations' in subdir:
            for file in sorted(files):  # sort files by date of creation
                DcmFilePathName = os.path.join(subdir, file)
                try:
                    dcm_file = os.path.normpath(DcmFilePathName)
                    dataset_segm = pydicom.read_file(dcm_file)
                    dataset_segm.PatientName = patient_name
                    dataset_segm.PatientID = patient_id
                    dataset_segm.PatientBirthDate = patient_dob
                    dataset_segm.InstitutionName = "None"
                    dataset_segm.InstitutionAddress = "None"
                    dataset_segm.SliceLocation = dataset_segm.ImagePositionPatient[2]
                    dataset_segm.SOPInstanceUID = uid.generate_uid()
                    dataset_segm.InstanceNumber = k
                    k += 1  # increase the instance number
                    dataset_segm.ImageType = "DERIVED\SECONDARY\AXIAL"
                    dataset_segm.SOPClassUID = "1.2.840.10008.5.1.4.1.1.66.4"

                    dataset_segm_series_no = dataset_segm.SeriesNumber
                    print('series number segmentation:', str(dataset_segm_series_no))
                    df_ct_mapping = pd.DataFrame(list_all_ct_series)
                    idx = df_ct_mapping.index[df_ct_mapping['SeriesNumber'] == dataset_segm_series_no]


                    # todo: assign correctly the series instance from plan series to tumour segm
                    # todo: find the source series instance uid based on the source series number
                    dataset_segm.ReferencedSOPClassUID = df_ct_mapping.loc[idx].SOPClassUID  # Uniquely identifies the referenced SOP Class
                    dataset_segm.ReferenceSOPInstanceUID = source_series_instance_uid  # Uniquely identifies the referenced SOP Instance
                    dataset_segm.DerivationDescription = source_series_number
                    dataset_segm.SegmentLabel = "Tumour"  # User-defined label identifying this segment.
                    # get the series number
                    dataset_segm.save_as(dcm_file)

                except Exception as e:
                    pass
                    print(repr(e))
                    print('File where it breaks: ', DcmFilePathName)

print("Patient Folder Segmentations Fixed:", patient_name)


