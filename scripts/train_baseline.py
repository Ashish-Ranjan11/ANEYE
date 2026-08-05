import torch
import torch.nn as nn

from ai.models.efficientnet import EfficientNetClassifier

from ai.training.dataloader import create_dataloaders

from ai.training.class_weights import compute_class_weights

from ai.training.trainer import Trainer

from ai.utils.seed import seed_everything


seed_everything()

device = torch.device(

    "cuda"

    if torch.cuda.is_available()

    else

    "cpu"

)

train_loader, valid_loader = create_dataloaders(

    "datasets/metadata/ODIR5K/metadata.json",

    batch_size=16

)

model = EfficientNetClassifier()

weights = compute_class_weights(

    "datasets/metadata/ODIR5K/metadata.json"

).to(device)

criterion = nn.CrossEntropyLoss(weight=weights)

optimizer = torch.optim.AdamW(

    model.parameters(),

    lr=1e-4

)

trainer = Trainer(

    model,

    train_loader,

    valid_loader,

    criterion,

    optimizer,

    device

)

EPOCHS = 5

best_acc = 0

for epoch in range(EPOCHS):

    print()

    print("=" * 60)

    print(f"Epoch {epoch+1}")

    print("=" * 60)

    train_loss, train_acc = trainer.train_one_epoch()

    valid_loss, valid_acc = trainer.validate()

    print()

    print("Train Loss :", train_loss)

    print("Train Acc  :", train_acc)

    print("Valid Loss :", valid_loss)

    print("Valid Acc  :", valid_acc)

    if valid_acc > best_acc:

        best_acc = valid_acc

        torch.save(

            model.state_dict(),

            "ai/checkpoints/efficientnet_baseline.pth"

        )

        print()

        print("Best model saved.")