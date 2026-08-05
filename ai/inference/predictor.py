import torch

from ai.models.efficientnet import EfficientNetClassifier

from ai.inference.preprocess import preprocess_image

from ai.inference.disease_info import DISEASE_INFO

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else
    "cpu"
)

CLASS_NAMES = [
    "Normal",
    "Cataract",
    "Diabetic Retinopathy",
    "Glaucoma",
    "Age-related Macular Degeneration",
    "Hypertensive Retinopathy",
    "Myopia",
    "Other Retinal Diseases"
]

model = EfficientNetClassifier()

model.load_state_dict(
    torch.load(
        "ai/checkpoints/efficientnet_baseline.pth",
        map_location=DEVICE
    )
)

model.to(DEVICE)

model.eval()


@torch.no_grad()

def predict(image_path):

    image = preprocess_image(image_path)

    image = image.to(DEVICE)

    output = model(image)

    probabilities = torch.softmax(output,dim=1)

    confidence,prediction = probabilities.max(1)

    disease = CLASS_NAMES[prediction.item()]

    return{

        "prediction":disease,

        "confidence":round(confidence.item()*100,2),

        "description":DISEASE_INFO[disease]["description"],

        "severity":DISEASE_INFO[disease]["severity"],

        "recommendation":DISEASE_INFO[disease]["recommendation"]

    }