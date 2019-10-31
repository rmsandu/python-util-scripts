# -*- coding: utf-8 -*-
"""
Created on June 06th 2019

@author: Raluca Sandu
"""

import argparse
import os
import sys
from ast import literal_eval

import pandas as pd
import pydicom
from pydicom import uid
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence

import anonymization_xml_logs
from extract_segm_paths_xml import create_tumour_ablation_mapping


def anonymize_all_dcm_files(rootdir, patient_name, patient_id, patient_dob):
    """
    :param rootdir:
    :param patient_name:
    :param patient_id:
    :param patient_dob:
    :return:
    """
    for subdir, dirs, files in os.walk(rootdir):
        for file in sorted(files):  # sort files by date of creation
            DcmFilePathName = os.path.join(subdir, file)
            try:
                dcm_file = os.path.normpath(DcmFilePathName)
                dataset = pydicom.read_file(dcm_file)
            except Exception as e:
                # print(repr(e))
                continue  # not a DICOM file
            dataset.PatientName = patient_name
            dataset.PatientID = patient_id
            dataset.PatientBirthDate = patient_dob
            dataset.InstitutionName = "None"
            dataset.InstitutionAddress = "None"
            dataset.save_as(dcm_file)


def encode_segmentations_dcm_tags(rootdir, patient_name, patient_id, patient_dob):
    """

    :param rootdir:
    :param patient_name:
    :param patient_id:
    :param patient_dob:
    :return:
    """
    series_no = 50  # take absurd series number for the segmentations
    for subdir, dirs, files in os.walk(rootdir):
        if ('Segmentations' in subdir) and ('SeriesNo_' in subdir):
            k = 1
            series_no += 1
            SeriesInstanceUID_segmentation = uid.generate_uid()  # generate a new series instance uid for each folder
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
                dataset_segm.SeriesInstanceUID = SeriesInstanceUID_segmentation
                dataset_segm.InstanceNumber = k
                dataset_segm.SeriesNumber = series_no
                k += 1  # increase the instance number
                dataset_segm.save_as(dcm_file)  # save to disk


def add_general_reference_segmentation(dataset_segm,
                                       ReferencedSeriesInstanceUID_segm,
                                       ReferencedSOPInstanceUID_src,
                                       StudyInstanceUID_src,
                                       segment_label,
                                       lesion_number
                                       ):
    """
    Add Reference to the tumour/ablation and source img in the DICOM segmentation metatags. 
    :param dataset_segm: dcm file read with pydicom library
    :param ReferencedSOPInstanceUID_segm: SeriesInstanceUID of the related segmentation file (tumour or ablation)
    :param ReferencedSOPInstanceUID_src: SeriesInstanceUID of the source image
    :param StudyInstanceUID_src: StudyInstanceUID of the source image
    :param segment_label: text describing whether is tumor or ablation
    :param: lesion_number: a int identifying which lesion was this
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
    Segm_ds.ReferencedSOPInstanceUID = ReferencedSeriesInstanceUID_segm
    Segm_ds.ReferencedSOPClassUID = dataset_segm.SOPClassUID
    Segm_ds.ReferencedSegmentNumber = lesion_number

    Source_ds = Dataset()
    Source_ds.ReferencedSOPInstanceUID = ReferencedSOPInstanceUID_src

    dataset_segm.ReferencedImageSequence = Sequence([Segm_ds])
    dataset_segm.SourceImageSequence = Sequence([Source_ds])

    return dataset_segm


def create_dict_paths_series_dcm(rootdir):
    list_all_ct_series = []
    for subdir, dirs, files in os.walk(rootdir):
        # study_0, study_1 case?
        path, foldername = os.path.split(subdir)
        if ("Series" in foldername) or ("SegmentationNo" in foldername):
            # get the source image sequence attribute - SOPClassUID
            for file in sorted(files):
                try:
                    dcm_file = os.path.join(subdir, file)
                    dataset_source_ct = pydicom.read_file(dcm_file)
                except Exception:
                    # not dicom file so continue until you find one
                    continue
                source_series_instance_uid = dataset_source_ct.SeriesInstanceUID
                try:
                    source_study_instance_uid = dataset_source_ct.StudyInstanceUID
                except Exception:
                    source_study_instance_uid = None
                source_series_number = dataset_source_ct.SeriesNumber
                source_SOP_class_uid = dataset_source_ct.SOPClassUID
                # if the ct series is not found in the dictionary, add it
                result = next((item for item in list_all_ct_series if
                               item["SeriesInstanceNumberUID"] == source_series_instance_uid), None)
                path_segmentations_idx = subdir.find("Segmentations")
                if path_segmentations_idx != -1:
                    path_segmentations_folder = subdir[path_segmentations_idx - 1:]
                else:
                    path_segmentations_folder = subdir
                if result is None:
                    dict_series_folder = {"SeriesNumber": source_series_number,
                                          "SeriesInstanceNumberUID": source_series_instance_uid,
                                          "SOPClassUID": source_SOP_class_uid,
                                          "StudyInstanceUID": source_study_instance_uid,
                                          "PathSeries": path_segmentations_folder
                                          }
                    list_all_ct_series.append(dict_series_folder)
    return list_all_ct_series


def create_dict_paths_series_xml(rootdir):
    """

    :param rootdir:
    :return:
    """
    list_segmentations_paths_xml = []
    for subdir, dirs, files in os.walk(rootdir):
        if 'Segmentations' in subdir and 'SeriesNo_' in subdir:
            path_segmentations, foldername = os.path.split(subdir)
            path_recordings, foldername = os.path.split(path_segmentations)
            dict_segmentations_paths_xml = \
                create_tumour_ablation_mapping(path_recordings, list_segmentations_paths_xml)
    df_segmentations_paths_xml = pd.DataFrame(list_segmentations_paths_xml)
    # check if the dataframe is empty, exit the script if true
    if df_segmentations_paths_xml.empty:
        print("No Segmentations Paths found in the XML Cas-Recordings for Directory:", rootdir)
        return df_segmentations_paths_xml
    try:
        df_segmentations_paths_xml["TimeStartSegmentation"] = df_segmentations_paths_xml["Timestamp"].map(
            lambda x: x.split()[0])
    except KeyError:
        print('The TimeStamp Column in DataFrame is empty')
    return df_segmentations_paths_xml


def main_add_reference_tags_dcm(rootdir, df_ct_mapping, df_segmentations_paths_xml):
    """

    :param rootdir:
    :param df_segmentations_paths_xml:
    :param df_ct_mapping:
    :return:
    """
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
                path_segmentations_idx = subdir.find("Segmentations")
                path_segmentations_folder = subdir[path_segmentations_idx - 1:]
                try:
                    idx_segm_xml = df_segmentations_paths_xml.index[
                        df_segmentations_paths_xml["PathSeries"] == path_segmentations_folder].tolist()[0]
                except Exception as e:
                    continue
                    print(repr(e), "whats happening here")
                # get the timestamp value at the index of the identified segmentation series_uid both the Plan.xml (
                # tumour path) and Ablation_Validation.xml (ablation) have the same starting time in the XML
                # find the other segmentation with the matching start time != from the seriesinstanceuid read atm
                segm_instance_uid_val = df_segmentations_paths_xml.SegmentationSeriesUID_xml[idx_segm_xml]
                needle_idx_val = df_segmentations_paths_xml.NeedleIdx[idx_segm_xml]
                time_start_segm_val = df_segmentations_paths_xml.TimeStartSegmentation[idx_segm_xml]
                ReferencedSOPInstanceUID_src = \
                    df_segmentations_paths_xml.loc[idx_segm_xml].SourceSeriesID
                # get the SeriesInstanceUID of the source CT from the XML files.
                # 1) look for it in DF of the source CTs
                # 2) get the corresponding StudyInstanceUID
                try:
                    idx_series_source_study_instance_uid = df_ct_mapping.index[
                        df_ct_mapping['SeriesInstanceNumberUID'] == ReferencedSOPInstanceUID_src].tolist()

                    if not idx_series_source_study_instance_uid:
                        series_number = df_segmentations_paths_xml.loc[idx_segm_xml].SeriesNumber
                        idx_series_source_study_instance_uid = df_ct_mapping.index[
                            df_ct_mapping['SeriesNumber'] == int(series_number)].tolist()
                    if len(idx_series_source_study_instance_uid) > 1:
                        continue
                        # print('The StudyInstanceUID for the segmentations is not unique at the following address: ',
                        #       DcmFilePathName)
                        # sys.exit()
                    StudyInstanceUID_src = df_ct_mapping.loc[idx_series_source_study_instance_uid[0]].StudyInstanceUID

                except Exception as e:
                    continue
                    # print(repr(e))
                needle_idx_df_xml = df_segmentations_paths_xml.index[
                    df_segmentations_paths_xml["NeedleIdx"] == needle_idx_val].tolist()
                idx_referenced_segm = [el for el in needle_idx_df_xml if el != idx_segm_xml]
                if len(idx_referenced_segm) > 1:
                    # print('The SeriesInstanceUID for the segmentations is not unique at the following address: ',
                    #       DcmFilePathName)
                    # do the matching based on the time of the segmentations
                    time_start_idx_df_xml = df_segmentations_paths_xml.index[
                        df_segmentations_paths_xml["TimeStartSegmentation"] == time_start_segm_val].tolist()
                    idx_referenced_segm = [el for el in time_start_idx_df_xml if el != idx_segm_xml]

                # %% get the path series instead of the segmentationseriesuid_xml
                #  read the SeriesInstanceUID from the DICOM file (take the path)
                if idx_referenced_segm:
                    ReferencedSOPInstanceUID_path = \
                        df_segmentations_paths_xml.loc[idx_referenced_segm[0]].PathSeries
                elif len(idx_referenced_segm) > 1:
                    print('Multiple Segmentation Folders present.,'
                          'Please clean ')
                    sys.exit()
                else:
                    ReferencedSOPInstanceUID_path = None
                if ReferencedSOPInstanceUID_path is None:
                    segment_label = 0
                    lesion_number = 0
                    ReferencedSOPInstanceUID_ds = "None"
                    ReferencedSeriesInstanceUID_segm = "None"
                else:
                    referenced_dcm_dir = subdir[
                                         0:len(subdir) - len(path_segmentations_folder)] + ReferencedSOPInstanceUID_path
                    try:
                        segm_file = os.listdir(referenced_dcm_dir)[0]
                    except FileNotFoundError:
                        # print('No Files have been found at the specified address: ', referenced_dcm_dir)
                        continue  # go back to the beginning of the loop
                    ReferencedSOPInstanceUID_ds = pydicom.read_file(os.path.join(referenced_dcm_dir, segm_file))
                    ReferencedSeriesInstanceUID_segm = ReferencedSOPInstanceUID_ds.SeriesInstanceUID
                    segment_label = df_segmentations_paths_xml.loc[idx_segm_xml].SegmentLabel
                    lesion_number = df_segmentations_paths_xml.loc[idx_segm_xml].NeedleIdx + 1
                # call function to change the segmentation uid
                dataset_segm = add_general_reference_segmentation(dataset_segm,
                                                                  ReferencedSeriesInstanceUID_segm,
                                                                  ReferencedSOPInstanceUID_src,
                                                                  StudyInstanceUID_src,
                                                                  segment_label,
                                                                  lesion_number)
                dataset_segm.save_as(dcm_file)  # save to disk


# %%

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--rootdir", required=False, help="input single patient folder path to be processed")
    ap.add_argument("-n", "--patient_name", required=False,
                    help="patient name to be encoded into the files. eg: MAVM03")
    ap.add_argument("-u", "--patient_id", required=False, help="patient id to be encoded into the files. eg: M03")
    ap.add_argument("-d", "--patient_dob", required=False, help="patient date of birth in format eg: 19380101")
    ap.add_argument("-b", "--input_batch_proc", required=False,
                    help="input Excel file for batch processing, eg: Batch_processing_MAVERRIC")
    ap.add_argument("-a", '--anonymize_all_dcm_files', required=True,
                    help='flag whether to anonymize all the dcm files or not')
    args = vars(ap.parse_args())
    if args["patient_name"] is not None:
        print("Patient Name:", args["patient_name"])
        print("Patient ID:", args["patient_id"])
        print("Patient date-of-birth:", args["patient_dob"])
        print("Rootdir:", args['rootdir'])
    elif args["input_batch_proc"] is not None:
        print("Batch Processing Enabled, path to csv: ", args["input_batch_proc"])
    else:
        print("no input values provided either for single patient processing or batch processing. System Exiting")
        sys.exit()
        # in case of  batch processing loop through the csv for each patient folder
    # %% Change the Metatags of the Segmentations and the XMLs
    if args["input_batch_proc"] is not None:
        print('Flag to anonymize all files:', args["anonymize_all_dcm_files"])
        # iterate through each patient and send the root dir filepath
        df = pd.read_excel(args["input_batch_proc"])
        df.drop_duplicates(subset=["Patient_ID"], inplace=True)
        df.reset_index(inplace=True)
        df['Patient_Dir_Paths'].fillna("[]", inplace=True)
        df['Patient_Dir_Paths'] = df['Patient_Dir_Paths'].apply(literal_eval)
        # remove the dash from the PatientName variable
        df['Patient Name'] = df['Patient Name'].map(lambda x: x.split('-')[0] + x.split('-')[1])
        for idx in range(len(df)):
            patient_id = str(df["Patient_ID"].iloc[idx])
            patient_dob = str(df['Date_of_Birth'].iloc[idx])
            patient_name = str(df['Patient Name'].iloc[idx])
            patient_dir_paths = df.Patient_Dir_Paths[idx]
            if len(patient_dir_paths) > 0:
                for rootdir in patient_dir_paths:
                    rootdir = os.path.normpath(rootdir)
                    # 1. anonymize ALL the DICOM files
                    if args["anonymize_all_dcm_files"] == 'True':
                        anonymize_all_dcm_files(rootdir, patient_name, patient_id, patient_dob)
                    # for each patient folder associated with a patient encode the DCM and the XML
                    encode_segmentations_dcm_tags(rootdir, patient_name, patient_id, patient_dob)
                    # 2. create dictionary of filepaths and SeriesUIDs
                    list_all_ct_series = create_dict_paths_series_dcm(rootdir)
                    df_ct_mapping = pd.DataFrame(list_all_ct_series)
                    # 3. XML encoding. rewrite the series and the name in the xml after re-writing the broken series uid
                    anonymization_xml_logs.main_encode_xml(rootdir, patient_id, patient_name, patient_dob,
                                                           df_ct_mapping)
                    # 4. create dict of xml and dicom paths
                    df_segmentations_paths_xml = create_dict_paths_series_xml(rootdir)
                    # 5. Edit each DICOM Segmentation File  by adding reference Source CT and the related segmentation
                    if df_segmentations_paths_xml.empty:
                        print('No Segmentations Found for Patient:', rootdir)
                        continue
                    else:
                        main_add_reference_tags_dcm(rootdir, df_ct_mapping, df_segmentations_paths_xml)
                        print("Patient Folder Segmentations Fixed:", patient_name)

    else:
        # single patient folder
        if args["anonymize_all_dcm_files"] == 'True':
            # 1. anonymize ALL the DICOM files
            anonymize_all_dcm_files(args["rootdir"], args["patient_name"], args["patient_id"], args["patient_dob"])
        # 2. create dictionary of filepaths and SeriesUIDs
        encode_segmentations_dcm_tags(args["rootdir"], args["patient_name"], args["patient_id"], args["patient_dob"])
        # 3. XML encoding. rewrite the series and the name in the xml after re-writing the broken series uid
        list_all_ct_series = create_dict_paths_series_dcm(args["rootdir"])
        df_ct_mapping = pd.DataFrame(list_all_ct_series)
        # 4. create dict of xml and dicom paths
        anonymization_xml_logs.main_encode_xml(args["rootdir"], args["patient_id"], args["patient_name"],
                                               args["patient_dob"], df_ct_mapping)
        # create dict of xml and dicom paths
        df_segmentations_paths_xml = create_dict_paths_series_xml(args["rootdir"])
        # 5. Edit each DICOM Segmentation File  by adding reference Source CT and the related segmentation
        if df_segmentations_paths_xml.empty:
            print('No Segmentations Found for Patient:', args["rootdir"])
        else:
            # Edit each DICOM Segmentation File  by adding reference Source CT and the related segmentation
            main_add_reference_tags_dcm(args["rootdir"], df_ct_mapping, df_segmentations_paths_xml)
            print("Patient Folder Segmentations Fixed:", args["patient_name"])
