// --------------------------------
// <copyright file="casEfficacyMeasurements.cpp" company="CAScination AG">
//     This file contains proprietary code.Copyright (c) 2009 - 2018. All rights reserved
// </copyright>
// <author>Radek Hrabuska</author>
// <email>Radek.Hrabuska@artorg.unibe.ch</email>
// <date>05.02.2018 00:00:00</date>
// ---------------------------------

#include "casEfficacyMeasurements.h"

#include "casTumorSegmentation.h"
#include "casSegmentationEvaluationTools.h"
#include "casRegistrationData.h"


#include "base/egItkImageUtils.h"
#include "casDICOMWrite.h"
#include <itkPasteImageFilter.h>

#include "core/egException.h"
#include "base/egPatientRegistrationData.h"
#include "itkImageDuplicator.h"

typedef itk::ImageDuplicator< egItkUC3DImageType > t_ItkDuplicatorType;
typedef itk::PasteImageFilter <egItkUC3DImageType, egItkUC3DImageType > PasteImageFilterType;

casEfficacyMeasurements::casEfficacyMeasurements(const casSegmentationDataWrapper::t_Ptr a_PlanningData, const casSegmentationDataWrapper::t_Ptr a_ValidationData)
{
}

casEfficacyMeasurements::~casEfficacyMeasurements()
{
}

bool casEfficacyMeasurements::computeEfficacyMeasurement(const int a_TrajectoryID, casSegmentationDataWrapper::t_Ptr a_PlanningDataInstance, casSegmentationDataWrapper::t_Ptr a_ValidationData, const casRegistrationData * v_RegistrationData)
{

    //check whether segmentation masks are initialized
    casStructureIR::t_Ptr v_SegmentationMask = casTumorSegmentation::getSegmentationForTrajectory(a_PlanningDataInstance, a_TrajectoryID);
    if (!v_SegmentationMask) {
        return false;
    }

    egItkUC3DImageType::SpacingType v_Spacing = a_PlanningDataInstance->getBrush()->getSpacing();
    egItkUC3DImagePtr v_TumorMaskItk = casTumorSegmentation::extractItkSegmentationMask(v_SegmentationMask, v_Spacing, a_PlanningDataInstance);

    if (!v_TumorMaskItk) {
        return false;
    }

    v_SegmentationMask = casTumorSegmentation::getSegmentationForTrajectory(a_ValidationData, a_TrajectoryID);
    if (!v_SegmentationMask) {
        return false;
    }

   v_Spacing = a_ValidationData->getBrush()->getSpacing();
    egItkUC3DImagePtr v_AblationMaskItk = casTumorSegmentation::extractItkSegmentationMask(v_SegmentationMask, v_Spacing, a_PlanningDataInstance);

    if (!v_AblationMaskItk) {
        return false;
    }

    TransMatrix3d v_RegistrationMatrix = TransMatrix3d::getIdentity();

    casRegistrationData::t_RegistrationType v_Type = v_RegistrationData->getRegistrationType();

    if (v_Type == casRegistrationData::t_RegistrationType::TRANSLATION) {
        v_RegistrationMatrix.setRotation(v_RegistrationData->getPatientRegistrationData().getRigidPatientRegistration().getRotation());
        v_RegistrationMatrix.setTranslation(v_RegistrationData->getPatientRegistrationData().getRigidPatientRegistration().getTranslation());
    } else if (v_Type == casRegistrationData::t_RegistrationType::NONE) {
        v_RegistrationMatrix = TransMatrix3d::getIdentity();
    } else if (v_Type == casRegistrationData::t_RegistrationType::RIGID_REGISTRATION) {
        v_RegistrationMatrix.setRotation(v_RegistrationData->getPatientRegistrationData().getRigidPatientRegistration().getRotation());
        v_RegistrationMatrix.setTranslation(v_RegistrationData->getPatientRegistrationData().getRigidPatientRegistration().getTranslation());

    }

    //compute measurements
    m_Measurement = new casEfficacyMeasurements::s_EfficacyScores();
    try
    {
        try
        {
            try
            {
                m_Measurement = efficacyMeasurement(v_TumorMaskItk, v_AblationMaskItk, v_RegistrationMatrix);
            }
            catch (itk::ExceptionObject e)
            {
                egError("Efficacy metrics failed to compute, because: " + std::string(e.GetDescription()));
                return false;
            }
        }
        catch (egException e)
        {
            egError("Efficacy metrics failed to compute, because: " + std::string(e.whatString()));
            return false;
        }
    }
    catch (std::exception e)
    {
        egError("Efficacy metrics failed to compute, because: " + std::string(e.what()));
        return false;
    }
    return true;
}

egItkUC3DImagePtr getDuplicatedImgROI(egItkUC3DImagePtr a_segmentationImage)
{
    t_ItkDuplicatorType::Pointer v_ImageDuplicator = t_ItkDuplicatorType::New();

    egItkUC3DImageType::Pointer v_ITKImageResized;
    v_ImageDuplicator->SetInputImage(a_segmentationImage);
    v_ImageDuplicator->Update();
    v_ITKImageResized = v_ImageDuplicator->GetOutput();

    casSegmentationEvaluationTools::getImgROI(v_ITKImageResized);

    return v_ITKImageResized;
}

egItkUC3DImagePtr casEfficacyMeasurements::getReorientedImage(egItkUC3DImagePtr a_OriginalImage, egItkUC3DImagePtr a_ImageToReorient)
{
    egItkUC3DImagePtr v_duplicatedImg = getDuplicatedImgROI(a_OriginalImage);

    itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_IteratorForItkIm(v_duplicatedImg, v_duplicatedImg->GetLargestPossibleRegion());
    v_IteratorForItkIm.GoToBegin();
    while (!v_IteratorForItkIm.IsAtEnd()) {
        v_IteratorForItkIm.Set(0);
        ++v_IteratorForItkIm;
    }

    PasteImageFilterType::Pointer v_PasteFilter = PasteImageFilterType::New();

    v_PasteFilter->SetDestinationImage(v_duplicatedImg);
    v_PasteFilter->SetSourceImage(a_ImageToReorient);
    v_PasteFilter->SetSourceRegion(a_ImageToReorient->GetLargestPossibleRegion());

    egItkUC3DImageType::PointType v_ItkPixelLocationPointinSpace;
    egItkUC3DImageType::IndexType v_ItkPixelLocationCoordinatesInImage;
    a_ImageToReorient->TransformIndexToPhysicalPoint(a_ImageToReorient->GetLargestPossibleRegion().GetIndex(), v_ItkPixelLocationPointinSpace);
    v_duplicatedImg->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);

    v_PasteFilter->SetDestinationIndex(v_ItkPixelLocationCoordinatesInImage);
    v_PasteFilter->Update();

    egItkUC3DImagePtr v_ReorientedImage = v_PasteFilter->GetOutput();

    return v_ReorientedImage;
}

casEfficacyMeasurements::s_EfficacyScores * casEfficacyMeasurements::efficacyMeasurement(const egItkUC3DImagePtr a_ITKImageTumour, const egItkUC3DImagePtr a_ITKImageAblation, const TransMatrix3d & a_TransformationMatrix)
{

    egItkUC3DImagePtr v_ITKImageTumourResized = getDuplicatedImgROI(a_ITKImageTumour);
    egItkUC3DImagePtr v_ITKImageAblationResized = getDuplicatedImgROI(a_ITKImageAblation);

    //Make the measurements:
    egItkUC3DImagePtr v_ITKImageAblationResizedRotated = casSegmentationEvaluationTools::TransformImageAccordingToRegistration(v_ITKImageAblationResized, a_TransformationMatrix);

    casSegmentationEvaluationTools::resampleMasksToSameSpacing(v_ITKImageAblationResizedRotated, v_ITKImageTumourResized);

    egItkUC3DImagePtr v_BBImage = casSegmentationEvaluationTools::FindBoundingBoxForTwoImages(v_ITKImageAblationResizedRotated, v_ITKImageTumourResized);

    v_ITKImageAblationResized = v_BBImage;
    egItkUC3DImageType::IndexType v_ItkIndex = v_ITKImageAblationResized->GetLargestPossibleRegion().GetIndex();
    egItkUC3DImageType::PointType v_ItkPoint;
    v_ITKImageAblationResized->TransformIndexToPhysicalPoint(v_ItkIndex, v_ItkPoint);

    v_ITKImageAblationResized->SetOrigin(v_ItkPoint);

    v_ItkIndex[0] = 0;
    v_ItkIndex[1] = 0;
    v_ItkIndex[2] = 0;

    egItkUC3DImageType::RegionType v_Reg = v_ITKImageAblationResized->GetLargestPossibleRegion();
    v_Reg.SetIndex(v_ItkIndex);
    v_ITKImageAblationResized->SetRegions(v_Reg);

    casSegmentationEvaluationTools::findCommonBoundingBox(v_ITKImageAblationResized, v_ITKImageTumourResized);

    s_EfficacyScores * v_InterMeasurement = new s_EfficacyScores();
    v_InterMeasurement->m_DiceIndex = casSegmentationEvaluationTools::GetDiceIndex(v_ITKImageAblationResized, v_ITKImageTumourResized);

    s_ResultsMargins Margins = getMarginsBetweenBorders(v_ITKImageAblationResized, v_ITKImageTumourResized);
    v_InterMeasurement->m_MeanMargin = Margins.m_Mean;
    v_InterMeasurement->m_MedianMargin = Margins.m_Median;
    v_InterMeasurement->m_SmallestMargin = Margins.m_Minimal;
    v_InterMeasurement->m_MaximalMargin = Margins.m_Maximal;
    v_InterMeasurement->m_HistogramBins = Margins.m_HistogramBins;
    v_InterMeasurement->m_SD = Margins.m_SD;

    //Volume measures
    v_InterMeasurement->m_Volumes = measureSegmentationVolumes(v_ITKImageTumourResized, v_ITKImageAblationResized);

    v_InterMeasurement->m_TumorCoverageRatio = calculateCoverageRatio(v_InterMeasurement->m_Volumes.m_TumourResidualVolumeML, v_InterMeasurement->m_Volumes.m_TumourVolumeML);

    float v_MarginSize = 5;
    v_InterMeasurement->m_AblationMarginCoverage5 = getAblationMarginCoverageRatio(v_ITKImageTumourResized, v_ITKImageAblationResized, v_MarginSize);

    v_MarginSize = 10;
    v_InterMeasurement->m_AblationMarginCoverage10 = getAblationMarginCoverageRatio(v_ITKImageTumourResized, v_ITKImageAblationResized, v_MarginSize);

    return v_InterMeasurement;
}

float casEfficacyMeasurements::getAblationMarginCoverageRatio(egItkUC3DImagePtr a_TumorMask, egItkUC3DImagePtr a_AblationMask, float & a_MarginSize)
{
    egItkUC3DImagePtr v_AblMargin = getAblationMargin(a_TumorMask, a_MarginSize);
    casSegmentationEvaluationTools::findCommonBoundingBox(a_AblationMask, v_AblMargin);
    s_VolumesStructure v_AblMarginVolumes = measureSegmentationVolumes(v_AblMargin, a_AblationMask);
    return calculateCoverageRatio(v_AblMarginVolumes.m_TumourResidualVolumeML, v_AblMarginVolumes.m_TumourVolumeML);
}

egItkUC3DImagePtr casEfficacyMeasurements::getAblationMargin(egItkUC3DImagePtr a_TumourMask, float a_SizeOfMargin)
{
    egItkUC3DImageType::IndexType v_Padding;

    v_Padding[0] = abs(a_SizeOfMargin) * (1 / a_TumourMask->GetSpacing()[0]) +1;
    v_Padding[1] = abs(a_SizeOfMargin) * (1 / a_TumourMask->GetSpacing()[1]) +1;
    v_Padding[2] = abs(a_SizeOfMargin) * (1 / a_TumourMask->GetSpacing()[2]) +1;

    egItkUC3DImagePtr v_PaddedTumourMask = casTumorSegmentation::AddPaddingToItkMask(a_TumourMask, v_Padding);
    t_OutputImageTypePtr v_DistanceMap = casSegmentationEvaluationTools::GetSignedMaurerDistanceMap(v_PaddedTumourMask);

    itk::ImageRegionIteratorWithIndex<t_OutputImageType> v_DistanceImageIterator(v_DistanceMap, v_DistanceMap->GetLargestPossibleRegion());
    itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_MaskImageIterator(v_PaddedTumourMask, v_PaddedTumourMask->GetLargestPossibleRegion());

    for (v_DistanceImageIterator.GoToBegin(); !v_DistanceImageIterator.IsAtEnd(); ++v_DistanceImageIterator) {
        v_MaskImageIterator.SetIndex(v_DistanceImageIterator.GetIndex());

        float v_CurrentSize = 0;
        v_CurrentSize = v_DistanceImageIterator.Get();
        if (v_CurrentSize < a_SizeOfMargin)
        {
            v_MaskImageIterator.Set(255);
        }
        else
        {
            v_MaskImageIterator.Set(0);
        }
    }

    return v_PaddedTumourMask;
}

float casEfficacyMeasurements::calculateCoverageRatio(float a_UncoveredVolumeMl, float a_TotalVolumeMl)
{
    float a_CoverageRatio = 1 - (a_UncoveredVolumeMl / a_TotalVolumeMl);
    return a_CoverageRatio;
}


CONST casEfficacyMeasurements::s_ResultsMargins casEfficacyMeasurements::getMarginsBetweenBorders(egItkUC3DImagePtr a_SegmentationVolumeA, egItkUC3DImagePtr a_SegmentationVolumeB) CONST
{
    egItkUC3DImagePtr v_ContourmaskB = casSegmentationEvaluationTools::getItkMaskContour(a_SegmentationVolumeB);
    egItkUC3DImagePtr v_ContourmaskA = casSegmentationEvaluationTools::getItkMaskContour(a_SegmentationVolumeA);

    t_OutputImageTypePtr v_DistaceMap = casSegmentationEvaluationTools::GetSignedMaurerDistanceMap(a_SegmentationVolumeA);
    std::vector<double> v_Distances = casSegmentationEvaluationTools::GetMarginsListBetweenBorders(v_DistaceMap, v_ContourmaskB);
    std::vector<double>::iterator v_It;

    double v_SumOfElements = 0;
    for (v_It = v_Distances.begin(); v_Distances.end() != v_It; v_It++) {
        *v_It = -(*v_It);
        v_SumOfElements += (*v_It);
    }

    s_ResultsMargins v_Result = {};

    if (v_Distances.size() == 0)
    {
        return v_Result;
    }

        std::size_t v_SizeVector = v_Distances.size();
    std::sort(v_Distances.begin(), v_Distances.end());
    if (v_SizeVector % 2 == 0) {
        v_Result.m_Median = (v_Distances[v_SizeVector / 2 - 1] + v_Distances[v_SizeVector / 2]) / 2;
    }
    else {
        v_Result.m_Median = v_Distances[v_SizeVector / 2];
    }

    v_Result.m_Minimal = v_Distances[0];
    v_Result.m_Maximal = v_Distances[v_SizeVector - 1];

    v_Result.m_Mean = v_SumOfElements / v_SizeVector;

    v_Result.m_HistogramBins = calculateHistogramBins(v_Distances);
    v_Result.m_SD = calculateStandartDeviation(v_Distances, v_Result.m_Mean);

    return v_Result;
}

const float casEfficacyMeasurements::calculateStandartDeviation(std::vector<double> &a_Distances, float a_Mean) const
{
    float v_StandardDeviation = 0;
    for (std::vector<double>::iterator v_It = a_Distances.begin(); v_It != a_Distances.end(); v_It++)
    {
        v_StandardDeviation += pow( (*v_It) - a_Mean, 2);
    }

    v_StandardDeviation = sqrt(v_StandardDeviation/ a_Distances.size());
    return v_StandardDeviation;
}

CONST casEfficacyMeasurements::s_histogramBins casEfficacyMeasurements::calculateHistogramBins(std::vector<double> a_SortedDistances) CONST
{
    s_histogramBins v_Bins;

    int v_Cnt = 0;
    int v_Threshold = -10;
    int v_Sum = 0;
    for (std::vector<double>::iterator v_It = a_SortedDistances.begin(); v_It < a_SortedDistances.end(); v_It++) {
        while (((*v_It) >= v_Threshold)) {
            if (v_Threshold <= 10) {
                if (v_Threshold == 10) {
                    v_Bins.m_5_10 = v_Cnt;
                }
                else if (v_Threshold == 5) {
                    v_Bins.m_0_5 = v_Cnt;
                }
                else if (v_Threshold == 0) {
                    v_Bins.m_Neg5_neg0 = v_Cnt;
                }
                else if (v_Threshold == -5) {
                    v_Bins.m_Neg10_neg5 = v_Cnt;
                }
                else if (v_Threshold == -10) {
                    v_Bins.m_ToNeg10 = v_Cnt;
                }
                v_Threshold += 5;
                v_Sum += v_Cnt;
                v_Cnt = 0;
            }
            else {
                v_Threshold = 255;
            }
        }
        v_Cnt++;
    }
    v_Sum += v_Cnt;
    if (v_Threshold > 10) {
        v_Bins.m_10plus = v_Cnt;
    }
    else if (v_Threshold == 10) {
        v_Bins.m_5_10 = v_Cnt;
    }
    else if (v_Threshold == 5) {
        v_Bins.m_0_5 = v_Cnt;
    }
    else if (v_Threshold == 0) {
        v_Bins.m_Neg5_neg0 = v_Cnt;
    }
    else if (v_Threshold == -5) {
        v_Bins.m_Neg10_neg5 = v_Cnt;
    }
    else if (v_Threshold == -10) {
        v_Bins.m_ToNeg10 = v_Cnt;
    }

    v_Bins.m_ToNeg10 = (v_Bins.m_ToNeg10 / v_Sum) * 100;
    v_Bins.m_Neg10_neg5 = (v_Bins.m_Neg10_neg5 / v_Sum) * 100;
    v_Bins.m_Neg5_neg0 = (v_Bins.m_Neg5_neg0 / v_Sum) * 100;
    v_Bins.m_0_5 = (v_Bins.m_0_5 / v_Sum) * 100;
    v_Bins.m_5_10 = (v_Bins.m_5_10 / v_Sum) * 100;
    v_Bins.m_10plus = (v_Bins.m_10plus / v_Sum) * 100;

    return v_Bins;
}

CONST casEfficacyMeasurements::s_VolumesStructure casEfficacyMeasurements::measureSegmentationVolumes(
    const egItkUC3DImagePtr a_TumourSegmentationMask, const egItkUC3DImagePtr a_AblationSegmentationMask) CONST
{
    //images have same sizes within same coordinate system and same spacing
    //returns tumor volume and tumour residual volume in ml, and also their ratio

    s_VolumesStructure v_Results = {};

    itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkTumour(a_TumourSegmentationMask, a_TumourSegmentationMask->GetLargestPossibleRegion());
    itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkAblation(a_AblationSegmentationMask, a_AblationSegmentationMask->GetLargestPossibleRegion());

    v_Results.m_TumourVolumeML = 0;
    v_Results.m_TumourResidualVolumeML = 0;
    v_Results.m_AblationVolumeML = 0;
    v_Results.m_PredictedAblationVolumeML = 0;
    for (v_ItItkTumour.GoToBegin(); !v_ItItkTumour.IsAtEnd(); ++v_ItItkTumour) {
        v_ItItkAblation.SetIndex(v_ItItkTumour.GetIndex());

        if (v_ItItkTumour.Get() > 0) {
            v_Results.m_TumourVolumeML++;

            if (v_ItItkAblation.Get() == 0 && v_ItItkTumour.Get() > 0) {
                v_Results.m_TumourResidualVolumeML++;
            }
        }
    }

    for (v_ItItkAblation.GoToBegin(); !v_ItItkAblation.IsAtEnd(); ++v_ItItkAblation)
    {
        if (v_ItItkAblation.Get() != 0) {
            v_Results.m_AblationVolumeML++;
        }
    }

    float v_VolumeConversion = a_TumourSegmentationMask->GetSpacing()[0] * a_TumourSegmentationMask->GetSpacing()[1] * a_TumourSegmentationMask->GetSpacing()[2] / 1000;

    v_Results.m_TumourVolumeML *= v_VolumeConversion;
    v_Results.m_TumourResidualVolumeML *= v_VolumeConversion;

    v_VolumeConversion = a_AblationSegmentationMask->GetSpacing()[0] * a_AblationSegmentationMask->GetSpacing()[1] * a_AblationSegmentationMask->GetSpacing()[2] / 1000;
    v_Results.m_AblationVolumeML *= v_VolumeConversion;

    return v_Results;
}

CONST casEfficacyMeasurements::s_EfficacyScores * casEfficacyMeasurements::getMeasurements() CONST
{
    return m_Measurement;
}


	void resampleMasksToSameSpacing(egItkUC3DImagePtr &a_SegmentationVolumeA, egItkUC3DImagePtr &a_SegmentationVolumeB)
	{
		if (a_SegmentationVolumeA->GetSpacing() != a_SegmentationVolumeB->GetSpacing())
		{
			ResampleImageFilterType::Pointer resample = ResampleImageFilterType::New();
            resample->SetDefaultPixelValue(255);
			resample->SetInput(a_SegmentationVolumeA);
			resample->SetOutputSpacing(a_SegmentationVolumeB->GetSpacing());
            resample->SetOutputDirection(a_SegmentationVolumeB->GetDirection());
            resample->SetOutputOrigin(a_SegmentationVolumeA->GetOrigin());
			resample->SetTransform(t_TransformType::New());
			resample->SetInterpolator(t_InterpolatorType::New());
            resample->SetSize(a_SegmentationVolumeA->GetLargestPossibleRegion().GetSize());
            resample->Update();

			a_SegmentationVolumeA = resample->GetOutput();
		}
	}
