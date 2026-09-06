import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from pathlib import Path


MODEL_PATH = Path("models/realcheck_image_model.pth")

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def load_model():

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


def analyze_video(video_path, frame_interval=15):

    model = load_model()

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError("Could not open video.")

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30

    frame_number = 0

    analyzed_frames = 0
    fake_frames = 0
    real_frames = 0

    fake_scores = []
    suspicious_frames = []

    while True:

        success, frame = cap.read()

        if not success:
            break

        if frame_number % frame_interval == 0:

            # OpenCV BGR → RGB
            frame_rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            image = Image.fromarray(
                frame_rgb
            )

            image_tensor = transform(
                image
            )

            image_tensor = image_tensor.unsqueeze(0)
            image_tensor = image_tensor.to(device)

            with torch.no_grad():

                outputs = model(
                    image_tensor
                )

                probabilities = torch.softmax(
                    outputs,
                    dim=1
                )

                fake_probability = (
                    probabilities[0][0].item()
                )

            fake_percentage = (
                fake_probability * 100
            )

            analyzed_frames += 1

            fake_scores.append(
                fake_percentage
            )

            if fake_percentage >= 50:

                fake_frames += 1

            else:

                real_frames += 1

            # Suspicious frame threshold
            if fake_percentage >= 75:

                suspicious_frames.append({
                    "frame": frame_number,
                    "time": frame_number / fps,
                    "fake_probability": fake_percentage
                })

        frame_number += 1

    cap.release()

    if analyzed_frames == 0:

        raise ValueError(
            "No frames could be analyzed."
        )

    average_fake_score = (
        sum(fake_scores) / len(fake_scores)
    )

    fake_ratio = (
        fake_frames / analyzed_frames
    )

    if average_fake_score >= 50:

        result = "FAKE"

    else:

        result = "REAL"

    return {
        "result": result,
        "confidence": (
            average_fake_score
            if result == "FAKE"
            else 100 - average_fake_score
        ),
        "total_frames": total_frames,
        "analyzed_frames": analyzed_frames,
        "fake_frames": fake_frames,
        "real_frames": real_frames,
        "fake_ratio": fake_ratio * 100,
        "suspicious_frames": suspicious_frames
    }