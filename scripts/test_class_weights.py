from ai.training.class_weights import compute_class_weights

weights = compute_class_weights(
    "datasets/metadata/ODIR5K/metadata.json"
)

print(weights)