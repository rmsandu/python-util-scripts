# -*- coding: utf-8 -*-
"""
Created on June 06th 2019

@author: Raluca Sandu
"""
import numpy as np
import untangle as ut
import xml.etree.ElementTree as ET


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

    # re-write the XML and save it
    xmlobj.write(filename)
