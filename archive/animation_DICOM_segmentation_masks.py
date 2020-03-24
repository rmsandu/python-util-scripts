# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import DicomReader as Reader
import ResampleSegmentations
import SimpleITK as sitk

#%%


class Animation(object):

    def __init__(self, ablation_img_sitk, tumor_img_sitk, source_img_sitk):
        self.ablation_img_sitk = ablation_img_sitk
        self.tumor_img_sitk = tumor_img_sitk
        self.source_img_sitk = source_img_sitk

        source_img_sitk_cast = sitk.Cast(sitk.RescaleIntensity(self.source_img_sitk), sitk.sitkUInt16)
        tumor_img_sitk_cast = sitk.Cast(sitk.RescaleIntensity(self.tumor_img_sitk), sitk.sitkUInt16)
        ablation_img_sitk_cast = sitk.Cast(sitk.RescaleIntensity(self.ablation_img_sitk), sitk.sitkUInt16)

        self.ablation_mask_nda = sitk.GetArrayFromImage(ablation_img_sitk_cast)
        self.source_img_nda = sitk.GetArrayFromImage(source_img_sitk_cast)
        self.tumor_mask_nda = sitk.GetArrayFromImage(tumor_img_sitk_cast)

    def get_tumor_img(self):
        return self.tumor_mask_nda

    def get_ablation_img(self):
        return self.ablation_mask_nda

    def get_src_img(self):
        return self.source_img_nda

    def animate_dicom(self):

        fig = plt.figure()
        plt.grid(False)
        self.im = plt.imshow(self.source_img_nda[0, :, :], cmap=plt.cm.gray, interpolation='none', animated=True)
        self.im2 = plt.imshow(self.tumor_mask_nda[0, :, :], cmap='RdYlGn', alpha=0.8, interpolation='none', animated=True)
        self.im3 = plt.imshow(self.ablation_mask_nda[0, :, :], cmap='seismic', alpha=0.3, interpolation='none', animated=True)
        self.ims = []
        return fig

    def update_fig(self, z):
        # z = 138
        # print("z slice: ", z)
        TumorOverlay = self.tumor_mask_nda[z, :, :].astype(np.float)
        TumorOverlay[TumorOverlay == 0] = np.nan

        AblationOverlay = self.ablation_mask_nda[z, :, :].astype(np.float)
        AblationOverlay[AblationOverlay == 0] = np.nan

        new_slice = self.source_img_nda[z, :, :]
        self.im2.set_array(TumorOverlay)
        self.im3.set_array(AblationOverlay)
        self.im.set_array(new_slice)
        self.ims.append([self.im])
        self.ims.append([self.im2])
        self.ims.append([self.im3])
        return [self.ims]


if __name__ == '__main__':

    ablation = r"C:\tmp_patients\Pat_MAV_BE_B02_\Study_0\Series_7\CAS-One Recordings\2019-07-28_19-33-55\Segmentations\SeriesNo_28\SegmentationNo_0"
    tumor = r"C:\tmp_patients\Pat_MAV_BE_B02_\Study_0\Series_7\CAS-One Recordings\2019-07-28_19-33-55\Segmentations\SeriesNo_7\SegmentationNo_0"
    source_img = r"C:\tmp_patients\Pat_MAV_BE_B02_\Study_0\Series_7"

    ablation_img_sitk = Reader.read_dcm_series(ablation, False)
    tumor_img_sitk = Reader.read_dcm_series(tumor, False)
    source_img_sitk = Reader.read_dcm_series(source_img, False)
    resizer_tumor = ResampleSegmentations.ResizeSegmentation(source_img_sitk, tumor_img_sitk)
    resizer_ablation = ResampleSegmentations.ResizeSegmentation(source_img_sitk, ablation_img_sitk)
    tumor_img_resampled = resizer_tumor.resample_segmentation()
    ablation_img_resampled = resizer_ablation.resample_segmentation()

    animation_obj = Animation(ablation_img_resampled, tumor_img_resampled, source_img_sitk)
    fig = animation_obj.animate_dicom()
    img = animation_obj.get_src_img()
    slices, x, y = img.shape
    frames = slices - 1
    ani = animation.FuncAnimation(fig, animation_obj.update_fig,  frames=frames, interval=1, repeat_delay=10)
    plt.show()

