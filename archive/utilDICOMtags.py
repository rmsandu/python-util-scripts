#!/usr/bin/env python

import numpy as np
import numpy.linalg
import io
from scipy import misc
import dicom
from dicom.dataset import Dataset, FileDataset
import datetime, time
import os
import uuid
import hashlib
from random import random
import SimpleITK as sitk

def txt_to_mat(xml_tag):
    mat_1 = np.array([[0, 0, 0, 1]])
    mat_34 = np.genfromtxt(io.BytesIO(xml_tag.cdata.encode()))
    mat = np.concatenate([mat_34, mat_1])
    return np.matrix(mat)


def mat_get_rotation(transform_mat):
    rotation_mat = np.eye(4)
    rotation_mat[0:3, 0:3] = transform_mat[0:3, 0:3]
    return rotation_mat


def mat_get_rotation_vec(transform_mat):
    return mat_get_rotation_vec2(transform_mat)


def mat_get_rotation_vec1(transform_mat):
    rotation_vec = np.ndarray(9)
    rotation_mat = mat_get_rotation(transform_mat)
    rotation_vec[0:3] = rotation_mat[0, 0:3]
    rotation_vec[3:6] = rotation_mat[1, 0:3]
    rotation_vec[6:9] = rotation_mat[2, 0:3]
    return rotation_vec


def mat_get_inv(transform_mat):
    return np.linalg.inv(transform_mat)


def mat_get_rotation_vec2(transform_mat):
    rotation_vec = np.ndarray(9)
    rotation_mat = mat_get_rotation(transform_mat)
    rotation_vec[0:3] = rotation_mat[0:3, 0]
    rotation_vec[3:6] = rotation_mat[0:3, 1]
    rotation_vec[6:9] = rotation_mat[0:3, 2]
    return rotation_vec


def mat_get_translation_mat(transform_mat):
    translation_mat = np.eye(4)
    translation_mat[0, 3] = transform_mat[0, 3]
    translation_mat[1, 3] = transform_mat[1, 3]
    translation_mat[2, 3] = transform_mat[2, 3]
    return translation_mat


def mat_get_translation_vec(transform_mat):
    translation_vec = mat_get_translation_mat(transform_mat)[0:3, 3]
    return translation_vec


def mat_get_rot90_y():
    return [[1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, -1, 0],
            [0, 0, 0, 1]]

def img_to_mat(img_file, dtype=np.uint8):
    img = misc.imread(img_file).astype(dtype)
    return img


def write_image_dicom(image, file_name, metadata_file, image_number = 0):
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = 'Secondary Capture Image Storage'
    file_meta.MediaStorageSOPInstanceUID = '1.3.6.1.4.1.9590.100.1.1.111165684411017669021768385720736873780'
    file_meta.ImplementationClassUID = '1.3.6.1.4.1.9590.100.1.0.100.4.0'

    dcm_image = FileDataset(file_name, {}, file_meta=file_meta)

    for tag in metadata_file:
        if tag.name != "Pixel Data":
            dcm_image.add(tag)

    dcm_image.PixelSpacing = ['0.25', '0.25']
    dcm_image.SliceThickness = 1.0
    dcm_image.preamble = "\0" * 128

    dcm_image.Rows = image.shape[0]
    dcm_image.Columns = image.shape[1]
    dcm_image.InstanceNumber = image_number
    dcm_image.PixelData = image.reshape(3, dcm_image.Rows, dcm_image.Columns).tostring()

    dcm_image.save_as(file_name)

def make_uid(entropy_srcs=None, prefix='2.25.'):
    """Generate a DICOM UID value.
    Follows the advice given at:
    http://www.dclunie.com/medical-image-faq/html/part2.html#UID
    Parameters
    ----------
    entropy_srcs : list of str or None
        List of strings providing the entropy used to generate the UID. If
        None these will be collected from a combination of HW address, time,
        process ID, and randomness.
    prefix : prefix
    """
    # Combine all the entropy sources with a hashing algorithm
    if entropy_srcs is None:
        entropy_srcs = [str(uuid.uuid1()), # 128-bit from MAC/time/randomness
                        str(os.getpid()), # Current process ID
                        random().hex() # 64-bit randomness
                       ]
    hash_val = hashlib.sha256(''.join(entropy_srcs))

    # Converet this to an int with the maximum available digits
    avail_digits = 64 - len(prefix)
    int_val = int(hash_val.hexdigest(), 16) % (10 ** avail_digits)

    return prefix  + str(int_val)


class DicomWriter:

    def __init__(self, file_name, series_name, patient_name, patient_id):
        self.file_name = file_name
        self.series_name = series_name
        self.series_number = 1
        self.patient_name = patient_name
        self.patient_id = patient_id
        self.pixel_spacing = [1, 1]
        self.slice_thickness = 1
        self.series_instance_uid = make_uid()
        self.study_instance_uid = make_uid()
        self.study_time = str(time.time())
        self.study_date = str(datetime.date.today()).replace('-', '')
        metadata = os.path.join('data', 'metadata.dcm')
        self.metadata_image = dicom.read_file(metadata)

    def set_study_instance_uid(self, study_instance_uid):
        self.study_instance_uid = study_instance_uid

    def save_volume_to_file(self, volume):
        for slice_idx in range(0, volume.GetSize()[2]):#
            slice_img = volume[:, :, slice_idx]
            slice_img = np.asarray(sitk.GetArrayFromImage(slice_img), dtype=np.uint8)
            slice_file_name = ''.join((self.file_name, str(slice_idx).zfill(3), '.dcm'))
            self.save_image_to_file(slice_img, slice_file_name, slice_idx)

    def save_image_to_file(self, image, file_name, slice_idx):
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = 'Modality Performed Procedure Step SOP Class'
        file_meta.MediaStorageSOPInstanceUID = '1.3.12.2.1107.5.1.4.73448.30000013112907000263500000016'
        file_meta.ImplementationClassUID = '1.3.6.1.4.1.9590.100.1.0.100.4.0'

        dcm_image = FileDataset(file_name, {}, file_meta=file_meta)

        for tag in self.metadata_image:
            if tag.name != "Pixel Data":
                dcm_image.add(tag)

        dcm_image.Modality = 'US'
        dcm_image.SOPInstanceUID = '1.3.12.2.1107.5.1.4.73448.30000013112907000263500000011'
        dcm_image.ContentDate = str(datetime.date.today()).replace('-', '')
        dcm_image.ContentTime = str(time.time())  # milliseconds since the epoch
        dcm_image.StudyDate = self.study_date
        dcm_image.StudyTime = self.study_time
        dcm_image.SeriesDate = self.study_date
        dcm_image.SeriesTime = str(time.time())
        dcm_image.StudyInstanceUID = self.study_instance_uid
        dcm_image.SeriesInstanceUID = self.series_instance_uid
        dcm_image.StudyDescription = 'Ablation Ultraschall'
        dcm_image.Manufacturer = 'ARTORG'
        dcm_image.ImageType = ['ORIGINAL', 'PRIMARY', 'AXIAL', 'CT_SOM5 SPI']
        dcm_image.PhotometricInterpretation = "MONOCHROME1"
        dcm_image.SamplesPerPixel = 1
        dcm_image.HighBit = 7
        dcm_image.BitsStored = 8
        dcm_image.BitsAllocated = 8
        dcm_image.StudyID = '1'
        dcm_image.PatientName = self.patient_name
        dcm_image.PatientID = self.patient_id
        dcm_image.PatientBirthDate = '19410315'
        dcm_image.PatientSex = 'W'
        dcm_image.PatientAge = '072Y'
        dcm_image.InstitutionName = 'Inselspital - Uni Bern'
        dcm_image.PatientPosition = 'HFS'
        dcm_image.RescaleType = 'US'

        dcm_image.SeriesNumber = self.series_number
        dcm_image.PixelSpacing = self.pixel_spacing
        dcm_image.SliceThickness = self.slice_thickness
        dcm_image.SliceLocation = slice_idx * self.slice_thickness
        dcm_image.ImagePositionPatient = ['0', '0', dcm_image.SliceLocation]
        dcm_image.ImageOrientationPatient = ['1', '0', '0', '0', '1', '0']

        dcm_image.preamble = "\0" * 128

        dcm_image.Rows = image.shape[0]
        dcm_image.Columns = image.shape[1]
        dcm_image.InstanceNumber = slice_idx
        dcm_image.SeriesDescription = self.series_name
        dcm_image.PixelData = image  # .reshape(3, dcm_image.Rows, dcm_image.Columns).tostring()
        dcm_image.save_as(file_name)
        print('save file ', slice_idx)
