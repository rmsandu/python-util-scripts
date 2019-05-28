# -*- coding: utf-8 -*-
"""
Created on Tue Feb 07 11:34:48 2019

@author: Raluca Sandu
"""
import os
import pydicom
import untangle as ut
import xml.etree.ElementTree as ET
#%%
def getInteger(prompt, mustBePositive=False):
    v = None
    while v is None:
        try:
            vIn = input(prompt + ':')
            v = int(vIn)
            if mustBePositive and v < 1:
                print("You must enter a POSITIVE number")
                v = None
        except ValueError:
            print("Non integer value given, please enter a valid integer")
    return v


def getNaturalNumber(prompt):
    return getInteger(prompt, mustBePositive=True)

def getNonEmptyString(prompt):
    v = None
    while v is None or len(v) == 0:
        v = input(prompt + ':').strip()
    return v


def getChoice(prompt, choices):
    assert (type(choices) == list)
    choices = list(map(lambda L: L.lower(), choices))
    clf_name = None
    while clf_name is None:
        clf = input(prompt + ' (any of ' + ",".join(choices) + '):').lower()
        if clf in choices:
            clf_name = clf
            return clf_name
        else:
            print("Oops, you did not enter a valid value from the available choices")


def getChoiceYesNo(prompt, choices):
    assert (type(choices) == list)
    choices = list(map(lambda L: L.lower(), choices))
    clf_name = None
    while clf_name is None:
        clf = input(prompt + ' (any of ' + ",".join(choices) + '):').lower()
        if clf in choices:
            if clf == 'y':
                clf_name = True
            elif clf == 'n':
                clf_name = False
            return clf_name
        else:
            print("Oops, you did not enter a valid value from the available choices")


def encode_xml(filename, patient_id, patient_name, patient_dob):

    xmlobj = ET.parse(filename)
    root = xmlobj.getroot()
    try:
        CT_info = root.findall('CTInfo')
        root.remove(CT_info)
        surgery_date = root.findall('SurgeryInfo')
        root.remove(surgery_date)
    except Exception as e:
        pass # elements not found in XML
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
    xmlobj.write()

    # todo: 2. rreplace the patientid, remove the date of birth

    # modify patient id
    # patient name tag
    # for rank in root.iter():


#%%
# rootdir = os.path.normpath(getNonEmptyString("Root Directory FilePath with Patient Folder"))
# patient_name = getNonEmptyString("New Patient Name ")
# patient_id = getNonEmptyString("New Patient ID, eg. G001 ")
# patient_dob = getNonEmptyString("Patient's BirthDate, format eg. 19540101 ")


rootdir = r"C:\MAVERRIC_STOCK_III\Pat_M53"
patient_name = "MAV-STO-M53"
patient_id = "MAV-M53"
patient_dob = ''
for subdir, dirs, files in os.walk(rootdir):
    for file in sorted(files):  # sort files by date of creation
        fileName, fileExtension = os.path.splitext(file)
        DcmFilePathName = os.path.join(subdir, file)
        if fileExtension.lower().endswith('.xml'):
            xmlFilePathName = os.path.join(subdir, file)
            xmlfilename = os.path.normpath(xmlFilePathName)
            encode_xml(xmlfilename, patient_id, patient_name, patient_dob)

        try:
            dcm_file = os.path.normpath(DcmFilePathName)
            dataset = pydicom.read_file(dcm_file)
            dataset.PatientName = patient_name
            dataset.PatientID = patient_id
            # dataset.PatientBirthDate = patient_dob
            dataset.InstitutionName = "None"
            dataset.InstitutionAddress = "None"

            dataset.save_as(dcm_file)
        except Exception as e:
            pass
            # print(repr(e))

print("Patient Folder Contents Successfully Anonymized:", patient_name)
# os.system("pause")
