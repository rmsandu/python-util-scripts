import argparse
import os
import glob
import pydicom
import readInputKeyboard


"""
# 1. give the patient folder as input
# 2. scan for all the dicom files in that folder and if it's a dicom just change the patient id, patient name and study institution
# 3. turn it into an executable
# 4. optional - change the xmls
"""
# folder = ''
# give folder patient name and parse through all files folders
# seg_files = glob.glob('C:\\Pat_MAV_GRON_G01\\*')
ap = argparse.ArgumentParser()
ap.add_argument("-r", "--rootdir", required=True, help="Insert Patient Folder Root Directory")
ap.add_argument("-i", "--patient_id", required=True, help="New Patient ID")
ap.add_argument("-n", "--patient_name", required=True, help="New Patient Name")
ap.add_argument("-dob", "--patient_dob", required=True, help="Patient's BirthDate")
args = vars(ap.parse_args())
#%%
# rootdir = os.path.normpath(readInputKeyboard.getNonEmptyString("Root Directory with Patient Folder"))
# patient_name = readInputKeyboard.getNonEmptyString("New Patient Name ")
# patient_id = readInputKeyboard.getNonEmptyString("New Patient ID, eg. G01 ")
# patient_dob = readInputKeyboard.getNonEmptyString("Patient's BirthDate, format eg. 19540101 ")
#todo: study institution
#todo: physician's name
# seg_files = glob.glob(r"\*")
# patient_id = "G01"
# patient_dob = "19540101"

rootdir = os.path.normpath(args["rootdir"])
patient_id = args["patient_id"]
patient_name = args["patient_name"]
patient_dob = args["patient_dob"]



for subdir, dirs, files in os.walk(rootdir):
    for file in sorted(files):  # sort files by date of creation
        fileName, fileExtension = os.path.splitext(file)
        DcmFilePathName = os.path.join(subdir, file)
        try:
            dcm_file = os.path.normpath(DcmFilePathName)
            dataset = pydicom.read_file(dcm_file)
            dataset.PatientName = patient_name
            dataset.PatientID = patient_id
            dataset.PatientBirthDate = patient_dob
            dataset.save_as(dcm_file)
        except Exception as e:
            print(repr(e))

    # for seg_nr, seg_file in enumerate(seg_files):
    # dataset.InstanceNumber = seg_nr
    # dataset.ImageType = ['DERIVED', 'SECONDARY', 'AXIAL', 'CT_SOM5 SPI']
    # dataset.SeriesInstanceUID = "1.2.840.113564.9.1.2792465697.55.2.5008512924"
    # dataset.AcquisitionTime = "092358.{0:06d}".format(int(seg_nr))
    # dataset.AcquisitionDateTime = "20161220092358.{0:06d}".format(int(seg_nr))
    # dataset.ContentTime = "092358.{0:06d}".format(int(seg_nr))
    # dataset.SeriesNumber = 30
    # dataset.AcquisitionNumber = 20
    # dataset.RescaleType = "HU"
    # dataset.AccessionNumber = "6201271.30"


