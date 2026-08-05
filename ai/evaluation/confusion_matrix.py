import os

import matplotlib.pyplot as plt

from sklearn.metrics import confusion_matrix

import seaborn as sns


def save_confusion_matrix(
    y_true,
    y_pred,
    class_names,
    save_dir
):

    os.makedirs(save_dir, exist_ok=True)

    cm = confusion_matrix(
        y_true,
        y_pred
    )

    plt.figure(figsize=(10,8))

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names
    )

    plt.xlabel("Predicted")

    plt.ylabel("Actual")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            save_dir,
            "confusion_matrix.png"
        )
    )

    plt.close()