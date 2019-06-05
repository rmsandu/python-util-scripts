# -*- coding: utf-8 -*-
"""
Created on Tue Feb 07 11:34:48 2019

@author: Raluca Sandu
"""
import re
import os
import pydicom
import pandas as pd
from pydicom import uid
import readInputKeyboard
from anonym_xml_logs import encode_xml
from extract_segm_paths_xml import create_tumour_ablation_mapping

#%%

if __name__ == '__main__':
    # rootdir = os.path.normpath(readInputKeyboard.getNonEmptyString("Root Directory FilePath with Patient Folder"))
    # patient_name = readInputKeyboard.getNonEmptyString("New Patient Name, eg MAV-STO-M06")
    # patient_id = readInputKeyboard.getNonEmptyString("New Patient ID, eg. MAV-M06 ")
    # patient_dob = readInputKeyboard.getNonEmptyString("Patient's BirthDate, format eg. 19540101 ")
    rootdir = r"C:\tmp_patients\Pat_M6"
    patient_name = "MAV-STO-M06"
    patient_id = "MAV-M06"
    patient_dob = '19600101'
    # %% XML encoding
    for subdir, dirs, files in os.walk(rootdir):
        for file in sorted(files):  # sort files by date of creation
            fileName, fileExtension = os.path.splitext(file)
            if fileExtension.lower().endswith('.xml'):
                xmlFilePathName = os.path.join(subdir, file)
                xmlfilename = os.path.normpath(xmlFilePathName)
                encode_xml(xmlfilename, patient_id, patient_name, patient_dob)

    # %% DICOM encoding
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
                dict_series_folder = {"SeriesNumber": source_series_number,
                                      "SeriesInstanceNumberUID": source_series_instance_uid,
                                      "SOPClassUID": source_SOP_class_uid
                                      }
                list_all_ct_series.append(dict_series_folder)
                break  # exit loop, we only need the first file

    for subdir, dirs, files in os.walk(rootdir):
        k = 1

        if 'Segmentations' in subdir and 'SeriesNo_' in subdir:

            path_segmentations, foldername = os.path.split(subdir)
            path_recordings, foldername = os.path.split(path_segmentations)

            try:
                df_segmentations_paths_xml
            except NameError:
                print('DF XML Paths not defined yet')
                df_segmentations_paths_xml = create_tumour_ablation_mapping(path_recordings)
            else:
                print('DF already exists')

            for file in sorted(files):
                DcmFilePathName = os.path.join(subdir, file)
                try:
                    dcm_file = os.path.normpath(DcmFilePathName)
                    dataset_segm = pydicom.read_file(dcm_file)
                except Exception:
                    continue  # not a DICOM file
                # next lines will be executed only if the file is DICOM
                dataset_segm.PatientName = patient_name
                dataset_segm.PatientID = patient_id
                dataset_segm.PatientBirthDate = patient_dob
                dataset_segm.InstitutionName = "None"
                dataset_segm.InstitutionAddress = "None"
                dataset_segm.SliceLocation = dataset_segm.ImagePositionPatient[2]
                dataset_segm.SOPInstanceUID = uid.generate_uid()
                dataset_segm.InstanceNumber = k
                k += 1  # increase the instance number
                dataset_segm.ImageType = "DERIVED\PRIMARY\AXIAL"
                dataset_segm.SOPClassUID = "1.2.840.10008.5.1.4.1.1.66.4"  # the sop class for segmentation

                dataset_segm_series_no = dataset_segm.SeriesNumber
                dataset_segm_series_uid = dataset_segm.SeriesInstanceUID
                print('series number segmentation:', str(dataset_segm_series_no))
                df_ct_mapping = pd.DataFrame(list_all_ct_series)
                idx_series_source = df_ct_mapping.index[df_ct_mapping['SeriesNumber'] == dataset_segm_series_no]
                idx_series_xml = df_segmentations_paths_xml.index[
                    df_segmentations_paths_xml["SeriesUID_xml"] == dataset_segm_series_uid]

                dataset_segm.ReferencedSOPClassUID = df_ct_mapping.loc[idx_series_source].SOPClassUID.tolist()[0]
                # Uniquely identifies the referenced SOP Instance of the source CT from which it was derived
                dataset_segm.SourceImageSequence = \
                    df_ct_mapping.loc[idx_series_source].SeriesInstanceNumberUID.tolist()[0]

                dataset_segm.ReferencedSOPInstanceUID = df_segmentations_paths_xml.loc[idx_series_xml].SeriesUID_xml.tolist()[0]
                # User-defined label identifying this segment

                dataset_segm.SegmentLabel = "Tumour"
                dataset_segm.DerivationDescription = "Segmentation generated using CAS-ONE IR semi-automatic segmentation tool"
                dataset_segm.save_as(dcm_file)


print("Patient Folder Segmentations Fixed:", patient_name)
