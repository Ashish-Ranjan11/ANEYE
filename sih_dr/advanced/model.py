import torch
import torch.nn as nn
import timm


ADVANCED_LABELS = [
    "VB_IRMA",
    "NV",
    "VH",
]


class AdvancedDREvidenceModel(
    nn.Module
):

    def __init__(
        self,
        backbone="efficientnet_b0",
        pretrained=False,
    ):

        super().__init__()

        self.backbone_name = (
            backbone
        )

        self.encoder = (
            timm.create_model(
                backbone,
                pretrained=pretrained,
                num_classes=0,
                global_pool="avg",
            )
        )

        features = (
            self.encoder
            .num_features
        )

        self.dropout = (
            nn.Dropout(
                0.30
            )
        )

        # Explicit independent evidence heads.
        self.heads = (
            nn.ModuleDict({
                "VB_IRMA":
                    nn.Linear(
                        features,
                        1
                    ),

                "NV":
                    nn.Linear(
                        features,
                        1
                    ),

                "VH":
                    nn.Linear(
                        features,
                        1
                    ),
            })
        )


    def forward(
        self,
        x
    ):

        features = (
            self.encoder(
                x
            )
        )

        dropped = (
            self.dropout(
                features
            )
        )

        named_logits = {}

        outputs = []

        for name in (
            "VB_IRMA",
            "NV",
            "VH",
        ):

            logit = (
                self.heads[
                    name
                ](
                    dropped
                )
                .squeeze(
                    1
                )
            )

            named_logits[
                name
            ] = logit

            outputs.append(
                logit
            )

        logits = torch.stack(
            outputs,
            dim=1,
        )

        return {
            "logits":
                logits,

            "named_logits":
                named_logits,

            "features":
                features,
        }


    def load_retinal_encoder(
        self,
        global_checkpoint
    ):
        """
        Warm-start the encoder from our already-trained
        APTOS EfficientNet-B0 retinal grader.

        Advanced heads remain newly initialized and are
        independently supervised by MMRDR lesion labels.
        """

        state = global_checkpoint[
            "model_state_dict"
        ]

        encoder_state = {}

        prefix = "encoder."

        for key, value in state.items():

            if key.startswith(
                prefix
            ):

                encoder_state[
                    key[
                        len(
                            prefix
                        ):
                    ]
                ] = value

        result = (
            self.encoder
            .load_state_dict(
                encoder_state,
                strict=False,
            )
        )

        return {
            "missing":
                list(
                    result.missing_keys
                ),

            "unexpected":
                list(
                    result.unexpected_keys
                ),
        }
