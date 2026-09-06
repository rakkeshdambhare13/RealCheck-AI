import torch
import torch.nn as nn
import numpy as np
import cv2

from torchvision import models
from PIL import Image


class GradCAM:

    def __init__(self, model, target_layer):

        self.model = model
        self.target_layer = target_layer

        self.activations = None
        self.gradients = None

        target_layer.register_forward_hook(
            self.save_activation
        )

        target_layer.register_full_backward_hook(
            self.save_gradient
        )

    def save_activation(self, module, input, output):

        self.activations = output.detach()

    def save_gradient(self, module, grad_input, grad_output):

        self.gradients = grad_output[0].detach()

    def generate(self, image_tensor, target_class):

        self.model.zero_grad()

        output = self.model(image_tensor)

        score = output[0, target_class]

        score.backward()

        activations = self.activations[0]

        gradients = self.gradients[0]

        # Global average pooling of gradients
        weights = gradients.mean(
            dim=(1, 2)
        )

        cam = torch.zeros(
            activations.shape[1:],
            device=activations.device
        )

        for i, weight in enumerate(weights):

            cam += weight * activations[i]

        cam = torch.relu(cam)

        cam -= cam.min()

        if cam.max() != 0:

            cam /= cam.max()

        cam = cam.cpu().numpy()

        return cam


def create_gradcam_image(
    model,
    image,
    transform,
    target_class,
    device
):

    image_rgb = image.convert("RGB")

    image_tensor = transform(
        image_rgb
    ).unsqueeze(0).to(device)

    # EfficientNet-B0 final convolutional layer
    target_layer = model.features[-1]

    gradcam = GradCAM(
        model,
        target_layer
    )

    cam = gradcam.generate(
        image_tensor,
        target_class
    )

    original = np.array(
        image_rgb
    )

    height, width = original.shape[:2]

    cam = cv2.resize(
        cam,
        (width, height)
    )

    heatmap = np.uint8(
        255 * cam
    )

    heatmap = cv2.applyColorMap(
        heatmap,
        cv2.COLORMAP_JET
    )

    heatmap = cv2.cvtColor(
        heatmap,
        cv2.COLOR_BGR2RGB
    )

    overlay = cv2.addWeighted(
        original,
        0.55,
        heatmap,
        0.45,
        0
    )

    return Image.fromarray(overlay)