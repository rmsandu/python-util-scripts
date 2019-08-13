for subdir, dirs, files in os.walk(rootdir):
    # get the source image sequence attribute - SOPClassUID
    dcm_file_source = os.path.normpath(DcmFilePathName)
    dataset_source_ct = pydicom.read_file(dcm_file)
    source_series_instance_uid = dataset_source_ct.SeriesInstanceUID
    source_series_number = dataset_source_ct.SeriesNumber

    # todo: assign correctly the series instance from plan series to tumour segm
    # todo: assign correctly the series instance from validation series to ablation segm
    if 'SeriesNo_' and 'Segmentations' in subdir:
        for file in sorted(files):  # sort files by date of creation
            DcmFilePathName = os.path.join(subdir, file)
            try:
                k = 1
                # modify only the segmentation files --> if the files are in the "Segmentations" files
                # InstanceNumber, SliceLocation, SOPInstanceUID
                # what about the SOPClassUID?
                dcm_file = os.path.normpath(DcmFilePathName)
                dataset = pydicom.read_file(dcm_file)
                dataset.PatientName = patient_name
                dataset.PatientID = patient_id
                dataset.PatientBirthDate = patient_dob
                dataset.InstitutionName = "None"
                dataset.InstitutionAddress = "None"
                # dataset_segm.SOPInstanceUID = make_uid()
                dataset.SliceLocation = dataset.ImagePositionPatient[2]
                dataset.SOPInstanceUID = uid.generate_uid()
                dataset.InstanceNumber = k
                k += 1
                dataset.ImageType = "DERIVED\SECONDARY\AXIAL"
                dataset.SourceInstanceSequence = source_series_instance_uid
                dataset.DerivationDescription = source_series_number
                # todo:
                # should we modify the series number as well? now identical to the source ct
                dataset.save_as(dcm_file)

            except Exception as e:
                pass
                print(repr(e))
