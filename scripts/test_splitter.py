from collections import Counter

from ai.training.splitter import StratifiedDatasetSplitter

splitter = StratifiedDatasetSplitter(
    "datasets/metadata/ODIR5K/metadata.json"
)

train, valid = splitter.split()

print("="*60)
print("Train Images :", len(train))
print("Validation Images :", len(valid))
print("="*60)

train_counts = Counter([x["label"] for x in train])
valid_counts = Counter([x["label"] for x in valid])

print("\nTRAIN DISTRIBUTION\n")
print(train_counts)

print("\nVALID DISTRIBUTION\n")
print(valid_counts)