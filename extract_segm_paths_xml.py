import os
import untangle as ut
import pandas as pd


def create_tumour_ablation_mapping(path_xml_recordings):
    """
    :param path_xml_recordings: filepath to where the XML recordings are (date_time)
    :return: dictionary list with tumor and its corresponding ablations per needle trajectory
    """
    for subdir, dirs, files in os.walk(path_xml_recordings):
        list_dict_paths_xml = []
        for file in sorted(files):
            xml_file = os.path.join(subdir, file)
            if "AblationValidation_" or "Plan_" in file:
                xmlobj = ut.parse(xml_file)
                trajectories = xmlobj.Eagles.Trajectories
                for idx, tr in trajectories:
                    single_tr = tr.Trajectory
                    for el in single_tr:
                        # match ablation and tumour segmentations based on the needle index
                        # ignore unique values,just loop until you find a not None value for both tumour and ablation at the same needle idx
                        try:
                            dict_series_path_xml = {
                                "needle_idx": idx,
                                "path_series_no_xml": el.Segmentation.Path.cdata,
                                "series_uid_xml": el.Segmentation.SeriesUID.cdata,
                                "segment_label": el.Segmentation["StructureType"]
                            }
                        except Exception as e:
                            print(repr(e))
                            dict_series_path_xml = {
                                "needle_idx": idx,
                                "path_series_no_xml": None,
                                "series_uid_xml": None,
                                "segment_label": None
                            }
                list_dict_paths_xml.append(dict_series_path_xml)

    df_paths_one_recordings_xml = pd.DataFrame(list_dict_paths_xml)

    return df_paths_one_recordings_xml
