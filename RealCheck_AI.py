import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import EfficientNet_B0_Weights
from PIL import Image
from pathlib import Path


MODEL_PATH = Path("models/realcheck_image_model.pth")

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def load_model():

    weights = EfficientNet_B0_Weights.DEFAULT

    model = models.efficientnet_b0(
        weights=None
    )

    model.classifier[1] = nn.Linear(
        model.classifier[1].in_features,
        2
    )

    model.load_state_dict(
        torch.load(
            MODEL_PATH,
            map_location=device,
            weights_only=True
        )
    )

    model = model.to(device)
    model.eval()

    return model


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def predict_image(image):

    model = load_model()

    image = image.convert("RGB")

    image_tensor = transform(image)

    image_tensor = image_tensor.unsqueeze(0)

    image_tensor = image_tensor.to(device)

    with torch.no_grad():

        outputs = model(image_tensor)

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        confidence, prediction = torch.max(
            probabilities,
            dim=1
        )

    prediction = prediction.item()
    confidence = confidence.item() * 100

    if prediction == 0:
        label = "FAKE"
    else:
        label = "REAL"

    return label, confidence