import torch

from sih_dr.lesions.model import (
    build_lesion_model,
)


def main():

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Device:", device)

    model = build_lesion_model(
        encoder_weights="imagenet"
    ).to(device)

    x = torch.randn(
        1,
        3,
        512,
        512,
        device=device,
    )

    with torch.no_grad():
        y = model(x)

    print("Input :", x.shape)
    print("Output:", y.shape)

    assert y.shape == (
        1,
        4,
        512,
        512,
    )

    if device.type == "cuda":

        print(
            "GPU allocated:",
            round(
                torch.cuda.memory_allocated()
                / 1024**3,
                2,
            ),
            "GB",
        )

        print(
            "GPU reserved:",
            round(
                torch.cuda.memory_reserved()
                / 1024**3,
                2,
            ),
            "GB",
        )

    print("\nLESION MODEL GPU TEST OK")


if __name__ == "__main__":
    main()