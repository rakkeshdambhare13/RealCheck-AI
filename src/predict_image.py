
import torch
import torch.nn as nn

from torchvision import models, transforms
from pathlib import Path
from PIL import Image


# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = Path("models/realcheck_image_model.pth")


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    # Create EfficientNet-B0
    model = models.efficientnet_b0(
        weights=None
    )

    # Get original classifier input features
    in_features = model.classifier[1].in_features

    # IMPORTANT:
    # This MUST exactly match the architecture
    # used during training.
    #
    # Training architecture:
    #
    # model.classifier[1] = nn.Sequential(
    #     nn.Dropout(p=0.30),
    #     nn.Linear(in_features, 2)
    # )
    #
    # Therefore the saved checkpoint contains:
    #
    # classifier.1.0.weight
    # classifier.1.0.bias
    # classifier.1.1.weight
    # classifier.1.1.bias

    model.classifier[1] = nn.Sequential(
        nn.Dropout(
            p=0.30
        ),
        nn.Linear(
            in_features,
            2
        )
    )

    # Check model file
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    # Load trained weights
    state_dict = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True
    )

    model.load_state_dict(
        state_dict
    )

    # Move model to device
    model = model.to(device)

    # Evaluation mode
    model.eval()

    return model


# ============================================================
# IMAGE TRANSFORM
# ============================================================

transform = transforms.Compose([

    transforms.Resize(
        (224, 224)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[
            0.485,
            0.456,
            0.406
        ],
        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


# ============================================================
# IMAGE PREDICTION
# ============================================================

def predict_image(
    image,
    model=None
):

    # Load model if not provided
    if model is None:
        model = load_model()

    # Make sure image is RGB
    image = image.convert("RGB")

    # Apply preprocessing
    image_tensor = transform(
        image
    ).unsqueeze(0)

    # Move tensor to CPU/GPU
    image_tensor = image_tensor.to(
        device
    )

    # ========================================================
    # PREDICTION
    # ========================================================

    with torch.no_grad():

        outputs = model(
            image_tensor
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        confidence_tensor, prediction_tensor = torch.max(
            probabilities,
            dim=1
        )

    # Convert tensors to Python values
    prediction = prediction_tensor.item()

    confidence = confidence_tensor.item()

    # ========================================================
    # CLASS SCORES
    # ========================================================

    # Dataset:
    # 0 = FAKE
    # 1 = REAL

    fake_score = probabilities[
        0, 0
    ].item()

    real_score = probabilities[
        0, 1
    ].item()

    # ========================================================
    # LABEL
    # ========================================================

    if prediction == 0:
        label = "FAKE"
    else:
        label = "REAL"

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {
        "prediction": label,
        "confidence": confidence,
        "fake_score": fake_score,
        "real_score": real_score,
        "class_id": prediction
    }
