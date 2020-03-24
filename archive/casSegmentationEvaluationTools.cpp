// --------------------------------
// <copyright file="casSegmentationEvaluationTools.cpp" company="ARTORG">
//     This file contains proprietary code.Copyright (c) 2009 - 2015. All rights reserved
// </copyright>
// <author>Johan Baijot</author>
// <email>johan.baijot@artorg.unibe.ch</email>
// <date>28.11.2016 14:00:00</date>
// ---------------------------------

#include "casSegmentationEvaluationTools.h"
#include "casBrush.h"

#include "Base/egPatientRegistrationData.h"
#include "base/egAppInterface.h"
#include "base/egItkImageUtils.h"

#include "core/geometry/Vector3d.h"
#include "base/casImageConverter.h"

#include <itkImage.h>
#include <itkImageRegionIterator.h>
#include <itkImageRegionConstIteratorWithIndex.h>
#include <itkCastImageFilter.h>
#include <itkExtractImageFilter.h>
#include <itkImageMomentsCalculator.h>
#include <itkSignedDanielssonDistanceMapImageFilter.h>
#include <itkIsoContourDistanceImageFilter.h>
#include <itkSignedMaurerDistanceMapImageFilter.h>
#include <itkConnectedComponentImageFilter.h>
#include <itkPasteImageFilter.h>
#include <itkRescaleIntensityImageFilter.h>
#include <itkBinaryMask3DMeshSource.h>
#include <vtkSmartPointer.h>
#include <itkImageMaskSpatialObject.h>
#include <itkRegionOfInterestImageFilter.h>
#include <itkMultiplyImageFilter.h>
#include <itkResampleImageFilter.h>

#include <iostream>
#include <list>
#include <vector>
#include <numeric>
#include <cmath>

namespace casSegmentationEvaluationTools
{
    typedef itk::Image< float, 3U > t_OutputImageType;
    typedef t_OutputImageType::Pointer t_OutputImageTypePtr;
    typedef itk::ImageMomentsCalculator<egItkUC3DImageType> t_PCAType;
    typedef itk::IsoContourDistanceImageFilter<egItkUC3DImageType, t_OutputImageType> t_GradientType;
    typedef itk::SignedDanielssonDistanceMapImageFilter<egItkUC3DImageType, t_OutputImageType, egItkUC3DImageType> t_SignedDanielssonType;
    typedef itk::SignedDanielssonDistanceMapImageFilter<egItkUC3DImageType, t_OutputImageType> t_SignedDanielssonType;
    typedef itk::SignedMaurerDistanceMapImageFilter<egItkUC3DImageType, t_OutputImageType> t_SignedMaurerType;
    typedef itk::ConnectedComponentImageFilter<egItkUC3DImageType, egItkUC3DImageType> t_LabelerType;
    typedef itk::RescaleIntensityImageFilter<t_OutputImageType, t_OutputImageType > t_RescalerType;
    typedef itk::PasteImageFilter <egItkUC3DImageType, egItkUC3DImageType > PasteImageFilterType;

    typedef itk::ImageMaskSpatialObject< 3 > ImageMaskSpatialObjectType;
    typedef itk::RegionOfInterestImageFilter< egItkUC3DImageType,
        egItkUC3DImageType > FilterTypeROI;
    typedef itk::MultiplyImageFilter< egItkUC3DImageType, egItkUC3DImageType, egItkUC3DImageType > t_ItkMultiplyImageFilter;
    typedef itk::ResampleImageFilter<egItkUC3DImageType, egItkUC3DImageType> ResampleImageFilterType;
    typedef itk::IdentityTransform<double, 3> t_TransformType;
    typedef itk::NearestNeighborInterpolateImageFunction< egItkUC3DImageType, double > t_InterpolatorType;
    typedef itk::BinaryContourImageFilter<egItkUC3DImageType, egItkUC3DImageType> t_BinaryContourImageFilter;

	egItkUC3DImagePtr getItkMaskContour(egItkUC3DImagePtr a_SegmentationMask)
	{
		t_BinaryContourImageFilter::Pointer v_BinaryContourImageFilter = t_BinaryContourImageFilter::New();
		v_BinaryContourImageFilter->SetInput(a_SegmentationMask);
		v_BinaryContourImageFilter->SetBackgroundValue(0);
		v_BinaryContourImageFilter->FullyConnectedOff();
		v_BinaryContourImageFilter->Update();
		return v_BinaryContourImageFilter->GetOutput();
	}

	void pasteIntoCommonSpace(egItkUC3DImagePtr & v_NewBiggerImage, egItkUC3DImagePtr v_OldImg)
	{
		egItkUC3DImageType::PointType v_ItkPixelLocationPointinSpace;
		egItkUC3DImageType::IndexType v_ItkPixelLocationCoordinatesInImage;

		itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkNewImage(v_NewBiggerImage, v_NewBiggerImage->GetLargestPossibleRegion());
		itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkOldImage(v_OldImg, v_OldImg->GetLargestPossibleRegion());

		v_ItItkOldImage.GoToBegin();
		while (!v_ItItkOldImage.IsAtEnd()) {
			v_ItkPixelLocationCoordinatesInImage = v_ItItkOldImage.GetIndex();

			v_OldImg->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
			v_NewBiggerImage->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
			v_ItItkNewImage.SetIndex(v_ItkPixelLocationCoordinatesInImage);

			v_ItItkNewImage.Set(v_ItItkOldImage.Get());

			++v_ItItkOldImage;
		}

	}

	egItkUC3DImagePtr CreateCommonSpace(egItkUC3DImagePtr a_AblationMask, egItkUC3DImagePtr a_TumorMask)
	{
		egItkUC3DImagePtr v_NewImage;
		v_NewImage = egItkUC3DImageType::New();

		egItkUC3DImageType::PointType v_Origin;
		egItkUC3DImageType::PointType v_VectTumor = a_TumorMask->GetOrigin();
		egItkUC3DImageType::PointType v_VectAblation = a_AblationMask->GetOrigin();

		v_Origin[0] = (v_VectTumor.GetElement(0) < v_VectAblation.GetElement(0)) ? v_VectTumor.GetElement(0) : v_VectAblation.GetElement(0);
		v_Origin[1] = (v_VectTumor.GetElement(1) < v_VectAblation.GetElement(1)) ? v_VectTumor.GetElement(1) : v_VectAblation.GetElement(1);
		v_Origin[2] = (v_VectTumor.GetElement(2) < v_VectAblation.GetElement(2)) ? v_VectTumor.GetElement(2) : v_VectAblation.GetElement(2);
		v_NewImage->SetOrigin(v_Origin);

		v_NewImage->SetSpacing(a_AblationMask->GetSpacing());

		egItkUC3DImageType::SizeType v_SizeTumor = a_TumorMask->GetLargestPossibleRegion().GetSize();

		egItkUC3DImageType::IndexType v_TumorIndex;
		v_TumorIndex[0] = v_SizeTumor.GetElement(0);
		v_TumorIndex[1] = v_SizeTumor.GetElement(1);
		v_TumorIndex[2] = v_SizeTumor.GetElement(2);

		a_TumorMask->TransformIndexToPhysicalPoint(v_TumorIndex, v_VectTumor);

		egItkUC3DImageType::SizeType v_SizeAblation = a_AblationMask->GetLargestPossibleRegion().GetSize();

		egItkUC3DImageType::IndexType v_AblationIndex;
		v_AblationIndex[0] = v_SizeAblation.GetElement(0);
		v_AblationIndex[1] = v_SizeAblation.GetElement(1);
		v_AblationIndex[2] = v_SizeAblation.GetElement(2);

		a_AblationMask->TransformIndexToPhysicalPoint(v_AblationIndex, v_VectAblation);

		egItkUC3DImageType::PointType v_End;
		v_End[0] = (v_VectTumor.GetElement(0) > v_VectAblation.GetElement(0)) ? v_VectTumor.GetElement(0) : v_VectAblation.GetElement(0);
		v_End[1] = (v_VectTumor.GetElement(1) > v_VectAblation.GetElement(1)) ? v_VectTumor.GetElement(1) : v_VectAblation.GetElement(1);
		v_End[2] = (v_VectTumor.GetElement(2) > v_VectAblation.GetElement(2)) ? v_VectTumor.GetElement(2) : v_VectAblation.GetElement(2);

		egItkUC3DImageType::IndexType v_EndIndex;
		v_NewImage->TransformPhysicalPointToIndex(v_End, v_EndIndex);

		egItkUC3DImageType::SizeType v_NewSize;
		v_NewSize[0] = v_EndIndex.GetElement(0);
		v_NewSize[1] = v_EndIndex.GetElement(1);
		v_NewSize[2] = v_EndIndex.GetElement(2);

		egItkUC3DImageType::IndexType v_IndexAblation = a_AblationMask->GetLargestPossibleRegion().GetIndex();
		egItkUC3DImageType::IndexType v_IndexTumor = a_TumorMask->GetLargestPossibleRegion().GetIndex();
		egItkUC3DImageType::IndexType v_StartIndex;
		v_StartIndex[0] = (v_IndexTumor.GetElement(0) < v_IndexAblation.GetElement(0)) ? v_IndexTumor.GetElement(0) : v_IndexAblation.GetElement(0);
		v_StartIndex[1] = (v_IndexTumor.GetElement(1) < v_IndexAblation.GetElement(1)) ? v_IndexTumor.GetElement(1) : v_IndexAblation.GetElement(1);
		v_StartIndex[2] = (v_IndexTumor.GetElement(2) < v_IndexAblation.GetElement(2)) ? v_IndexTumor.GetElement(2) : v_IndexAblation.GetElement(2);

		egItkUC3DImageType::IndexType v_ZeroVector;
		v_ZeroVector[0] = 0;
		v_ZeroVector[1] = 0;
		v_ZeroVector[2] = 0;

		if (v_StartIndex != v_ZeroVector)
		{
			v_NewImage->TransformIndexToPhysicalPoint(v_StartIndex, v_Origin);
			v_NewImage->SetOrigin(v_Origin);
			v_StartIndex = v_ZeroVector;
		}

		egItkUC3DImageType::RegionType v_NewRegion;
		v_NewRegion.SetSize(v_NewSize);
		v_NewRegion.SetIndex(v_StartIndex);
		v_NewImage->SetRegions(v_NewRegion);

		v_NewImage->Allocate();

		itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkNewImage(v_NewImage, v_NewImage->GetLargestPossibleRegion());

		v_ItItkNewImage.GoToBegin();
		while (!v_ItItkNewImage.IsAtEnd()) {
			v_ItItkNewImage.Set(0);
			++v_ItItkNewImage;
		}

		return v_NewImage;
	}

	void findCommonBoundingBox(egItkUC3DImagePtr &v_SegmentationVolumeA, egItkUC3DImagePtr &v_SegmentationVolumeB)
	{
		egItkUC3DImagePtr v_NewSegmentationVolumeB = casSegmentationEvaluationTools::CreateCommonSpace(v_SegmentationVolumeA, v_SegmentationVolumeB);
		egItkUC3DImagePtr v_NewSegmentationVolumeA = casSegmentationEvaluationTools::CreateCommonSpace(v_SegmentationVolumeA, v_SegmentationVolumeB);

		casSegmentationEvaluationTools::pasteIntoCommonSpace(v_NewSegmentationVolumeB, v_SegmentationVolumeB);
		casSegmentationEvaluationTools::pasteIntoCommonSpace(v_NewSegmentationVolumeA, v_SegmentationVolumeA);

		v_SegmentationVolumeA = v_NewSegmentationVolumeA;
		v_SegmentationVolumeB = v_NewSegmentationVolumeB;
	}

	void getImgROI(egItkUC3DImagePtr & a_SegmVolume)
	{
		ImageMaskSpatialObjectType::Pointer
			imageMaskSpatialObject = ImageMaskSpatialObjectType::New();
		imageMaskSpatialObject->SetImage(a_SegmVolume);
		egItkUC3DImageType::RegionType v_SegmVolumeReg = imageMaskSpatialObject->GetAxisAlignedBoundingBoxRegion();

		FilterTypeROI::Pointer v_FilterROI = FilterTypeROI::New();
		v_FilterROI->SetRegionOfInterest(v_SegmVolumeReg);
		v_FilterROI->SetInput(a_SegmVolume);
		v_FilterROI->Update();

		a_SegmVolume = (v_FilterROI->GetOutput());
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkIm(a_SegmVolume, a_SegmVolume->GetLargestPossibleRegion());

        while (!v_ItItkIm.IsAtEnd()) {
            if (v_ItItkIm.Get() != casBrush::BRUSH_BACKGROUND) {
                v_ItItkIm.Set(casBrush::BRUSH_FOREGROUND);
            }
            ++v_ItItkIm;
        }

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

    const double GetSegmentationVolume(egItkUC3DImagePtr a_SegmentationVolume){
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkIm(a_SegmentationVolume, a_SegmentationVolume->GetLargestPossibleRegion());

        int v_Volume = 0;
        v_ItItkIm.GoToBegin();
        unsigned char v_PixelValue;

        while (!v_ItItkIm.IsAtEnd()){
            v_PixelValue = v_ItItkIm.Get();
            if (v_PixelValue > 254){
                ++v_Volume;
            }
            ++v_ItItkIm;
        }
        v_Volume = v_Volume*a_SegmentationVolume->GetSpacing()[0] * a_SegmentationVolume->GetSpacing()[1] * a_SegmentationVolume->GetSpacing()[2];
        return v_Volume;
    }

    s_ResultsLargestDiameter GetLargestDiameterIn2D(egItkUC2DImagePtr a_SegmentationVolume){
        s_ResultsLargestDiameter v_Result;
        itk::ImageRegionIteratorWithIndex<egItkUC2DImageType> v_ItItkIm(a_SegmentationVolume, a_SegmentationVolume->GetLargestPossibleRegion());
        const itk::Vector<double, 2U> v_Spacing = a_SegmentationVolume->GetSpacing();
        std::list<Vector2d> v_Border;
        Vector2d v_Location;
        v_ItItkIm.GoToBegin();
        unsigned char v_PixelValue;
        while (!v_ItItkIm.IsAtEnd()){
            v_PixelValue = v_ItItkIm.Get();
            if (v_PixelValue > 254){
                v_Location[0] = v_ItItkIm.GetIndex()[0];
                v_Location[1] = v_ItItkIm.GetIndex()[1];
                v_Border.push_front(v_Location);
            }
            ++v_ItItkIm;
        }
        double v_MaxDistance = 0;
        v_Result.m_Distance = 0;
        for (std::list<Vector2d>::iterator v_Itt1 = v_Border.begin(); v_Itt1 != v_Border.end(); ++v_Itt1){
            Vector2d v_PointOfBorderOne = *v_Itt1;
            for (std::list<Vector2d>::iterator v_Itt2 = v_Border.begin(); v_Itt2 != v_Border.end(); ++v_Itt2){
                Vector2d v_PointOfBorderTwo = *v_Itt2;
                double v_Distance = std::hypot(((v_PointOfBorderOne[0] - v_PointOfBorderTwo[0] + 1)*v_Spacing[0]), ((v_PointOfBorderOne[1] - v_PointOfBorderTwo[1] + 1)* v_Spacing[1]));
                if (v_Distance > v_MaxDistance){
                    v_MaxDistance = v_Distance;
                    v_Result.m_PointA[0] = v_PointOfBorderOne[0];
                    v_Result.m_PointA[1] = v_PointOfBorderOne[1];
                    v_Result.m_PointB[0] = v_PointOfBorderTwo[0];
                    v_Result.m_PointB[1] = v_PointOfBorderTwo[1];
                }
            }
        }
        v_Result.m_Distance = v_MaxDistance;
        return v_Result;
    }

    const egItkUC3DImagePtr GetContourOfSegmentation(egItkUC3DImagePtr a_SegmentationVolume){
        egItkUC3DImagePtr v_ModelContourMask = egItkUC3DImageType::New();
        egItkUC3DImageType::RegionType v_ItkRegion;
        v_ItkRegion.SetSize(a_SegmentationVolume->GetLargestPossibleRegion().GetSize());
        v_ItkRegion.SetIndex(a_SegmentationVolume->GetLargestPossibleRegion().GetIndex());

        v_ModelContourMask->SetRegions(v_ItkRegion);
        v_ModelContourMask->SetDirection(a_SegmentationVolume->GetDirection());
        v_ModelContourMask->SetOrigin(a_SegmentationVolume->GetOrigin());
        v_ModelContourMask->SetSpacing(a_SegmentationVolume->GetSpacing());
        v_ModelContourMask->Allocate();

        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_IteratorForItkIm(v_ModelContourMask, v_ModelContourMask->GetLargestPossibleRegion());
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkIm(a_SegmentationVolume, a_SegmentationVolume->GetLargestPossibleRegion());


        int v_XMax = a_SegmentationVolume->GetLargestPossibleRegion().GetSize()[0];
        int v_YMax = a_SegmentationVolume->GetLargestPossibleRegion().GetSize()[1];
        int v_ZMax = a_SegmentationVolume->GetLargestPossibleRegion().GetSize()[2];

        unsigned char v_PixelValue; //copy the image
        v_PixelValue = 0;
        v_IteratorForItkIm.GoToBegin();
        v_ItItkIm.GoToBegin();

        while (!v_ItItkIm.IsAtEnd()){
            v_PixelValue = v_ItItkIm.Get();;
            v_IteratorForItkIm.Set(v_PixelValue);
            ++v_IteratorForItkIm;
            ++v_ItItkIm;
        }

        v_ItItkIm.GoToBegin();
        unsigned char v_PixelValueFront;
        unsigned char v_PixelValueBack;
        unsigned char v_PixelValueRight;
        unsigned char v_PixelValueLeft;
        unsigned char v_PixelValueUp;
        unsigned char v_PixelValueDown;
        egItkUC3DImageType::PointType v_Index2;
        itk::ImageBase<3U>::IndexType v_Index;
        itk::ImageBase<3U>::IndexType v_Cornerindex = a_SegmentationVolume->GetLargestPossibleRegion().GetIndex();
        for (int x = v_Cornerindex[0] + 1; x < v_Cornerindex[0] + v_XMax - 1; x++){
            for (int y = v_Cornerindex[1] + 1; y < v_Cornerindex[1] + v_YMax - 1; y++){
                for (int z = v_Cornerindex[2] + 1; z <v_Cornerindex[2] + v_ZMax - 1; z++){

                    v_Index[0] = x;
                    v_Index[1] = y;
                    v_Index[2] = z;
                    v_PixelValue = a_SegmentationVolume->GetPixel(v_Index);

                    if (v_PixelValue > 254)
                    {
                        v_ModelContourMask->SetPixel(v_Index, v_PixelValue);

                        v_Index[0] = x + 1;
                        //v_Index[1] = y;
                        //v_Index[2] = z;
                        v_PixelValueFront = a_SegmentationVolume->GetPixel(v_Index);

                        v_Index[0] = x - 1;
                        //v_Index[1] = y;
                        //v_Index[2] = z;
                        v_PixelValueBack = a_SegmentationVolume->GetPixel(v_Index);

                        v_Index[0] = x;
                        v_Index[1] = y + 1;
                        //v_Index[2] = z;
                        v_PixelValueRight = a_SegmentationVolume->GetPixel(v_Index);

                        //v_Index[0] = x;
                        v_Index[1] = y - 1;
                        //v_Index[2] = z;
                        v_PixelValueLeft = a_SegmentationVolume->GetPixel(v_Index);

                        //v_Index[0] = x;
                        v_Index[1] = y;
                        v_Index[2] = z + 1;
                        v_PixelValueUp = a_SegmentationVolume->GetPixel(v_Index);

                        //v_Index[0] = x;
                        //v_Index[1] = y;
                        v_Index[2] = z - 1;
                        v_PixelValueDown = a_SegmentationVolume->GetPixel(v_Index);

                        if ((v_PixelValueFront > 254) && (v_PixelValueBack > 254) && (v_PixelValueRight > 254) && (v_PixelValueLeft > 254) && (v_PixelValueUp > 254) && (v_PixelValueDown > 254))
                        {
                            //v_Index[0] = x;
                            //v_Index[1] = y;
                            v_Index[2] = z;
                            v_ModelContourMask->SetPixel(v_Index, 0);
                        }
                    }
                }
            }
        }

        return v_ModelContourMask;
    }

    s_ResultsLargestDiameter GetLargestDiameterInOneAxisInAxialSlice(egItkUC3DImagePtr a_SegmentationVolume){
        //casCommandsPersistence::Write3DItkImageToMevisDicomTiff(a_SegmentationVolume, "C:\\Users\\Johan\\Documents", "mask.tif");
        s_ResultsLargestDiameter v_Result;
        v_Result.m_Distance = 0;
        typedef itk::ExtractImageFilter< egItkUC3DImageType, egItkUC2DImageType > FilterType;
        FilterType::Pointer v_Filter = FilterType::New();
        v_Filter->SetDirectionCollapseToIdentity();
        egItkUC3DImageType::IndexType start = a_SegmentationVolume->GetLargestPossibleRegion().GetIndex();
        egItkUC3DImageType::RegionType desiredRegion;
        v_Filter->SetInput(a_SegmentationVolume);
        egItkUC2DImagePtr v_Slice;
        s_ResultsLargestDiameter v_DiameterForThisSlice;
        double v_Largestdiameter = 0;

        //Slices along the first axis
        egItkUC3DImageType::SizeType size = a_SegmentationVolume->GetLargestPossibleRegion().GetSize();
        size[2] = 0;
        int v_ZstartPoint = start[2];
        desiredRegion.SetSize(size);
        for (int z = 0; z < a_SegmentationVolume->GetLargestPossibleRegion().GetSize()[2]; z++){
            start[2] = v_ZstartPoint + z;
            desiredRegion.SetIndex(start);
            v_Filter->SetExtractionRegion(desiredRegion);
            v_Filter->Update();
            v_Slice = v_Filter->GetOutput();
            itk::Vector<double, 3U> v_SpacingOrigin = a_SegmentationVolume->GetSpacing();
            itk::Vector<double, 2U> v_SpacingSlice;
            v_SpacingSlice[0] = v_SpacingOrigin[0];
            v_SpacingSlice[1] = v_SpacingOrigin[1];
            v_Slice->SetSpacing(v_SpacingSlice);
            v_DiameterForThisSlice = GetLargestDiameterIn2D(v_Slice); //GetLargestdiameterIn3D(v_Slice);
            if (v_DiameterForThisSlice.m_Distance > v_Largestdiameter){
                v_Largestdiameter = v_DiameterForThisSlice.m_Distance;
                v_Result = v_DiameterForThisSlice;
                v_Result.m_PointA[2] = z;
                v_Result.m_PointB[2] = z;
            }
        }

        egItkUC3DImageType::IndexType v_ItkPixelLocationCoordinatesInImage;
        egItkUC3DImageType::PointType v_ItkPixelLocationPointinPhysicalSpace;
        v_ItkPixelLocationCoordinatesInImage[0] = v_Result.m_PointA[0];
        v_ItkPixelLocationCoordinatesInImage[1] = v_Result.m_PointA[1];
        v_ItkPixelLocationCoordinatesInImage[2] = v_Result.m_PointA[2];
        a_SegmentationVolume->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinPhysicalSpace);
        v_Result.m_PointA[0] = v_ItkPixelLocationPointinPhysicalSpace[0];
        v_Result.m_PointA[1] = v_ItkPixelLocationPointinPhysicalSpace[1];
        v_Result.m_PointA[2] = v_ItkPixelLocationPointinPhysicalSpace[2];
        v_ItkPixelLocationCoordinatesInImage[0] = v_Result.m_PointB[0];
        v_ItkPixelLocationCoordinatesInImage[1] = v_Result.m_PointB[1];
        v_ItkPixelLocationCoordinatesInImage[2] = v_Result.m_PointB[2];
        a_SegmentationVolume->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinPhysicalSpace);
        v_Result.m_PointB[0] = v_ItkPixelLocationPointinPhysicalSpace[0];
        v_Result.m_PointB[1] = v_ItkPixelLocationPointinPhysicalSpace[1];
        v_Result.m_PointB[2] = v_ItkPixelLocationPointinPhysicalSpace[2];
        v_Result.m_Distance = v_Result.m_Distance;

        /* Intresting link for other stuff (PCA):
          http://itk-users.7.n7.nabble.com/Measuring-tumor-diameter-td19512.html */
        return v_Result;
    }

    s_ResultsLargestDiameter GetLargestDiameterIn3D(egItkUC3DImagePtr a_SegmentationVolume){
        s_ResultsLargestDiameter v_Result;
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkIm(a_SegmentationVolume, a_SegmentationVolume->GetLargestPossibleRegion());
        const itk::Vector<double, 3U> v_Spacing = a_SegmentationVolume->GetSpacing();
        std::list<Vector3d> v_Border;
        Vector3d v_Location;
        v_ItItkIm.GoToBegin();
        unsigned char v_PixelValue;

        while (!v_ItItkIm.IsAtEnd()){
            v_PixelValue = v_ItItkIm.Get();
            if (v_PixelValue > 254)
            {
                v_Location[0] = v_ItItkIm.GetIndex()[0];
                v_Location[1] = v_ItItkIm.GetIndex()[1];
                v_Location[2] = v_ItItkIm.GetIndex()[2];
                v_Border.push_front(v_Location);
            }
            ++v_ItItkIm;
        }

        double v_MaxDistance = 0;
        for (std::list<Vector3d>::iterator v_Itt1 = v_Border.begin(); v_Itt1 != v_Border.end(); ++v_Itt1){
            Vector3d v_PointOfBorderOne = *v_Itt1;
            for (std::list<Vector3d>::iterator v_Itt2 = v_Border.begin(); v_Itt2 != v_Border.end(); ++v_Itt2){
                Vector3d v_PointOfBorderTwo = *v_Itt2;
                double v_Distance = ((v_PointOfBorderOne[0] - v_PointOfBorderTwo[0] + 1)*v_Spacing[0])*((v_PointOfBorderOne[0] - v_PointOfBorderTwo[0] + 1)*v_Spacing[0]) + ((v_PointOfBorderOne[1] - v_PointOfBorderTwo[1] + 1)*v_Spacing[1])*((v_PointOfBorderOne[1] - v_PointOfBorderTwo[1] + 1)*v_Spacing[1]) + ((v_PointOfBorderOne[2] - v_PointOfBorderTwo[2] + 1)*v_Spacing[2])*((v_PointOfBorderOne[2] - v_PointOfBorderTwo[2] + 1)*v_Spacing[2]);
                if (v_Distance > v_MaxDistance)
                {
                    v_MaxDistance = v_Distance;
                    v_Result.m_PointA = v_PointOfBorderOne;
                    v_Result.m_PointB = v_PointOfBorderTwo;
                }
            }
        }
        egItkUC3DImageType::IndexType v_ItkPixelLocationCoordinatesInImage;
        egItkUC3DImageType::PointType v_ItkPixelLocationPointinPhysicalSpace;
        v_ItkPixelLocationCoordinatesInImage[0] = v_Result.m_PointA[0];
        v_ItkPixelLocationCoordinatesInImage[1] = v_Result.m_PointA[1];
        v_ItkPixelLocationCoordinatesInImage[2] = v_Result.m_PointA[2];
        a_SegmentationVolume->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinPhysicalSpace);
        v_Result.m_PointA[0] = v_ItkPixelLocationPointinPhysicalSpace[0];
        v_Result.m_PointA[1] = v_ItkPixelLocationPointinPhysicalSpace[1];
        v_Result.m_PointA[2] = v_ItkPixelLocationPointinPhysicalSpace[2];
        v_ItkPixelLocationCoordinatesInImage[0] = v_Result.m_PointB[0];
        v_ItkPixelLocationCoordinatesInImage[1] = v_Result.m_PointB[1];
        v_ItkPixelLocationCoordinatesInImage[2] = v_Result.m_PointB[2];
        a_SegmentationVolume->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinPhysicalSpace);
        v_Result.m_PointB[0] = v_ItkPixelLocationPointinPhysicalSpace[0];
        v_Result.m_PointB[1] = v_ItkPixelLocationPointinPhysicalSpace[1];
        v_Result.m_PointB[2] = v_ItkPixelLocationPointinPhysicalSpace[2];
        v_Result.m_Distance = sqrt(v_MaxDistance);
        return v_Result;
    }

    const double GetDiceIndex(egItkUC3DImagePtr a_SegmentationVolumeA, egItkUC3DImagePtr a_SegmentationVolumeB){
        //For this function to work correctly the image B should fit inside image A
        // Asumed voxel size is the same between the two images!!!
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImA(a_SegmentationVolumeA, a_SegmentationVolumeA->GetLargestPossibleRegion());
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImB(a_SegmentationVolumeB, a_SegmentationVolumeB->GetLargestPossibleRegion());
        double v_VolumeA = 0;
        double v_VolumeB = 0;
        double v_VolumeAB = 0;
        v_ItItkImB.GoToBegin();
        unsigned char v_PixelValueA;
        unsigned char v_PixelValueB;
        egItkUC3DImageType::IndexType v_ItkPixelLocationCoordinatesInImage;
        egItkUC3DImageType::PointType v_ItkPixelLocationPointinSpace;

        while (!v_ItItkImB.IsAtEnd()){
            v_PixelValueB = v_ItItkImB.Get();
            a_SegmentationVolumeB->TransformIndexToPhysicalPoint(v_ItItkImB.GetIndex(), v_ItkPixelLocationPointinSpace);
            a_SegmentationVolumeA->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
            v_ItItkImA.SetIndex(v_ItkPixelLocationCoordinatesInImage);
            v_PixelValueA = v_ItItkImA.Get();
            if (v_PixelValueA > 254){
                ++v_VolumeA;
            }
            if (v_PixelValueB > 254){
                ++v_VolumeB;
            }
            if ((v_PixelValueA > 254) && (v_PixelValueB > 254)){
                ++v_VolumeAB;
            }
            ++v_ItItkImB;
        }
        double v_OversizeCheck = GetSegmentationVolume(a_SegmentationVolumeA);
        v_OversizeCheck = v_OversizeCheck*a_SegmentationVolumeA->GetSpacing()[0] * a_SegmentationVolumeA->GetSpacing()[1] * a_SegmentationVolumeA->GetSpacing()[2] / a_SegmentationVolumeB->GetSpacing()[0] / a_SegmentationVolumeB->GetSpacing()[1] / a_SegmentationVolumeB->GetSpacing()[2];
        if (v_VolumeA < v_OversizeCheck){
            v_VolumeA = v_OversizeCheck;
        }

        double v_DiceIndex = (2 * v_VolumeAB) / (v_VolumeA + v_VolumeB);
        return v_DiceIndex;
    }

    void GetInsideOutsideimage(egItkUC3DImagePtr a_SegmentationVolumeA, egItkUC3DImagePtr a_SegmentationVolumeB, egItkUC3DImagePtr a_ResultSegmentationVolumeBInside, egItkUC3DImagePtr a_ResultSegmentationVolumeBOutside){
        //SegmentationA should be bigger as B, we split B up in two parts the part that is inside and the part that is outside of segmentation A
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImA(a_SegmentationVolumeA, a_SegmentationVolumeA->GetLargestPossibleRegion());
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImB(a_SegmentationVolumeB, a_SegmentationVolumeB->GetLargestPossibleRegion());
        egItkUC3DImageType::RegionType v_ItkRegion;
        v_ItkRegion.SetSize(a_SegmentationVolumeB->GetLargestPossibleRegion().GetSize());
        v_ItkRegion.SetIndex(a_SegmentationVolumeB->GetLargestPossibleRegion().GetIndex());
        a_ResultSegmentationVolumeBInside->SetRegions(v_ItkRegion);
        a_ResultSegmentationVolumeBInside->SetDirection(a_SegmentationVolumeB->GetDirection());
        a_ResultSegmentationVolumeBInside->SetOrigin(a_SegmentationVolumeB->GetOrigin());
        a_ResultSegmentationVolumeBInside->SetSpacing(a_SegmentationVolumeB->GetSpacing());
        a_ResultSegmentationVolumeBInside->Allocate();
        a_ResultSegmentationVolumeBOutside->SetRegions(v_ItkRegion);
        a_ResultSegmentationVolumeBOutside->SetDirection(a_SegmentationVolumeB->GetDirection());
        a_ResultSegmentationVolumeBOutside->SetOrigin(a_SegmentationVolumeB->GetOrigin());
        a_ResultSegmentationVolumeBOutside->SetSpacing(a_SegmentationVolumeB->GetSpacing());
        a_ResultSegmentationVolumeBOutside->Allocate();
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImBIn(a_ResultSegmentationVolumeBInside, a_ResultSegmentationVolumeBInside->GetLargestPossibleRegion());
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImBOut(a_ResultSegmentationVolumeBOutside, a_ResultSegmentationVolumeBOutside->GetLargestPossibleRegion());

        v_ItItkImA.GoToBegin();
        v_ItItkImB.GoToBegin();
        v_ItItkImBIn.GoToBegin();
        v_ItItkImBOut.GoToBegin();
        unsigned char v_PixelValueA;
        unsigned char v_PixelValueB;
        unsigned char v_PixelValue;
        v_PixelValue = 0;
        egItkUC3DImageType::IndexType v_ItkPixelLocationCoordinatesInImage;
        egItkUC3DImageType::PointType v_ItkPixelLocationPointinSpace;

        while (!v_ItItkImB.IsAtEnd()){
            v_PixelValueB = v_ItItkImB.Get();
            if (v_PixelValueB > 254){
                a_SegmentationVolumeB->TransformIndexToPhysicalPoint(v_ItItkImB.GetIndex(), v_ItkPixelLocationPointinSpace);
                a_SegmentationVolumeA->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
                v_ItItkImA.SetIndex(v_ItkPixelLocationCoordinatesInImage);
                v_PixelValueA = v_ItItkImA.Get();
                if (v_PixelValueA > 254){
                    v_ItItkImBIn.Set(v_PixelValueB);
                    v_ItItkImBOut.Set(v_PixelValue);
                }
                else{
                    v_ItItkImBIn.Set(v_PixelValue);
                    v_ItItkImBOut.Set(v_PixelValueB);
                }
            }
            else{
                v_ItItkImBIn.Set(v_PixelValue);
                v_ItItkImBOut.Set(v_PixelValue);
            }
            ++v_ItItkImB;
            ++v_ItItkImBIn;
            ++v_ItItkImBOut;
        }
    }

    const itk::Vector<double, 3U> GetPCAFromImage(egItkUC3DImagePtr a_SegmentationVolume){
        //https://github.com/InsightSoftwareConsortium/ITK/blob/master/Modules/Filtering/ImageStatistics/include/itkImageMomentsCalculator.h
        t_PCAType::Pointer v_PCA = t_PCAType::New();
        v_PCA->SetImage(a_SegmentationVolume);
        v_PCA->Compute();

        //double v_TotalMass = v_PCA->GetTotalMass();
        //itk::Vector<double, 3U> v_CenterOfGravity = v_PCA->GetCenterOfGravity();
        //itk::Vector<double, 3U> v_PrincipalMoments = v_PCA->GetPrincipalMoments();
        itk::Matrix<double, 3U, 3U> v_PrincipalAxes = v_PCA->GetPrincipalAxes();
        //itk::Vector<double, 3U> v_FirstMoments = v_PCA->GetFirstMoments();
        return v_PrincipalAxes[2];
    }

    const t_OutputImageTypePtr GetSignedDanielssonDistancemap(egItkUC3DImagePtr a_SegmentationVolume){
        t_SignedDanielssonType::Pointer v_DistanceMapFilter = t_SignedDanielssonType::New();
        v_DistanceMapFilter->SetInput(a_SegmentationVolume);
        v_DistanceMapFilter->Update();
        return v_DistanceMapFilter->GetOutput();
    }

    const t_OutputImageTypePtr GetGradientmap(egItkUC3DImagePtr a_SegmentationVolume){
        t_GradientType::Pointer v_GradientMapFilter = t_GradientType::New();
        v_GradientMapFilter->SetInput(a_SegmentationVolume);
        v_GradientMapFilter->Update();
        return v_GradientMapFilter->GetOutput();
    }

    const t_OutputImageTypePtr GetSignedMaurerDistanceMap(egItkUC3DImagePtr a_SegmentationVolume){
        t_SignedMaurerType::Pointer v_DistanceMapFilter = t_SignedMaurerType::New();
        v_DistanceMapFilter->SetInput(a_SegmentationVolume);
        v_DistanceMapFilter->Update();
        return v_DistanceMapFilter->GetOutput();
    }

    std::vector<double> GetMarginsListBetweenBorders(t_OutputImageTypePtr a_Distancemap, egItkUC3DImagePtr a_Contour){

        itk::ImageRegionIteratorWithIndex<t_OutputImageType> v_ItItkImDistance(a_Distancemap, a_Distancemap->GetLargestPossibleRegion());
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImB(a_Contour, a_Contour->GetLargestPossibleRegion());
        v_ItItkImDistance.GoToBegin();
        v_ItItkImB.GoToBegin();
        egItkUC3DImageType::PointType v_PhysicalIndex;
        egItkUC3DImageType::IndexType v_IndexOnDistanceMap;
        unsigned char v_PixelValueB;
        std::vector<double> v_Distances;

        while (!v_ItItkImB.IsAtEnd()){
            v_PixelValueB = v_ItItkImB.Get();
            if (v_PixelValueB > 254){
                a_Contour->TransformIndexToPhysicalPoint(v_ItItkImB.GetIndex(), v_PhysicalIndex);
                a_Distancemap->TransformPhysicalPointToIndex(v_PhysicalIndex, v_IndexOnDistanceMap);
                v_ItItkImDistance.SetIndex(v_IndexOnDistanceMap);
                v_Distances.push_back(v_ItItkImDistance.Get());
            }

            ++v_ItItkImB;
        }
        return v_Distances;
    }

    s_ResultsMargins GetMarginsBetweenBorders(egItkUC3DImagePtr a_SegmentationVolumeA, egItkUC3DImagePtr a_SegmentationVolumeB){
        egItkUC3DImagePtr v_ContourmaskB = casSegmentationEvaluationTools::GetContourOfSegmentation(a_SegmentationVolumeB);
        egItkUC3DImageType::Pointer v_VolumeAResized = casSegmentationEvaluationTools::FindBoundingBoxForTwoImages(a_SegmentationVolumeA, a_SegmentationVolumeB);
        t_OutputImageTypePtr v_DistaceMap = GetSignedMaurerDistanceMap(v_VolumeAResized);
        std::vector<double> v_Distances = GetMarginsListBetweenBorders(v_DistaceMap, v_ContourmaskB);

        s_ResultsMargins v_Result;

        std::size_t v_SizeVector = v_Distances.size();
        std::sort(v_Distances.begin(), v_Distances.end());
        if (v_SizeVector % 2 == 0){
            v_Result.m_median = (v_Distances[v_SizeVector / 2 - 1] + v_Distances[v_SizeVector / 2]) / 2;
        }
        else{
            v_Result.m_median = v_Distances[v_SizeVector / 2];
        }
        v_Result.m_minimal = v_Distances[0];
        v_Result.m_maximal = v_Distances[v_SizeVector - 1];
        v_Result.m_mean = std::accumulate(v_Distances.begin(), v_Distances.end(), 0.0) / v_SizeVector;

        return v_Result;
    }

    const egItkUC3DImageType::Pointer TransformImageAccordingToRegistration(egItkUC3DImageType::Pointer a_SegmentationVolume, TransMatrix3d a_TransformationMatrix){

        egItkUC3DImageType::Pointer v_ImageInNewReferenceCoordinates = egItkUC3DImageType::New();
        egItkUC3DImageType::RegionType v_ItkRegion;
        Matrix3x3 v_Rotation = a_TransformationMatrix.getRotation();
        Vector3d v_Translation = a_TransformationMatrix.getTranslation();
        egItkUC3DImageType::DirectionType v_OldDirection = a_SegmentationVolume->GetDirection();
        egItkUC3DImageType::DirectionType v_NewDirection;
        egItkUC3DImageType::PointType v_Origin;

        for (int row = 0; row != 3; ++row)
        {
            for (int col = 0; col != 3; ++col)
            {
                double sum = 0;
                for (int element = 0; element != 3; ++element)
                {
                    sum += v_OldDirection[row][element] * v_Rotation[element][col];
                }
                v_NewDirection[row][col] = sum;
            }
        }

        v_Origin[0] = a_SegmentationVolume->GetOrigin()[0] * v_Rotation[0][0] + a_SegmentationVolume->GetOrigin()[1] * v_Rotation[0][1] + a_SegmentationVolume->GetOrigin()[2] * v_Rotation[0][2] + v_Translation[0];
        v_Origin[1] = a_SegmentationVolume->GetOrigin()[0] * v_Rotation[1][0] + a_SegmentationVolume->GetOrigin()[1] * v_Rotation[1][1] + a_SegmentationVolume->GetOrigin()[2] * v_Rotation[1][2] + v_Translation[1];
        v_Origin[2] = a_SegmentationVolume->GetOrigin()[0] * v_Rotation[2][0] + a_SegmentationVolume->GetOrigin()[1] * v_Rotation[2][1] + a_SegmentationVolume->GetOrigin()[2] * v_Rotation[2][2] + v_Translation[2];

        v_ItkRegion.SetSize(a_SegmentationVolume->GetLargestPossibleRegion().GetSize());
        v_ItkRegion.SetIndex(a_SegmentationVolume->GetLargestPossibleRegion().GetIndex());
        v_ImageInNewReferenceCoordinates->SetRegions(v_ItkRegion);
        v_ImageInNewReferenceCoordinates->SetOrigin(v_Origin);
        v_ImageInNewReferenceCoordinates->SetDirection(v_NewDirection);
        v_ImageInNewReferenceCoordinates->SetSpacing(a_SegmentationVolume->GetSpacing());
        v_ImageInNewReferenceCoordinates->Allocate();
        //v_ImageInNewReferenceCoordinates = a_SegmentationVolume->Clone();
        //v_ImageInNewReferenceCoordinates = a_SegmentationVolume->CreateAnother();

        //ugly way of fixing it (there should be a better way but I don't know how, not sure if the paste filter will work)
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImA(a_SegmentationVolume, a_SegmentationVolume->GetLargestPossibleRegion());
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_ItItkImB(v_ImageInNewReferenceCoordinates, v_ImageInNewReferenceCoordinates->GetLargestPossibleRegion());
        v_ItItkImA.GoToBegin();
        v_ItItkImB.GoToBegin();
        unsigned char v_PixelValue;
        while (!v_ItItkImA.IsAtEnd()){
            v_PixelValue = v_ItItkImA.Get();
            v_ItItkImB.Set(v_PixelValue);
            ++v_ItItkImA;
            ++v_ItItkImB;
        }

        return v_ImageInNewReferenceCoordinates;
    }

const egItkUC3DImageType::Pointer FindBoundingBoxForTwoImages(egItkUC3DImageType::Pointer a_BaseImageToEnlarge, egItkUC3DImageType::Pointer a_ImageThatHasToFitInTheEnlargedImage){
        std::vector<int> v_ListOfXCoordinates;
        std::vector<int> v_ListOfYCoordinates;
        std::vector<int> v_ListOfZCoordinates;

        //Add the 8 corners of the first image to the list.
        egItkUC3DImageType::SizeType v_ItkSizeBase = a_BaseImageToEnlarge->GetLargestPossibleRegion().GetSize();
        v_ListOfXCoordinates.push_back(a_BaseImageToEnlarge->GetLargestPossibleRegion().GetIndex()[0]);
        v_ListOfXCoordinates.push_back(a_BaseImageToEnlarge->GetLargestPossibleRegion().GetIndex()[0] + v_ItkSizeBase[0] - 1);
        v_ListOfYCoordinates.push_back(a_BaseImageToEnlarge->GetLargestPossibleRegion().GetIndex()[1]);
        v_ListOfYCoordinates.push_back(a_BaseImageToEnlarge->GetLargestPossibleRegion().GetIndex()[1] + v_ItkSizeBase[1] - 1);
        v_ListOfZCoordinates.push_back(a_BaseImageToEnlarge->GetLargestPossibleRegion().GetIndex()[2]);
        v_ListOfZCoordinates.push_back(a_BaseImageToEnlarge->GetLargestPossibleRegion().GetIndex()[2] + v_ItkSizeBase[2] - 1);

        egItkUC3DImageType::IndexType v_ItkPixelLocationCoordinatesInImage;
        egItkUC3DImageType::IndexType v_Origin;
        egItkUC3DImageType::PointType v_ItkPixelLocationPointinSpace;

        //Add the 8 corners of the other image to the list.
        egItkUC3DImageType::SizeType v_ItkSize = a_ImageThatHasToFitInTheEnlargedImage->GetLargestPossibleRegion().GetSize();
        v_Origin[0] = a_ImageThatHasToFitInTheEnlargedImage->GetLargestPossibleRegion().GetIndex()[0];
        v_Origin[1] = a_ImageThatHasToFitInTheEnlargedImage->GetLargestPossibleRegion().GetIndex()[1];
        v_Origin[2] = a_ImageThatHasToFitInTheEnlargedImage->GetLargestPossibleRegion().GetIndex()[2];

        v_ItkPixelLocationCoordinatesInImage[0] = v_Origin[0];
        v_ItkPixelLocationCoordinatesInImage[1] = v_Origin[1];
        v_ItkPixelLocationCoordinatesInImage[2] = v_Origin[2];
        a_ImageThatHasToFitInTheEnlargedImage->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
        a_BaseImageToEnlarge->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_ListOfXCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[0]);
        v_ListOfYCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[1]);
        v_ListOfZCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[2]);

        v_ItkPixelLocationCoordinatesInImage[0] = v_Origin[0]+v_ItkSize[0] - 1;
        v_ItkPixelLocationCoordinatesInImage[1] = v_Origin[1];
        v_ItkPixelLocationCoordinatesInImage[2] = v_Origin[2];
        a_ImageThatHasToFitInTheEnlargedImage->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
        a_BaseImageToEnlarge->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_ListOfXCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[0]);
        v_ListOfYCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[1]);
        v_ListOfZCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[2]);

        v_ItkPixelLocationCoordinatesInImage[0] = v_Origin[0];
        v_ItkPixelLocationCoordinatesInImage[1] = v_Origin[1]+v_ItkSize[1] - 1;
        v_ItkPixelLocationCoordinatesInImage[2] = v_Origin[2];
        a_ImageThatHasToFitInTheEnlargedImage->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
        a_BaseImageToEnlarge->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_ListOfXCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[0]);
        v_ListOfYCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[1]);
        v_ListOfZCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[2]);

        v_ItkPixelLocationCoordinatesInImage[0] = v_Origin[0]+v_ItkSize[0] - 1;
        v_ItkPixelLocationCoordinatesInImage[1] = v_Origin[1]+v_ItkSize[1] - 1;
        v_ItkPixelLocationCoordinatesInImage[2] = v_Origin[2];
        a_ImageThatHasToFitInTheEnlargedImage->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
        a_BaseImageToEnlarge->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_ListOfXCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[0]);
        v_ListOfYCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[1]);
        v_ListOfZCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[2]);

        v_ItkPixelLocationCoordinatesInImage[0] = v_Origin[0];
        v_ItkPixelLocationCoordinatesInImage[1] = v_Origin[1];
        v_ItkPixelLocationCoordinatesInImage[2] = v_Origin[2]+v_ItkSize[2] - 1;
        a_ImageThatHasToFitInTheEnlargedImage->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
        a_BaseImageToEnlarge->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_ListOfXCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[0]);
        v_ListOfYCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[1]);
        v_ListOfZCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[2]);

        v_ItkPixelLocationCoordinatesInImage[0] = v_Origin[0]+v_ItkSize[0] - 1;
        v_ItkPixelLocationCoordinatesInImage[1] = v_Origin[1];
        v_ItkPixelLocationCoordinatesInImage[2] = v_Origin[2]+v_ItkSize[2] - 1;
        a_ImageThatHasToFitInTheEnlargedImage->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
        a_BaseImageToEnlarge->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_ListOfXCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[0]);
        v_ListOfYCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[1]);
        v_ListOfZCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[2]);

        v_ItkPixelLocationCoordinatesInImage[0] = v_Origin[0];
        v_ItkPixelLocationCoordinatesInImage[1] = v_Origin[1]+v_ItkSize[1] - 1;
        v_ItkPixelLocationCoordinatesInImage[2] = v_Origin[2]+v_ItkSize[2] - 1;
        a_ImageThatHasToFitInTheEnlargedImage->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
        a_BaseImageToEnlarge->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_ListOfXCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[0]);
        v_ListOfYCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[1]);
        v_ListOfZCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[2]);

        v_ItkPixelLocationCoordinatesInImage[0] = v_Origin[0]+v_ItkSize[0] - 1;
        v_ItkPixelLocationCoordinatesInImage[1] = v_Origin[1]+v_ItkSize[1] - 1;
        v_ItkPixelLocationCoordinatesInImage[2] = v_Origin[2]+v_ItkSize[2] - 1;
        a_ImageThatHasToFitInTheEnlargedImage->TransformIndexToPhysicalPoint(v_ItkPixelLocationCoordinatesInImage, v_ItkPixelLocationPointinSpace);
        a_BaseImageToEnlarge->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_ListOfXCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[0]);
        v_ListOfYCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[1]);
        v_ListOfZCoordinates.push_back(v_ItkPixelLocationCoordinatesInImage[2]);

        //Create New image
        egItkUC3DImagePtr v_NewBiggerImage = egItkUC3DImageType::New();
        egItkUC3DImageType::RegionType v_ItkRegion;
        egItkUC3DImageType::IndexType v_ItkStart;
        v_ItkStart[0] = *std::min_element(v_ListOfXCoordinates.begin(), v_ListOfXCoordinates.end())-1;
        v_ItkStart[1] = *std::min_element(v_ListOfYCoordinates.begin(), v_ListOfYCoordinates.end())-1;
        v_ItkStart[2] = *std::min_element(v_ListOfZCoordinates.begin(), v_ListOfZCoordinates.end())-1;
        v_ItkSize[0] = *std::max_element(v_ListOfXCoordinates.begin(), v_ListOfXCoordinates.end()) - *std::min_element(v_ListOfXCoordinates.begin(), v_ListOfXCoordinates.end())+3;
        v_ItkSize[1] = *std::max_element(v_ListOfYCoordinates.begin(), v_ListOfYCoordinates.end()) - *std::min_element(v_ListOfYCoordinates.begin(), v_ListOfYCoordinates.end())+3;
        v_ItkSize[2] = *std::max_element(v_ListOfZCoordinates.begin(), v_ListOfZCoordinates.end()) - *std::min_element(v_ListOfZCoordinates.begin(), v_ListOfZCoordinates.end())+3;

        v_ItkRegion.SetSize(v_ItkSize);
        v_ItkRegion.SetIndex(v_ItkStart);
        v_NewBiggerImage->SetRegions(v_ItkRegion);
        v_NewBiggerImage->SetDirection(a_BaseImageToEnlarge->GetDirection());
        v_NewBiggerImage->SetOrigin(a_BaseImageToEnlarge->GetOrigin());
        v_NewBiggerImage->SetSpacing(a_BaseImageToEnlarge->GetSpacing());
        v_NewBiggerImage->Allocate();
        itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_IteratorForItkIm(v_NewBiggerImage, v_NewBiggerImage->GetLargestPossibleRegion());
        v_IteratorForItkIm.GoToBegin();
        while (!v_IteratorForItkIm.IsAtEnd()){
            v_IteratorForItkIm.Set(0);
            ++v_IteratorForItkIm;
        }

        PasteImageFilterType::Pointer v_PasteFilter= PasteImageFilterType::New();
        v_PasteFilter->SetDestinationImage(v_NewBiggerImage);
        v_PasteFilter->SetSourceImage(a_BaseImageToEnlarge);
        v_PasteFilter->SetSourceRegion(a_BaseImageToEnlarge->GetLargestPossibleRegion());
        a_BaseImageToEnlarge->TransformIndexToPhysicalPoint(a_BaseImageToEnlarge->GetLargestPossibleRegion().GetIndex(), v_ItkPixelLocationPointinSpace);
        v_NewBiggerImage->TransformPhysicalPointToIndex(v_ItkPixelLocationPointinSpace, v_ItkPixelLocationCoordinatesInImage);
        v_PasteFilter->SetDestinationIndex(v_ItkPixelLocationCoordinatesInImage);
        v_PasteFilter->Update();
        egItkUC3DImagePtr v_NewITKImage = v_PasteFilter->GetOutput();
        v_NewITKImage->SetDirection(a_BaseImageToEnlarge->GetDirection());
        v_NewITKImage->SetOrigin(a_BaseImageToEnlarge->GetOrigin());
        v_NewITKImage->SetSpacing(a_BaseImageToEnlarge->GetSpacing());
        return v_NewITKImage;
    }
}
