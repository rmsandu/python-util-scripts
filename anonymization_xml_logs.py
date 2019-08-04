# -*- coding: utf-8 -*-
"""
Created on June 06th 2019

@author: Raluca Sandu
"""
import numpy as np
import untangle as ut
import xml.etree.ElementTree as ET


def encode_xml(filename, patient_id, patient_name, patient_dob,  df_ct_mapping):
    """
    Remove the identifying information from the XML files. Update the SeriesInstanceUID
    :param filename:
    :param patient_id:
    :param patient_name:
    :param patient_dob:
    :param SeriesInstanceUID:
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
