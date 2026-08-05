import json
import os

import pandas as pd
import torch

from ai.evaluation.metrics import calculate_metrics

from ai.evaluation.confusion_matrix import save_confusion_matrix


@torch.no_grad()
def evaluate_model(
    model,
    dataloader,
    class_names,
    device,
    save_dir
):

    model.eval()

    predictions = []

    labels = []

    for images, targets in dataloader:

        images = images.to(device)

        outputs = model(images)

        preds = outputs.argmax(1)

        predictions.extend(
            preds.cpu().numpy()
        )

        labels.extend(
            targets.numpy()
        )

    metrics = calculate_metrics(
        labels,
        predictions
    )

    os.makedirs(save_dir, exist_ok=True)

    with open(
        os.path.join(
            save_dir,
            "metrics.json"
        ),
        "w"
    ) as f:

        json.dump(
            {
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"]
            },
            f,
            indent=4
        )

    with open(
        os.path.join(
            save_dir,
            "classification_report.txt"
        ),
        "w"
    ) as f:

        f.write(
            metrics["classification_report"]
        )

    pd.DataFrame({

        "actual": labels,

        "prediction": predictions

    }).to_csv(

        os.path.join(
            save_dir,
            "predictions.csv"
        ),

        index=False

    )

    save_confusion_matrix(

        labels,

        predictions,

        class_names,

        save_dir

    )

    return metrics