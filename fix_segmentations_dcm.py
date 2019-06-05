# -*- coding: utf-8 -*-
"""
Created on Tue Feb 07 11:34:48 2019

@author: Raluca Sandu
"""

import os
import sys
import pydicom
import pandas as pd
from pydicom import uid
from pydicom.sequence import Sequence
from pydicom.dataset import Dataset
import readInputKeyboard
from anonym_xml_logs import encode_xml
from extract_segm_paths_xml import create_tumour_ablation_mapping


def add_general_reference_segmentation(dcm_segm, ReferencedSOPInstanceUID_segm,
                                       ReferencedSOPClassUID_src,
                                       ReferencedSOPInstanceUID_src,
                                       segment_label):
    """
    Add Reference to the tumour/ablation and source img in the DICOM segmentation metatags. 
    :param dcm_segm: 
    :param ReferencedSOPClassUID_segm: 
    :param ReferencedSOPInstanceUID_segm: 
    :param ReferencedSOPClassUID_src: 
    :param ReferencedSOPInstanceUID_src: 
    :return: 
    """

    if "Lession" or "Lesion" or "Tumor" in segment_label:
        dataset_segm.SegmentLabel = "Tumor"
    elif "Ablation" in dataset_segm_series_uid:
        dataset_segm.SegmentLabel = "Ablation"

    dataset_segm.SegmentationType = "BINARY"
    dataset_segm.SegmentAlgorithmType = "SEMIAUTOMATIC"
    dataset_segm.DerivationDescription = "Segmentation mask done with CAS-ONE IR segmentation algorithm"
    dataset_segm.ImageType = "DERIVED\PRIMARY"
    # dataset_segm.SOPClassUID = "1.2.840.10008.5.1.4.1.1.66.4"  # the sop class for segmentation

    Segm_ds = Dataset()
    Segm_ds.ReferencedSOPInstanceUID = ReferencedSOPInstanceUID_segm
    Segm_ds.ReferencedSOPClassUID = dataset_segm.SOPClassUID

    Source_ds = Dataset()
    Source_ds.ReferencedSOPInstanceUID = ReferencedSOPInstanceUID_src
    Source_ds.ReferencedSOPClassUID = ReferencedSOPClassUID_src

    dataset_segm.ReferencedImageSequence = Sequence([Segm_ds])
    dataset_segm.SourceImageSequence = Sequence([Source_ds])

    return dcm_segm

# %%


if __name__ == '__main__':

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
                pass  # DF already exists

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
                dataset_segm.SliceLocation = dataset_segm.ImagePositionPatient[2]
                dataset_segm.SOPInstanceUID = uid.generate_uid()
                dataset_segm.InstanceNumber = k
                k += 1  # increase the instance number

                dataset_segm_series_no = dataset_segm.SeriesNumber
                dataset_segm_series_uid = dataset_segm.SeriesInstanceUID

                df_ct_mapping = pd.DataFrame(list_all_ct_series)
                idx_series_source = df_ct_mapping.index[df_ct_mapping['SeriesNumber'] == dataset_segm_series_no]

                idx_segm_xml = df_segmentations_paths_xml.index[
                    df_segmentations_paths_xml["SeriesUID_xml"] == dataset_segm_series_uid].tolist()[0]

                # get the needle value at the index of the identified segmentation series_uid
                needle_val = df_segmentations_paths_xml.NeedleIdx[idx_segm_xml]
                # find all the needles df_indexes with the value identified previously
                idx_needle_all = df_segmentations_paths_xml.index[
                    df_segmentations_paths_xml["NeedleIdx"] == needle_val].tolist()
                idx_referenced_segm = [el for el in idx_needle_all if el != idx_segm_xml]

                if len(idx_referenced_segm) > 1:
                    print('The SeriesInstanceUID for the segmentations is not unique')
                    sys.exit()

                ReferencedSOPInstanceUID_src = df_ct_mapping.loc[idx_series_source].SeriesInstanceNumberUID.tolist()[0]
                ReferencedSOPClassUID_src = df_ct_mapping.loc[idx_series_source].SOPClassUID.tolist()[0]
                ReferencedSOPInstanceUID_segm = \
                    df_segmentations_paths_xml.loc[idx_referenced_segm].SeriesUID_xml.tolist()[0]
                segment_label = df_segmentations_paths_xml.loc[idx_segm_xml].SegmentLabel
                #
                dataset_segm = add_general_reference_segmentation(dataset_segm, ReferencedSOPInstanceUID_segm,
                                                   ReferencedSOPClassUID_src,
                                                   ReferencedSOPInstanceUID_src,
                                                   segment_label)

                print(dataset_segm)

                dataset_segm.save_as(dcm_file)

print("Patient Folder Segmentations Fixed:", patient_name)
