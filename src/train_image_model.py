import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torchvision.models import EfficientNet_B0_Weights

from sklearn.metrics import accuracy_score, f1_score

from pathlib import Path
import random
import numpy as np


# ============================================================
# SETTINGS
# ============================================================

BATCH_SIZE = 32

EPOCHS = 25

LEARNING_RATE = 0.00005

PATIENCE = 5

TRAIN_DIR = Path("datasets/image/train")
VAL_DIR = Path("datasets/image/validation")

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "realcheck_image_model.pth"


# ============================================================
# REPRODUCIBILITY
# ============================================================

SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)


# ============================================================
# IMAGE TRANSFORMS
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize((256, 256)),

    transforms.RandomResizedCrop(
        224,
        scale=(0.85, 1.0),
        ratio=(0.9, 1.1)
    ),

    transforms.RandomHorizontalFlip(
        p=0.5
    ),

    transforms.RandomRotation(
        degrees=8
    ),

    transforms.ColorJitter(
        brightness=0.15,
        contrast=0.15,
        saturation=0.10,
        hue=0.02
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


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

train_dataset = datasets.ImageFolder(
    TRAIN_DIR,
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    VAL_DIR,
    transform=val_transform
)

print("Classes:", train_dataset.classes)
print("Training images:", len(train_dataset))
print("Validation images:", len(val_dataset))


# ============================================================
# DATA LOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# MODEL
# ============================================================

print("\nLoading EfficientNet-B0 pretrained model...")

weights = EfficientNet_B0_Weights.DEFAULT

model = models.efficientnet_b0(
    weights=weights
)


# ============================================================
# CLASSIFIER
# ============================================================

in_features = model.classifier[1].in_features

model.classifier[1] = nn.Sequential(
    nn.Dropout(p=0.30),
    nn.Linear(in_features, 2)
)

model = model.to(device)


# ============================================================
# LOSS FUNCTION
# ============================================================

criterion = nn.CrossEntropyLoss(
    label_smoothing=0.05
)


# ============================================================
# OPTIMIZER
# ============================================================

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)


# ============================================================
# LEARNING RATE SCHEDULER
# ============================================================

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=2,
    min_lr=1e-7
)


# ============================================================
# TRAINING VARIABLES
# ============================================================

best_val_accuracy = 0.0

best_val_f1 = 0.0

epochs_without_improvement = 0


# ============================================================
# TRAINING HEADER
# ============================================================

print("\n================================")
print("REALCHECK AI MODEL TRAINING")
print("================================")

print(f"Epochs: {EPOCHS}")
print(f"Batch size: {BATCH_SIZE}")
print(f"Learning rate: {LEARNING_RATE}")
print("Model: EfficientNet-B0")
print("Optimization: AdamW")
print("Early stopping: Enabled")

print("================================\n")


# ============================================================
# TRAINING LOOP
# ============================================================

for epoch in range(EPOCHS):

    # ========================================================
    # TRAIN
    # ========================================================

    model.train()

    running_loss = 0.0

    train_correct = 0

    train_total = 0


    for images, labels in train_loader:

        images = images.to(device)

        labels = labels.to(device)


        optimizer.zero_grad()


        outputs = model(images)


        loss = criterion(
            outputs,
            labels
        )


        loss.backward()


        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0
        )


        optimizer.step()


        running_loss += loss.item()


        predictions = torch.argmax(
            outputs,
            dim=1
        )


        train_total += labels.size(0)


        train_correct += (
            predictions == labels
        ).sum().item()


    # ========================================================
    # TRAIN METRICS
    # ========================================================

    train_accuracy = (
        100.0 * train_correct / train_total
    )


    average_train_loss = (
        running_loss / len(train_loader)
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    model.eval()

    all_labels = []

    all_predictions = []

    validation_loss = 0.0


    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(device)

            labels = labels.to(device)


            outputs = model(images)


            loss = criterion(
                outputs,
                labels
            )


            validation_loss += loss.item()


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


    # ========================================================
    # VALIDATION METRICS
    # ========================================================

    val_accuracy = (
        accuracy_score(
            all_labels,
            all_predictions
        ) * 100
    )


    val_f1 = (
        f1_score(
            all_labels,
            all_predictions,
            average="weighted"
        ) * 100
    )


    average_val_loss = (
        validation_loss / len(val_loader)
    )


    # ========================================================
    # LEARNING RATE
    # ========================================================

    scheduler.step(val_accuracy)

    current_lr = optimizer.param_groups[0]["lr"]


    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    print(
        f"Epoch [{epoch + 1}/{EPOCHS}] "
        f"Loss: {average_train_loss:.4f} "
        f"Train Acc: {train_accuracy:.2f}% "
        f"Val Loss: {average_val_loss:.4f} "
        f"Val Acc: {val_accuracy:.2f}% "
        f"Val F1: {val_f1:.2f}% "
        f"LR: {current_lr:.7f}"
    )


    # ========================================================
    # SAVE BEST MODEL
    # ========================================================

    if val_accuracy > best_val_accuracy:

        best_val_accuracy = val_accuracy

        best_val_f1 = val_f1


        torch.save(
            model.state_dict(),
            MODEL_PATH
        )


        print(
            f"✓ Best model saved! "
            f"Validation Accuracy: {val_accuracy:.2f}%"
        )


        epochs_without_improvement = 0


    else:

        epochs_without_improvement += 1


    # ========================================================
    # EARLY STOPPING
    # ========================================================

    if epochs_without_improvement >= PATIENCE:

        print(
            "\nEarly stopping triggered."
        )

        print(
            "Validation accuracy stopped improving."
        )

        break


# ============================================================
# TRAINING COMPLETED
# ============================================================

print("\n================================")
print("TRAINING COMPLETED")
print("================================")


print(
    f"Best Validation Accuracy: "
    f"{best_val_accuracy:.2f}%"
)


print(
    f"Best Validation F1 Score: "
    f"{best_val_f1:.2f}%"
)


print(
    "\nBest model saved at:"
)


print(
    MODEL_PATH
)


print("\n================================")