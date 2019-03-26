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


seg_files = glob.glob(r"\*")



for seg_nr, seg_file in enumerate(seg_files):
    dataset = pydicom.read_file(seg_file)
    dataset.PatientName = "GRON-001-G01"
    dataset.PatientID = "G01"
    dataset.PatientBirthDate = "19540101"
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

    dataset.save_as(seg_file)
