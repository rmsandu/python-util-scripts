# -*- coding: utf-8 -*-
"""
Created on June 06th 2019

@author: Raluca Sandu
"""

import os
import sys
import pydicom
import pandas as pd
from pydicom import uid
from pydicom.sequence import Sequence
from pydicom.dataset import Dataset
from anonymization_xml_logs import encode_xml
from extract_segm_paths_xml import create_tumour_ablation_mapping


def add_general_reference_segmentation(dcm_segm,
                                       ReferencedSOPInstanceUID_segm,
                                       ReferencedSOPInstanceUID_src,
                                       StudyInstanceUID_src,
                                       segment_label):
    """
    Add Reference to the tumour/ablation and source img in the DICOM segmentation metatags. 
    :param dcm_segm: dcm file read with pydicom library
    :param ReferencedSOPInstanceUID_segm: SeriesInstanceUID of the related segmentation file (tumour or ablation)
    :param ReferencedSOPInstanceUID_src: SeriesInstanceUID of the source image
    :param StudyInstanceUID_src: StudyInstanceUID of the source image
    :return: dicom single file/slice with new General Reference Sequence Tags
    """

    if segment_label == "Lession":
        dataset_segm.SegmentLabel = "Tumor"
    elif segment_label == "AblationZone":
        dataset_segm.SegmentLabel = "Ablation"

    dataset_segm.StudyInstanceUID = StudyInstanceUID_src
    dataset_segm.SegmentationType = "BINARY"
    dataset_segm.SegmentAlgorithmType = "SEMIAUTOMATIC"
    dataset_segm.DerivationDescription = "CasOneIR"
    dataset_segm.ImageType = "DERIVED\PRIMARY"

    Segm_ds = Dataset()
    Segm_ds.ReferencedSOPInstanceUID = ReferencedSOPInstanceUID_segm
    Segm_ds.ReferencedSOPClassUID = dataset_segm.SOPClassUID

    Source_ds = Dataset()
    Source_ds.ReferencedSOPInstanceUID = ReferencedSOPInstanceUID_src

    dataset_segm.ReferencedImageSequence = Sequence([Segm_ds])
    dataset_segm.SourceImageSequence = Sequence([Source_ds])

    return dcm_segm


# %%

if __name__ == '__main__':

    rootdir = r"C:\tmp_patients\Pat_MAV_BE_B01_"
    patient_name = "MAV-BER-B01"
    patient_id = "B01"
    patient_dob = '1942' \
                  '0101'
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
                source_study_instance_uid = dataset_source_ct.StudyInstanceUID
                source_series_number = dataset_source_ct.SeriesNumber
                source_SOP_class_uid = dataset_source_ct.SOPClassUID
                # if the ct series is not found in the dictionary, add it
                result = next((item for item in list_all_ct_series if
                               item["SeriesInstanceNumberUID"] == source_series_instance_uid), None)
                if result is None:
                    dict_series_folder = {"SeriesNumber": source_series_number,
                                          "SeriesInstanceNumberUID": source_series_instance_uid,
                                          "SOPClassUID": source_SOP_class_uid,
                                          "StudyInstanceUID": source_study_instance_uid
                                          }
                    list_all_ct_series.append(dict_series_folder)

    df_ct_mapping = pd.DataFrame(list_all_ct_series)
    # %% Create DF of CT Images and Segmentations SeriesInstanceUIDs based on the XML recordings
    list_segmentations_paths_xml = []
    for subdir, dirs, files in os.walk(rootdir):
        if 'Segmentations' in subdir and 'SeriesNo_' in subdir:
            path_segmentations, foldername = os.path.split(subdir)
            path_recordings, foldername = os.path.split(path_segmentations)

            dict_segmentations_paths_xml = \
                create_tumour_ablation_mapping(path_recordings, list_segmentations_paths_xml)
    df_segmentations_paths_xml = pd.DataFrame(list_segmentations_paths_xml)
    try:
        df_segmentations_paths_xml["TimeStartSegmentation"] = df_segmentations_paths_xml["Timestamp"].map(
            lambda x: x.split()[0])
    except KeyError:
        print('The TimeStamp Column in DataFrame is empty')

    # %% Edit each DICOM Segmentation File Individually by adding reference Source CT and the related segmentation
    for subdir, dirs, files in os.walk(rootdir):
        k = 1
        if 'Segmentations' in subdir and 'SeriesNo_' in subdir:
            for file in sorted(files):
                DcmFilePathName = os.path.join(subdir, file)
                try:
                    dcm_file = os.path.normpath(DcmFilePathName)
                    dataset_segm = pydicom.read_file(dcm_file)
                except Exception as e:
                    print(repr(e))
                    continue  # not a DICOM file
                # next lines will be executed only if the file is DICOM
                dataset_segm.PatientName = patient_name
                dataset_segm.PatientID = patient_id
                dataset_segm.PatientBirthDate = patient_dob
                dataset_segm.InstitutionName = "None"
                dataset_segm.InstitutionAddress = "None"
                # dataset_segm.SliceLocation = dataset_segm.ImagePositionPatient[2]
                dataset_segm.SOPInstanceUID = uid.generate_uid()
                dataset_segm.InstanceNumber = k
                k += 1  # increase the instance number

                dataset_segm_series_no = dataset_segm.SeriesNumber
                dataset_segm_series_uid = dataset_segm.SeriesInstanceUID



                try:
                    idx_segm_xml = df_segmentations_paths_xml.index[
                        df_segmentations_paths_xml["SegmentationSeriesUID_xml"] == dataset_segm_series_uid].tolist()[0]

                    # get the timestamp value at the index of the identified segmentation series_uid both the Plan.xml (
                    # tumour path) and Ablation_Validation.xml (ablation) have the same starting time in the XML
                    # find the other segmentation with the matching start time != from the seriesinstanceuid read atm
                    time_intervention = df_segmentations_paths_xml.TimeStartSegmentation[idx_segm_xml]
                    idx_segmentations_time = df_segmentations_paths_xml.index[
                        df_segmentations_paths_xml["TimeStartSegmentation"] == time_intervention].tolist()

                    idx_referenced_segm = [el for el in idx_segmentations_time if el != idx_segm_xml]

                    if len(idx_referenced_segm) > 1:
                        print('The SeriesInstanceUID for the segmentations is not unique at the following address: ',
                              DcmFilePathName)
                        sys.exit()

                    ReferencedSOPInstanceUID_src = \
                        df_segmentations_paths_xml.loc[idx_segm_xml].SourceSeriesID

                    # get the SeriesInstanceUID of the source CT from the XML files.
                    # 1) look for it in DF of the source CTs
                    # 2) get the corresponding StudyInstanceUID
                    idx_series_source_study_instance_uid = df_ct_mapping.index[
                        df_ct_mapping['SeriesInstanceNumberUID'] == ReferencedSOPInstanceUID_src].tolist()

                    if len(idx_series_source_study_instance_uid) > 1:
                        print('The StudyInstanceUID for the segmentations is not unique at the following address: ',
                              DcmFilePathName)
                        sys.exit()

                    StudyInstanceUID_src = df_ct_mapping.loc[idx_series_source_study_instance_uid[0]].StudyInstanceUID
                    print(StudyInstanceUID_src)

                    ReferencedSOPInstanceUID_segm = \
                        df_segmentations_paths_xml.loc[idx_referenced_segm[0]].SegmentationSeriesUID_xml

                    segment_label = df_segmentations_paths_xml.loc[idx_segm_xml].SegmentLabel

                    # call function to add reference to the source and other segmentations
                    dataset_segm = add_general_reference_segmentation(dataset_segm,
                                                                      ReferencedSOPInstanceUID_segm,
                                                                      ReferencedSOPInstanceUID_src,
                                                                      StudyInstanceUID_src,
                                                                      segment_label)
                except Exception as e:
                    print(repr(e) + "\n No Segmentation Found at this address: ", DcmFilePathName)

                dataset_segm.save_as(dcm_file) # save to disk

print("Patient Folder Segmentations Fixed:", patient_name)
