# -*- coding: utf-8 -*-
"""
Created on June 06th 2019

@author: Raluca Sandu
"""
import os
import xml.etree.ElementTree as ET


def encode_xml(filename, patient_id, patient_name, patient_dob,  df_ct_mapping):
    """
    Remove the identifying information from the XML files. Update the SeriesInstanceUID after modifying the corrupt DICOM
    :param filename:
    :param patient_id:
    :param patient_name:
    :param patient_dob:
    :param df_ct_mapping:
    :return:
    """
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
            pat.set('DOB', patient_dob[0:4] + '-01-01')
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

    for segmentation in root.iter('Segmentation'):
        path = segmentation.find('Path').text
        series_uid = segmentation.find('SeriesUID').text
        # update the series_uid
        idx_segm_xml = df_ct_mapping.index[
            df_ct_mapping["PathSeries"] == path].tolist()[0]
        series_instance_uid = df_ct_mapping.loc[idx_segm_xml].SeriesInstanceNumberUID
        for el in segmentation:
            if el.tag == 'SeriesUID':
                el.text = series_instance_uid

    # re-write the XML and save it
    xmlobj.write(filename)


def main_encode_xml(rootdir, patient_id, patient_name, patient_dob, df_ct_mapping):
    """

    :param rootdir:
    :param patient_id:
    :param patient_name:
    :param patient_dob:
    :param df_ct_mapping:
    :return:
    """
    for subdir, dirs, files in os.walk(rootdir):
        for file in sorted(files):  # sort files by date of creation
            fileName, fileExtension = os.path.splitext(file)
            if fileExtension.lower().endswith('.xml'):
                xmlFilePathName = os.path.join(subdir, file)
                xmlfilename = os.path.normpath(xmlFilePathName)
                encode_xml(xmlfilename, patient_id, patient_name, patient_dob, df_ct_mapping)

