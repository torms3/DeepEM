from augmentor import *


def get_augmentation(is_train, box=None, interp=False, missing=7, blur=7,
                     lost=True, random=False, **kwargs):
    # Mild misalignment
    m1 = Blend(
        [Misalign((0,10), margin=1), SlipMisalign((0,10), interp=interp, margin=1)],
        props=[0.7,0.3]
    )

    # Medium misalignment
    m2 = Blend(
        [Misalign((0,30), margin=1), SlipMisalign((0,30), interp=interp, margin=1)],
        props=[0.7,0.3]
    )

    # Large misalignment
    m3 = Blend(
        [Misalign((0,50), margin=1), SlipMisalign((0,50), interp=interp, margin=1)],
        props=[0.7,0.3]
    )

    augs = list()

    if is_train:
        # Box
        if box == 'noise':
            augs.append(
                NoiseBox(sigma=(1,3), dims=(10,50), margin=(1,10,10),
                         density=0.3, skip=0.1)
            )
        elif box == 'fill':
            augs.append(
                FillBox(dims=(10,50), margin=(1,10,10),
                        density=0.3, skip=0.1)
            )

        # Brightness & contrast purterbation
        augs.append(
            MixedGrayscale2D(
                contrast_factor=0.5,
                brightness_factor=0.5,
                prob=1, skip=0.3))

        # Missing section & misalignment
        to_blend = list()
        to_blend.append(Compose([m1,m2,m3]))
        to_blend.append(Blend([
            MisalignPlusMissing((5,30), value=1, random=random),
            MisalignPlusMissing((5,30), value=1, random=False)
        ]))
        if missing > 0:
            to_blend.append(Blend([
                MixedMissingSection(maxsec=missing, individual=True, value=1, random=random),
                MixedMissingSection(maxsec=missing, individual=False, value=1, random=random),
                MixedMissingSection(maxsec=missing, individual=False, value=1, random=False)
            ]))
        if lost:
            to_blend.append(Blend([
                LostSection(1),
                LostPlusMissing(value=1, random=random),
                LostPlusMissing(value=1, random=False)
            ]))
        augs.append(Blend(to_blend))

        # Out-of-focus
        if blur > 0:
            augs.append(MixedBlurrySection(maxsec=blur))

        # Warping
        augs.append(Warp(skip=0.3, do_twist=False, rot_max=45.0, scale_max=1.1))

    # Flip & rotate
    augs.append(FlipRotate())

    return Compose(augs)
