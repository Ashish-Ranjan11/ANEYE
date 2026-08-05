from ai.training.dataloader import create_dataloaders

train_loader, valid_loader = create_dataloaders(
    "datasets/metadata/ODIR5K/metadata.json"
)

print("=" * 60)
print("Train Batches")
print("=" * 60)

print(len(train_loader))

images, labels = next(iter(train_loader))

print(images.shape)

print(labels.shape)