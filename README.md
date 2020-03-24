# Repository for Python Snipets
- plotting and saving plots in good format ready for publications (high resolution, readable axis labels etc, friendly colours)
- util scripts for processing XML files
- util scripts for reading DICOM CT files
- util for modifying DICOM Tags

The snippets package contains the following modules:
* `DicomReader.py` - reads DICOM files using SimpleITK
* `scatter_plot` - takes different `kwargs` from a DataFrame and plots different types of scatter plots
* `pie_chart_scatter_plot` - scatter plot using pie charts as markers
* `DicomWriter.py`- writes DICOM files to disk using SimpleITK
* `anonymization_dicom` -- simple script using pydicom to remove the patient's id, name and study institution from DICOM Images
* `readInputKeyboard` -- getting user input for modular scripts
* `casxmlreader` -- reading XML Cas Logs for data extraction
* `Tiff2Nii` -- parse MEVIS TIff Image Files to NIfTI format https://nifti.nimh.nih.gov/nifti-1/
* `surface` -- library for computing surface distance metrics
* `utilCThistogram` -- reading plotting histogram of a DICOM CT Image
