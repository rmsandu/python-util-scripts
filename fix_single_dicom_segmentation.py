
import pydicom
from pydicom import uid
from pydicom.sequence import Sequence
from pydicom.dataset import Dataset

dcm_file = r"C:\develop\python-util-scripts\000"
dcm_file_src = r"C:\tmp_patients\Pat_M6\Study_840\Series_16\CT.1.2.392.200036.9116.2.6.1.37.2424156402.1461027540.552370"
dataset_segm = pydicom.read_file(dcm_file)
dataset_src = pydicom.read_file(dcm_file_src)

# next lines will be executed only if the file is DICOM
dataset_segm.PatientName = "Casper Casper"
dataset_segm.PatientID = "99"
dataset_segm.PatientBirthDate = "19600101"
dataset_segm.InstitutionName = "None"
dataset_segm.InstitutionAddress = "None"
dataset_segm.SliceLocation = dataset_segm.ImagePositionPatient[2]
dataset_segm.SOPInstanceUID = uid.generate_uid()
dataset_segm.InstanceNumber = 1

dataset_segm.SegmentLabel = "Tumour"
dataset_segm.SegmentationType = "BINARY"
dataset_segm.SegmentAlgorithmType = "SEMIAUTOMATIC"
dataset_segm.DerivationDescription = "Segmentation mask done with CAS-ONE IR segmentation algorithm"
dataset_segm.ImageType = "DERIVED\PRIMARY"
dataset_segm.SOPClassUID = "1.2.840.10008.5.1.4.1.1.66.4"  # the sop class for segmentation

Segm_ds = Dataset()
Segm_ds.ReferencedSOPInstanceUID = dataset_segm.SeriesInstanceUID
Segm_ds.ReferencedSOPClassUID = dataset_segm.SOPClassUID

Source_ds = Dataset()
Source_ds.ReferencedSOPInstanceUID = dataset_src.SeriesInstanceUID
Source_ds.ReferencedSOPClassUID = dataset_src.SOPClassUID

dataset_segm.ReferencedImageSequence = Sequence([Segm_ds])
dataset_segm.SourceImageSequence = Sequence([Source_ds])


dataset_segm.save_as(dcm_file)

print(dataset_segm)
