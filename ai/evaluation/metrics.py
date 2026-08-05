from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)


def calculate_metrics(y_true, y_pred):

    metrics = {

        "accuracy": accuracy_score(y_true, y_pred),

        "precision": precision_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=0
        ),

        "recall": recall_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=0
        ),

        "f1_score": f1_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=0
        ),

        "classification_report": classification_report(
            y_true,
            y_pred,
            zero_division=0
        )

    }

    return metrics