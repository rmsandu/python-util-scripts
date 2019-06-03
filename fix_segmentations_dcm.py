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
    # for subdir, dirs, files in os.walk(rootdir):
    #     for file in sorted(files):  # sort files by date of creation
    #         fileName, fileExtension = os.path.splitext(file)
    #         if fileExtension.lower().endswith('.xml'):
    #             xmlFilePathName = os.path.join(subdir, file)
    #             xmlfilename = os.path.normpath(xmlFilePathName)
    #             encode_xml(xmlfilename, patient_id, patient_name, patient_dob)

    #%% DICOM encoding

    # todo: assign correctly the series instance from validation series to ablation segm
    list_all_ct_series = []
    for subdir, dirs, files in os.walk(rootdir):
        # study_0, study_1 case?
        if 'Series_' in subdir:
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

        k = 1
        if 'SeriesNo_' and 'Segmentations' in subdir:
            for file in sorted(files):  # sort files by date of creation
                DcmFilePathName = os.path.join(subdir, file)
                try:
                    dcm_file = os.path.normpath(DcmFilePathName)
                    dataset = pydicom.read_file(dcm_file)
                    dataset.PatientName = patient_name
                    dataset.PatientID = patient_id
                    dataset.PatientBirthDate = patient_dob
                    dataset.InstitutionName = "None"
                    dataset.InstitutionAddress = "None"
                    dataset.SliceLocation = dataset.ImagePositionPatient[2]
                    dataset.SOPInstanceUID = uid.generate_uid()
                    dataset.InstanceNumber = k
                    k += 1
                    dataset.ImageType = "DERIVED\SECONDARY\AXIAL"
                    dataset.SOPClassUID = "1.2.840.10008.5.1.4.1.1.66.4"
                    # todo: assign correctly the series instance from plan series to tumour segm
                    # todo: find the source series instance uid based on the source series number
                    dataset.ReferencedSOPClassUID = source_SOP_class_uid  # Uniquely identifies the referenced SOP Class
                    dataset.ReferenceSOPInstanceUID = source_series_instance_uid  # Uniquely identifies the referenced SOP Instance
                    dataset.DerivationDescription = source_series_number
                    dataset.SegmentLabel = "Tumour"  # User-defined label identifying this segment.
                    # get the series number
                    dataset.save_as(dcm_file)

                except Exception as e:
                    pass
                    print(repr(e))
                    print('File where it breaks: ', DcmFilePathName)

print("Patient Folder Segmentations Fixed:", patient_name)


