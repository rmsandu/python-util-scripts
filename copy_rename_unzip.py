# -*- coding: utf-8 -*-
"""
Created on Wed Jun  6 10:10:24 2018

@author: Raluca Sandu
"""
import os
import shutil
import zipfile
from splitAllPaths import splitall as split_paths
# TODO: 1. copy/paste folders from folder dir to another one
# TODO 2. rename folder
# TODO 3. move Study0 to root folder
# TODO 4. unzip folders
# TODO 5 . convert to cmd line script . Input: rootdir
# TODO 6. remove the German umlauts and the French umlauts from the names

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
#%%
rootdir = r"C:\develop\data\PATS"

dictionary_filepaths = {}
# the filepaths are already saved in a CSV
for dirs in os.listdir(rootdir):
    if not os.path.isdir(os.path.join(rootdir, dirs)):
         continue # Not a directory
    if "Pat" in dirs:
        # rename folder
        os.rename(os.path.join(rootdir,dirs),
                  os.path.join(rootdir, dirs[dirs.find('Pat'):]))
#%%
for path, dirs, files in os.walk(rootdir):
    index_ir = [i for i, s in enumerate(dirs) if 'IR Data' in s]
    index_xml = [i for i, s in enumerate(dirs) if 'XML' in s]
    if index_ir:
        ir_data_dir = dirs[index_ir[0]]
        src = os.path.join(path,ir_data_dir)
        all_folders = split_paths(src)
        index = [i for i, s in enumerate(all_folders) if 'Pat' in s]
        dst = os.path.join(rootdir, all_folders[index[0]])
        copytree(src,dst)
    if index_xml:
        xml_dir = dirs[index_xml[0]]
        xml_dir = os.path.join(path, xml_dir)
        for file in os.listdir(xml_dir):
            if file.endswith(".zip"):
                filename, file_extension = os.path.splitext(file)
                # unzip file xml recordings
                zip_filepath = os.path.join(xml_dir,file)
                with zipfile.ZipFile(zip_filepath,"r") as zip_ref:
                    zip_ref.extractall(os.path.join(xml_dir,filename))
                    zip_ref.close()
