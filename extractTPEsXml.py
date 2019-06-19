# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 11:17:01 2018

@author: Raluca Sandu
"""
from elementExistsXml import elementExists


def extractTPES(measurement):
    """ extract the TPEs (target positioning errors) values.

    :param measurement: singleTrajectory.Measurements.Measurement.TPEErrors
    :return: target errors as tuple of 5
    """

    tpes = measurement.TPEErrors
    if elementExists(tpes, 'targetLateral'):
        entryLateral = tpes['entryLateral'][0:5]
        targetLateral = tpes['targetLateral'][0:5]
        targetLongitudinal = tpes['targetLongitudinal'][0:5]
        targetAngular = tpes['targetAngular'][0:5]
        targetEuclidean = tpes['targetResidualError'][0:5]
    else:
        # the case where the TPE errors are 0 in the TPE<0>. instead they are attributes of the measurement
        entryLateral = measurement['entryLateral'][0:5]
        targetLateral = measurement['targetLateral'][0:5]
        targetLongitudinal = measurement['targetLongitudinal'][0:5]
        targetAngular = measurement['targetAngular'][0:5]
        targetEuclidean = measurement['targetResidualError'][0:5]
        
    return entryLateral, targetLateral, targetAngular, targetLongitudinal, targetEuclidean