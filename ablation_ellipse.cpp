egItkUC3DImagePtr casImageComparisonPipeline::GenerateElipsoidAblationZones(egItkUC3DImagePtr& a_ablationMask, std::string a_path, egItkUC3DImageType::PointType a_targetPoint, std::string a_filename, TransMatrix3d v_mat)
{
    //load params
    ifstream v_File;
    v_File.open(a_filename, std::fstream::out);
    std::string v_shape;
    std::getline(v_File, v_shape);
    Vector3d v_radius;
    egItkUC3DImageType::PointType v_itkRadius;
    v_File >> v_itkRadius[0];
    v_radius[0] = v_itkRadius[0];
    v_File >> v_itkRadius[1];
    v_radius[1] = v_itkRadius[1];
    v_File >> v_itkRadius[2];
    v_radius[2] = v_itkRadius[2];
    egItkUC3DImageType::PointType v_translation;
    v_File >> v_translation[0];
    v_File >> v_translation[1];
    v_File >> v_translation[2];
    //v_translation[0] = -16;
    //v_translation[1] = 0;
    //v_translation[2] = 0;
    v_File.close();
    //create sufficiently big image
    egItkUC3DImageType::SizeType v_sizeOfmask;
    egItkUC3DImageType::IndexType v_sizeOfmaskInd;
    egItkUC3DImageType::SizeType v_size;
    egItkUC3DImageType::IndexType v_index;
    egItkUC3DImageType::PointType v_point;
    v_index[0] = -50;
    v_index[1] = -50;
    v_index[2] = -50;
    v_size[0] = 100;
    v_size[1] = 100;
    v_size[2] = 100;
    egItkUC3DImageType::PointType v_zeroPoint;
    v_zeroPoint[0] = 0;
    v_zeroPoint[1] = 0;
    v_zeroPoint[2] = 0;
    egItkUC3DImageType::PointType v_ablationOrigin;
    v_ablationOrigin = a_ablationMask->GetOrigin();
    v_ablationOrigin[0] += v_itkRadius[0];
    v_ablationOrigin[1] += v_itkRadius[1];
    v_ablationOrigin[2] += v_itkRadius[2];
    a_ablationMask->TransformPhysicalPointToIndex(v_ablationOrigin, v_sizeOfmaskInd);
    v_sizeOfmask[0] = v_sizeOfmaskInd[0] * 2;
    v_sizeOfmask[1] = v_sizeOfmaskInd[1] * 2;
    v_sizeOfmask[2] = v_sizeOfmaskInd[2] * 2;
    egItkUC3DImageType::PointType v_OriginPoint;
    v_OriginPoint[0] = -v_itkRadius[0];
    v_OriginPoint[1] = -v_itkRadius[1];
    v_OriginPoint[2] = -v_itkRadius[2];
    egItkUC3DImageType::IndexType v_zeroIndex;
    v_zeroIndex[0] = 0;
    v_zeroIndex[1] = 0;
    v_zeroIndex[2] = 0;
    egItkUC3DImageType::RegionType v_region;
    v_region.SetIndex(v_index);
    v_region.SetSize(v_size);
    //v_region.SetIndex(v_zeroIndex);
    //v_region.SetSize(v_sizeOfmask);
    egItkUC3DImagePtr v_predictedAblationMask = egItkUC3DImageType::New();
    v_predictedAblationMask->SetSpacing(a_ablationMask->GetSpacing());
    v_predictedAblationMask->SetRegions(v_region);
    v_predictedAblationMask->SetOrigin(v_zeroPoint);
    v_predictedAblationMask->Allocate();
    //calculate mask
    itk::ImageRegionIteratorWithIndex<egItkUC3DImageType> v_iterator(v_predictedAblationMask, v_predictedAblationMask->GetLargestPossibleRegion());
    v_iterator.GoToBegin();
    egItkUC3DImageType::IndexType v_imageIndex;
    egItkUC3DImageType::PointType v_imagePoint;
    float v_tmpFloat;
    while (!v_iterator.IsAtEnd()){
        v_imageIndex = v_iterator.GetIndex();
        v_predictedAblationMask->TransformIndexToPhysicalPoint(v_imageIndex, v_imagePoint);
        v_tmpFloat = 0;
        float v_tmp;
        ////elipsod equation
        for (int v_i = 0; v_i < 3; v_i++)
        {
            v_tmp = (sqr(v_imagePoint[v_i]) / sqr(v_itkRadius[v_i]));
            v_tmpFloat += v_tmp;
        }
        //generate axis of tumor
        //if (v_imagePoint[2] == 0 && v_imagePoint[1] == 0)
        //  v_tmpFloat = 1;
        //v_tmpFloat = (v_imagePoint[1])*v_imagePoint[1] + v_imagePoint[0] * v_imagePoint[0] ;
        if (v_tmpFloat <= 1)
        {
            v_iterator.Set(255);
            if (abs(v_imageIndex[1]) >(21))
                v_iterator.Set(255);
        }
        else
        {
            v_iterator.Set(0);
        }
        ++v_iterator;
    }
    //translate & rotate
    egItkUC3DImageType::PointType v_NewOriginPoint;
    v_NewOriginPoint[0] = v_zeroPoint[0] + v_translation[0];
    v_NewOriginPoint[1] = v_zeroPoint[1] + v_translation[1];
    v_NewOriginPoint[2] = v_zeroPoint[2] + v_translation[2];
    v_predictedAblationMask->SetOrigin(v_NewOriginPoint);
    t_affineTransformType::Pointer v_transform = t_affineTransformType::New();
    t_affineTransformType::MatrixType v_matrix;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            v_matrix[i][j] = v_mat[i][j];
    v_transform->SetMatrix(v_matrix);
    v_transform->SetCenter(v_zeroPoint);

    FilterType::Pointer filter = FilterType::New();
    InterpolatorType::Pointer interpolator = InterpolatorType::New();
    filter->SetInterpolator(interpolator);
    filter->SetDefaultPixelValue(0);
    filter->SetOutputSpacing(v_predictedAblationMask->GetSpacing());
    filter->SetOutputOrigin(v_zeroPoint);
    filter->SetSize(v_size);
    filter->SetOutputStartIndex(v_index);
    filter->SetInput(v_predictedAblationMask);
    filter->SetTransform(v_transform);
    filter->Update();
    egItkUC3DImagePtr v_rotatedAblation = filter->GetOutput();
    t_ImageFileWriter::Pointer v_writer1 = t_ImageFileWriter::New();
    t_ImageIOType::Pointer v_gdcmImageIO = t_ImageIOType::New();
    v_writer1->SetFileName(a_path + "RotatedPredictedSegm");
    v_writer1->SetInput(v_rotatedAblation);
    v_writer1->SetImageIO(v_gdcmImageIO);
    v_writer1->Update();
    v_writer1->SetFileName(a_path + "nonRotatedPredictedSegm");
    v_writer1->SetInput(v_predictedAblationMask);
    v_writer1->SetImageIO(v_gdcmImageIO);
    v_writer1->Update();
    v_rotatedAblation->SetOrigin(a_targetPoint);
    v_index = v_rotatedAblation->GetLargestPossibleRegion().GetIndex();
    v_rotatedAblation->TransformIndexToPhysicalPoint(v_index, v_OriginPoint);
    v_rotatedAblation->SetOrigin(v_OriginPoint);
    v_region = v_rotatedAblation->GetLargestPossibleRegion();
    v_region.SetIndex(v_zeroIndex);
    v_rotatedAblation->SetRegions(v_region);
    return v_rotatedAblation;
}
