#!/usr/bin/env python

import untangle as ut
import os
import util
import transformations as tf
import math


def read_recording_xml(xmlfilename, toolid):
    folder = os.path.dirname(xmlfilename)
    tree = ut.parse(xmlfilename)

    calibration = {'transform': util.txt_to_mat(tree.Eagles.ToolCalibration.Tools.Tool[toolid].Transform),
                   'scaling': util.txt_to_mat(tree.Eagles.ToolCalibration.Tools.Tool[toolid].Scaling)}
    calibration_mat = calibration['transform']
    scaling_mat = calibration['scaling']

    images = []
    data = tree.Eagles.DataSet.Datum

    for datum in data:
        try:
            filename = datum.Raw.Image['filename']
            filepath = os.path.join(folder, filename)
            img_mat = util.img_to_mat(filepath)
            pose = util.txt_to_mat(datum.Raw.Marker.Pose)
            usimage = {'filename': filepath,
                       'image_data': img_mat,
                       'pose': util.mat_get_rot90_y() * pose * calibration_mat,
                       'calibration': calibration_mat,
                       'scaling': scaling_mat}
            images.append(usimage)
        except Exception:
            pass

    return images