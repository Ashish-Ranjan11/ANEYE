import json
import torch
from collections import Counter


def compute_class_weights(metadata_file):

    with open(metadata_file) as f:
        metadata = json.load(f)

    labels = [x["class_id"] for x in metadata]

    counts = Counter(labels)

    total = len(labels)

    num_classes = len(counts)

    weights = []

    for i in range(num_classes):

        weights.append(
            total / (num_classes * counts[i])
        )

    return torch.tensor(weights, dtype=torch.float32)