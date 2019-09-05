# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import DicomReader as Reader
import SimpleITK as sitk

#%%

global tumor_mask_nda
global ablation_mask_nda


class Animation(object):

    def __init__(self, ablation_img_sitk, tumor_img_sitk, source_img_sitk):
        self.ablation_img_sitk = ablation_img_sitk
        self.tumor_img_sitk = tumor_img_sitk
        self.source_img_sitk = source_img_sitk

        self.ablation_mask_nda = sitk.GetArrayFromImage(self.ablation_img_sitk)
        self.SourceImg = sitk.GetArrayFromImage(self.source_img_sitk)
        self.tumor_mask_nda = sitk.GetArrayFromImage(self.tumor_img_sitk)

    def get_tumor_img(self):
        return self.tumor_mask_nda

    def get_ablation_img(self):
        return self.ablation_mask_nda

    def get_src_img(self):
        return self.source_img_sitk

    def animate_dicom(self):
        # source_img_sitk_cast = sitk.Cast(sitk.RescaleIntensity(self.source_img_sitk), sitk.sitkUInt16)
        # tumor_img_sitk_cast = sitk.Cast(sitk.RescaleIntensity(self.tumor_img_sitk), sitk.sitkUInt16)
        # ablation_img_sitk_cast = sitk.Cast(sitk.RescaleIntensity(self.ablation_img_sitk), sitk.sitkUInt16)
        #
        # SourceImg = sitk.GetArrayFromImage(source_img_sitk_cast)
        # SourceImg = SourceImg.astype(np.float)
        # SourceImg[SourceImg < 20] = np.nan
        # SourceImg[SourceImg > 720] = np.nan
        # SourceImg[SourceImg == 0] = np.nan

        # slices, x, y = SourceImg.shape
        fig = plt.figure()
        plt.grid(False)
        self.im = plt.imshow(self.SourceImg[0, :, :], cmap=plt.cm.gray, interpolation='none', animated=True)
        self.im2 = plt.imshow(self.tumor_mask_nda[0, :, :], cmap='RdYlBu', alpha=0.3, interpolation='none', animated=True)
        self.im3 = plt.imshow(self.ablation_mask_nda[0, :, :], cmap='winter', alpha=0.3, interpolation='none', animated=True)
        self.ims = []
        return fig

    def update_fig(self, z):
        TumorOverlay = tumor_mask_nda[z, :, :].astype(np.float)
        TumorOverlay[TumorOverlay == 0] = np.nan

        AblationOverlay = ablation_mask_nda[z,:,:].astype(np.float)
        AblationOverlay[AblationOverlay == 0] = np.nan

        new_slice = self.SourceImg[z, :, :]

        self.im2.set_array(TumorOverlay)
        self.im3.set_array(AblationOverlay)
        self.im.set_array(new_slice)
        self.ims.append([self.im])
        self.ims.append([self.im2])
        self.ims.append([self.im3])
        return [self.ims]


if __name__ == '__main__':

    animation_obj = Animation(...)
    fig = Animation.animate_dicom()
    img = Animation.get_src_img()
    slices, x, y = img.shape
    ani = animation.FuncAnimation(fig, Animation.update_fig, frames=np.arange(1, slices), interval=10)
    plt.show()

# plot_histogram(SourceImg)
# blit =  True option to re-draw only the parts that have changed
# repeat_delay=1000
# plt.show()
# saving doeasn't currently work 14.05.2018
# ani.save('animationTumor.gif', writer='imagemagick', fps=10)
# ani.save('animation.mp4', writer='ffmpeg' ,fps=10)