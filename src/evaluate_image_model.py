import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

BATCH_SIZE = 32

VAL_DIR = Path("datasets/image/validation")
MODEL_PATH = Path("models/realcheck_image_model.pth")


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)


# ============================================================
# IMAGE TRANSFORM
# ============================================================

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# DATASET
# ============================================================

val_dataset = datasets.ImageFolder(
    VAL_DIR,
    transform=val_transform
)

print("Classes:", val_dataset.classes)
print("Validation images:", len(val_dataset))


# ============================================================
# DATA LOADER
# ============================================================

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# MODEL
# ============================================================

print("\nLoading EfficientNet-B0 model...")

model = models.efficientnet_b0(
    weights=None
)


# ============================================================
# CLASSIFIER
# IMPORTANT: Must match train_image_model.py
# ============================================================

in_features = model.classifier[1].in_features

model.classifier[1] = nn.Sequential(
    nn.Dropout(p=0.30),
    nn.Linear(in_features, 2)
)

model = model.to(device)


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

print("Loading trained model...")

if not MODEL_PATH.exists():
    print("\nERROR: Model file not found!")
    print("Expected model at:")
    print(MODEL_PATH)

    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )


model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True
    )
)

model.eval()

print("Model loaded successfully.")


# ============================================================
# EVALUATION
# ============================================================

all_labels = []
all_predictions = []


print("\nRunning evaluation...")


with torch.no_grad():

    for images, labels in val_loader:

        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)

        predictions = torch.argmax(
            outputs,
            dim=1
        )

        all_labels.extend(
            labels.cpu().numpy()
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )


# ============================================================
# METRICS
# ============================================================

accuracy = (
    accuracy_score(
        all_labels,
        all_predictions
    ) * 100
)


precision = (
    precision_score(
        all_labels,
        all_predictions,
        average="binary",
        zero_division=0
    ) * 100
)


recall = (
    recall_score(
        all_labels,
        all_predictions,
        average="binary",
        zero_division=0
    ) * 100
)


f1 = (
    f1_score(
        all_labels,
        all_predictions,
        average="binary",
        zero_division=0
    ) * 100
)


cm = confusion_matrix(
    all_labels,
    all_predictions
)


# ============================================================
# RESULTS
# ============================================================

print("\n================================")
print("REALCHECK AI MODEL EVALUATION")
print("================================")

print(
    f"Accuracy  : {accuracy:.2f}%"
)

print(
    f"Precision : {precision:.2f}%"
)

print(
    f"Recall    : {recall:.2f}%"
)

print(
    f"F1 Score  : {f1:.2f}%"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\nConfusion Matrix:")
print(cm)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:")

print(
    classification_report(
        all_labels,
        all_predictions,
        target_names=val_dataset.classes,
        zero_division=0
    )
)


# ============================================================
# COMPLETE
# ============================================================

print("================================")
print("EVALUATION COMPLETED")
print("================================")
