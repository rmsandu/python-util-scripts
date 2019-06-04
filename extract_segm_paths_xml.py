import os
import untangle as ut
import pandas as pd


def create_tumour_ablation_mapping(path_xml_recordings):
    """
    :param path_xml_recordings: filepath to where the XML recordings are (date_time)
    :return: dictionary list with tumor and its corresponding ablations per needle trajectory
    """

    list_dict_paths_xml = []

    for subdir, dirs, files in os.walk(path_xml_recordings):

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
                        # match ablation and tumour segmentations based on the needle index
                        # ignore unique values,just loop until you find a not None value for both tumour and ablation at the same needle idx
                        try:
                            dict_series_path_xml = {
                                "NeedleIdx": idx,
                                "PathSeries": el.Segmentation.Path.cdata,
                                "SeriesUID_xml": el.Segmentation.SeriesUID.cdata,
                                "SegmentLabel": el.Segmentation["StructureType"]
                            }
                        except Exception as e:
                            print(repr(e))
                            dict_series_path_xml = {
                                "NeedleIdx": idx,
                                "PathSeries": None,
                                "SeriesUID_xml": None,
                                "SegmentLabel": None
                            }
                list_dict_paths_xml.append(dict_series_path_xml)

        df_paths_one_recordings_xml = pd.DataFrame(list_dict_paths_xml)

        return df_paths_one_recordings_xml
