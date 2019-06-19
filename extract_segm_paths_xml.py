# -*- coding: utf-8 -*-
"""
Created  June 2019

@author: Raluca Sandu
"""
import os
import untangle as ut


def create_tumour_ablation_mapping(dir_xml_files, list_segmentations_paths_xml):
    """
    Parses all the XML Files in a given directory and extracts the Source SeriesInstanceSeries on which the segmentation
    files were annotated and the SeriesInstanceUID of the segmentations
    :param list_segmentations_paths_xml: list of dicts with SeriesInstanceUID, TimeStamp adn SourceUID of segmentation files
    :param dir_xml_files: filepath to where the XML recordings are (date_time)
    :return: list_segmentations_paths_xml: Pandas DF with segmentation Sorur
    """

    # list_dict_paths_xml = []

    for subdir, dirs, files in os.walk(dir_xml_files):

        for file in sorted(files):
            xml_file = os.path.join(subdir, file)
            if file.startswith('AblationValidation_') or file.startswith('Plan_'):
                try:
                    xmlobj = ut.parse(xml_file)
                except Exception as e:
                    # the file is not an xml
                    continue
                try:
                    trajectories = xmlobj.Eagles.Trajectories
                except Exception as e:
                    print(repr(e))
                    continue
                for idx, tr in enumerate(trajectories):
                    single_tr = tr.Trajectory
                    for el in single_tr:
                        # do the source series mapping based on the seriesID from the XML PatientData
                        # match ablation and tumour segmentations based on the needle index
                        # ignore unique values, just loop until you find a not None value for both tumour and ablation at the same needle idx

                        try:
                            # check that both variables exist at the same time in the XML file
                            el.Segmentation.Path.cdata
                            xmlobj.Eagles.PatientData["seriesID"]
                        except AttributeError:
                            continue  # go back to the beginning of the loop

                        try:
                            dict_series_path_xml = {
                                "Timestamp": xmlobj.Eagles["time"],
                                "NeedleIdx": idx,
                                "SourceSeriesID": xmlobj.Eagles.PatientData["seriesID"],
                                "PathSeries": el.Segmentation.Path.cdata,
                                "SegmentationSeriesUID_xml": el.Segmentation.SeriesUID.cdata,
                                "SegmentLabel": el.Segmentation["StructureType"]
                            }
                        except Exception as e:
                            print(repr(e))
                            dict_series_path_xml = {
                                "Timestamp": xmlobj.Eagles["time"],
                                "NeedleIdx": idx,
                                "SourceSeriesID": None,
                                "PathSeries": None,
                                "SegmentationSeriesUID_xml": None,
                                "SegmentLabel": None
                            }
                    try:
                        dict_series_path_xml
                    except NameError:
                        # do nothing, no dict_series_path_xml variable created
                        continue
                    # if the ct series is not found in the dictionary, add it
                    result = next((item for item in list_segmentations_paths_xml if
                                   item["SegmentationSeriesUID_xml"] == el.Segmentation.SeriesUID.cdata), None)
                    if result is None:
                        # only add unique segmentations paths, skip duplicates
                        list_segmentations_paths_xml.append(dict_series_path_xml)


        return list_segmentations_paths_xml
