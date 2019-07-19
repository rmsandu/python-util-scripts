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
                        # ignore unique values
                        # just loop until you find a not None value for both tumour and ablation at the same needle idx
                        try:
                            segmentation = el.Segmentation
                            # todo: sphere case, what happens when no segmentation path available
                        except AttributeError:
                            # no segmentation found in this trajectory
                            continue  # go back to the beginning of the loop
                        try:
                            segmentation_series_uid = el.Segmentation.SeriesUID.cdata
                        except AttributeError:
                            print("No segmentation series uid for this segmentation")
                            segmentation_series_uid = None
                        try:
                            segmentation_path_series = el.Segmentation.Path.cdata
                        except AttributeError:
                            print('no segmentation path available')
                            segmentation_path_series = None
                        try:
                            type_of_segmentation = el.Segmentation["TypeOfSegmentation"]
                        except AttributeError:
                            type_of_segmentation = None

                        try:
                            sphere_radius = el.Segmentation["SphereRadius"]
                        except AttributeError:
                            sphere_radius = None

                        dict_series_path_xml = {
                            "Timestamp": xmlobj.Eagles["time"],
                            "NeedleIdx": idx,
                            "SourceSeriesID": xmlobj.Eagles.PatientData["seriesID"],
                            "PathSeries": segmentation_path_series,
                            "SegmentationSeriesUID_xml": segmentation_series_uid,
                            "SegmentLabel": el.Segmentation["StructureType"],
                            "TypeOfSegmentation": type_of_segmentation,
                            "SphereRadius": sphere_radius
                        }

                        if segmentation_series_uid and sphere_radius is not None:
                            try:
                                # if the ct series is not found in the dictionary, add it
                                series_uid_found = next((item for item in list_segmentations_paths_xml if
                                                         item["SegmentationSeriesUID_xml"] == segmentation_series_uid),
                                                        None)
                                sphere_radius = next(
                                    (item for item in list_segmentations_paths_xml if item["SphereRadius"] == sphere_radius),
                                    None)
                            except AttributeError:
                                print('WTF')
                                # print(list_segmentations_paths_xml)
                            if series_uid_found is not None or sphere_radius is not None:
                                # only add unique segmentations paths, skip duplicates
                                list_segmentations_paths_xml.append(dict_series_path_xml)

        return list_segmentations_paths_xml
