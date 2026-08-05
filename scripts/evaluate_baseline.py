import torch

from ai.models.efficientnet import EfficientNetClassifier

from ai.training.dataloader import create_dataloaders

from ai.evaluation.evaluator import evaluate_model


device = torch.device(

    "cuda"

    if torch.cuda.is_available()

    else

    "cpu"

)

_, valid_loader = create_dataloaders(

    "datasets/metadata/ODIR5K/metadata.json"

)

model = EfficientNetClassifier()

model.load_state_dict(

    torch.load(

        "ai/checkpoints/efficientnet_baseline.pth",

        map_location=device

    )

)

model.to(device)

class_names = [

    "Normal",

    "Diabetic Retinopathy",

    "Other Retinal Diseases",

    "Cataract",

    "Glaucoma",

    "Age-related Macular Degeneration",

    "Myopia",

    "Hypertensive Retinopathy"

]

metrics = evaluate_model(

    model,

    valid_loader,

    class_names,

    device,

    "ai/evaluation/results"

)

print(metrics)