import json

from ai.datasets.statistics import DatasetStatistics


with open(
    "datasets/metadata/ODIR5K/metadata.json"
) as f:

    metadata = json.load(f)

stats = DatasetStatistics(metadata)

report = stats.generate()

print("=" * 60)

print("DATASET REPORT")

print("=" * 60)

for k, v in report.items():

    print(f"{k}: {v}")
    