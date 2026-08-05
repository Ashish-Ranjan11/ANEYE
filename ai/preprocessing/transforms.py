import albumentations as A


def get_train_transforms():

    return A.Compose([

        A.HorizontalFlip(p=0.5),

        A.Rotate(
            limit=10,
            border_mode=0,
            p=0.5
        ),

        A.RandomBrightnessContrast(
            brightness_limit=0.2,
            contrast_limit=0.2,
            p=0.5
        ),

        A.CLAHE(
            clip_limit=2,
            p=0.3
        ),

        A.GaussNoise(
            std_range=(0.02, 0.08),
            p=0.3
        ),

        A.GaussianBlur(
            blur_limit=(3, 5),
            p=0.2
        )

    ])


def get_valid_transforms():

    return A.Compose([])