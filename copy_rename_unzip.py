# -*- coding: utf-8 -*-
"""
Created on Wed Jun  6 10:10:24 2018

@author: Raluca Sandu
"""

import os
import sys
import shutil
import zipfile
import pandas as pd
from splitAllPaths import splitall as split_paths


# TODO 6. remove the German umlauts and the French umlauts from the names
# TODO 7. create excel with name of each patient folder given root folder
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            try:
                shutil.copytree(s, d, symlinks, ignore)
            except Exception:
                print('Filename greater than 255 characters: ', s)
                # TODO: rename the files and folders???
                continue
        else:
            shutil.copy2(s, d)


def copy_rename(src_dir, dst_dir, keyword):
    """
    Copy all patient folders from src_dir to dest_dir and save the filenames to Excel
    :param src_dir: [string]. source directory where the files are
    :param dst_dir: [string]. destination directory where the files will be copied
    :param keyword: [string]. here keyword = "Pat". a repeating keyword to identify main patient folder
    :return: Excel with saved filenames and filepathss
    """
    dict_filenames = []
    pat_counter = 0
    # Copy all patient folders from src_dir to dest_dir'''
    copytree(src_dir, dst_dir)
    # iterate through each pat directory and rename it
    for dirs in os.listdir(dst_dir):
        if not os.path.isdir(os.path.join(dst_dir, dirs)):
            continue
        else:
            if keyword in dirs:
                # save filenames and filepaths to dict
                pat_folder_name = dirs[dirs.find(keyword):]
                pat_filepath = os.path.join(dst_dir, dirs[dirs.find(keyword):])
                pat_counter += 1
                patient_info = {"PatientID": pat_counter,
                                "Patient Folder Name": pat_folder_name,
                                "Filepath to Patient Folder": pat_filepath,
                                "Segmentation done by": '',
                                "Segmentation Date": ''}
                dict_filenames.append(patient_info)
                # rename folder
                os.rename(os.path.join(dst_dir, dirs),
                          os.path.join(dst_dir, dirs[dirs.find(keyword):]))
    # write to dataframe
    df_filenames = pd.DataFrame(dict_filenames)
    filename = 'Segmentations_Info_' + '.xlsx'
    filepath_excel = os.path.join(dst_dir, filename)
    writer = pd.ExcelWriter(filepath_excel)
    df_filenames.to_excel(writer, index=False)


def move_unzip(dst_dir, keyword):
    """
    Move Study to Root folder and Unzip XML Recordings
    :param dst_dir: 
    :param keyword:
    """
    for path, dirs, files in os.walk(dst_dir):
        index_ir = [i for i, s in enumerate(dirs) if 'IR Data' in s]
        index_xml = [i for i, s in enumerate(dirs) if 'XML' in s]
        if index_ir:
            # move Study folder to root patient folder
            # TODO: only if necesary!! condition needed
            ir_data_dir = dirs[index_ir[0]]
            src = os.path.join(path, ir_data_dir)
            all_folders = split_paths(src)
            index = [i for i, s in enumerate(all_folders) if keyword in s]
            dst = os.path.join(dst_dir, all_folders[index[0]])
            copytree(src, dst)
        if index_xml:
            # unzip the XML Recordings
            xml_dir = dirs[index_xml[0]]
            xml_dir = os.path.join(path, xml_dir)
            for file in os.listdir(xml_dir):
                if file.endswith(".zip"):
                    filename, file_extension = os.path.splitext(file)
                    # unzip file xml recordings
                    zip_filepath = os.path.join(xml_dir, file)
                    with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
                        zip_ref.extractall(os.path.join(xml_dir, filename))
                        zip_ref.close()
    print("Done! All files and folders copied and renamed")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(" To few arguments, please specify a source directory, a destination directory and a keyword for every"
              " patients folder name ")
        exit()
    else:
        source_directory = os.path.normpath(sys.argv[1])
        print("Source Directory:", source_directory)
        destination_directory = os.path.normpath(sys.argv[2])
        print("Destination Directory:", destination_directory)
        keyword_folder_name = sys.argv[3]
        print("Keyword for Patient Folder: ", keyword_folder_name)
        copy_rename(source_directory, destination_directory, keyword_folder_name)
        move_unzip(destination_directory, keyword_folder_name)
#   src_dir = "C:\develop\data\PATS" # source directory from where to copy the folders/files
#   dst_dir = "C:\develop\data\TEST_DIR" # destination directory to where copy folders/files
