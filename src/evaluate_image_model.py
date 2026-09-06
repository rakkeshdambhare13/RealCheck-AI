import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torchvision.models import EfficientNet_B0_Weights
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
from pathlib import Path


# =============================
# SETTINGS
# =============================

VAL_DIR = Path("datasets/image/validation")
MODEL_PATH = Path("models/realcheck_image_model.pth")

BATCH_SIZE = 32


# =============================
# DEVICE
# =============================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)


# =============================
# TRANSFORM
# =============================

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# =============================
# DATASET
# =============================

dataset = datasets.ImageFolder(
    VAL_DIR,
    transform=transform
)

loader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

print("Classes:", dataset.classes)
print("Validation images:", len(dataset))


# =============================
# LOAD MODEL
# =============================

weights = EfficientNet_B0_Weights.DEFAULT

model = models.efficientnet_b0(weights=None)

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


# =============================
# PREDICTIONS
# =============================

all_labels = []
all_predictions = []

with torch.no_grad():

    for images, labels in loader:

        images = images.to(device)

        outputs = model(images)

        predictions = torch.argmax(
            outputs,
            dim=1
        )

        all_labels.extend(labels.numpy())
        all_predictions.extend(
            predictions.cpu().numpy()
        )


# =============================
# METRICS
# =============================

accuracy = accuracy_score(
    all_labels,
    all_predictions
)

precision = precision_score(
    all_labels,
    all_predictions,
    average="binary"
)

recall = recall_score(
    all_labels,
    all_predictions,
    average="binary"
)

f1 = f1_score(
    all_labels,
    all_predictions,
    average="binary"
)

cm = confusion_matrix(
    all_labels,
    all_predictions
)


# =============================
# RESULTS
# =============================

print("\n================================")
print("REALCHECK AI MODEL EVALUATION")
print("================================")

print(f"Accuracy  : {accuracy * 100:.2f}%")
print(f"Precision : {precision * 100:.2f}%")
print(f"Recall    : {recall * 100:.2f}%")
print(f"F1 Score  : {f1 * 100:.2f}%")

print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")

print(
    classification_report(
        all_labels,
        all_predictions,
        target_names=dataset.classes
    )
)