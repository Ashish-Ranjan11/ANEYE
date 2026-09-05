import segmentation_models_pytorch as smp


def build_lesion_model(
    encoder_weights="imagenet",
):

    model = smp.Unet(
        encoder_name="efficientnet-b0",
        encoder_weights=encoder_weights,

        in_channels=3,

        # MA / HE / EX / SE
        classes=4,

        activation=None,
    )

    return model