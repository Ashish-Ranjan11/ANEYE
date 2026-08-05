import json
from sklearn.model_selection import StratifiedShuffleSplit


class StratifiedDatasetSplitter:

    def __init__(self, metadata_file):

        with open(metadata_file) as f:
            self.metadata = json.load(f)

    def split(self, test_size=0.2, random_state=42):

        labels = [item["class_id"] for item in self.metadata]

        splitter = StratifiedShuffleSplit(
            n_splits=1,
            test_size=test_size,
            random_state=random_state
        )

        train_idx, valid_idx = next(
            splitter.split(self.metadata, labels)
        )

        train = [self.metadata[i] for i in train_idx]
        valid = [self.metadata[i] for i in valid_idx]

        return train, valid