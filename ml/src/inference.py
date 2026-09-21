import os
import gc
import time
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np

from ml.src.model import GalaxyZooMultiHeadCNN
from ml.src.galaxy_zoo_dataset import IDX_TO_CLASS, ATTRIBUTE_COLS

class GalaxyZooInference:
    """
    Standalone Production Inference Module for ASTRA Galaxy Zoo Multi-Head CNN.
    
    Provides single-image morphology classification, continuous scientific attribute estimation,
    1280-dimensional latent embedding extraction, and inference timing metrics.
    """
    def __init__(self, model_path: str = None, device: str = None):
        if model_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            model_path = os.path.join(project_root, "ml", "models", "best_model.pt")
            
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model checkpoint not found at: {model_path}")
            
        if device is None:
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        # Load checkpoint
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
        self.backbone_name = checkpoint.get("backbone", "efficientnet_b0")
        self.num_classes = checkpoint.get("num_classes", 4)
        self.idx_to_class = checkpoint.get("idx_to_class", IDX_TO_CLASS)
        self.attribute_cols = checkpoint.get("attribute_cols", ATTRIBUTE_COLS)
        self.embedding_dim = checkpoint.get("embedding_dim", 1280)
        self.model_epoch = checkpoint.get("epoch", 10)

        # Instantiate model architecture and load weights
        self.model = GalaxyZooMultiHeadCNN(
            backbone_name=self.backbone_name,
            num_classes=self.num_classes,
            num_attributes=len(self.attribute_cols),
            pretrained=False
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()
        for p in self.model.parameters():
            p.requires_grad = False
        input_size = checkpoint.get("input_size", (224, 224))
        norm_config = checkpoint.get("norm_config", {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]})

        # Define canonical image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize(input_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=norm_config["mean"], std=norm_config["std"])
        ])

        del checkpoint
        gc.collect()

    @torch.inference_mode()
    def predict_single_image(self, image_input) -> dict:
        """
        Run inference on a single image.
        
        :param image_input: File path string, PIL Image object, or numpy array.
        :return: Dict containing:
            - predicted_class: str
            - class_confidence: float
            - class_probabilities: dict[str, float]
            - scientific_attributes: dict[str, float]
            - embedding: np.ndarray (shape 1280,)
            - inference_time_ms: float
        """
        t0 = time.perf_counter()

        if isinstance(image_input, str):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, np.ndarray):
            img = Image.fromarray(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        tensor_img = self.transform(img).unsqueeze(0).to(self.device)

        cls_logits, attr_probs, embedding = self.model(tensor_img)
        probs = torch.softmax(cls_logits, dim=1).squeeze(0).cpu().numpy()
        attr_vals = attr_probs.squeeze(0).cpu().numpy()
        emb_arr = embedding.squeeze(0).cpu().numpy()

        t1 = time.perf_counter()
        inference_time_ms = round((t1 - t0) * 1000.0, 3)

        pred_idx = int(np.argmax(probs))
        pred_class = self.idx_to_class[pred_idx]
        confidence = float(probs[pred_idx])

        class_probs_dict = {self.idx_to_class[i]: float(probs[i]) for i in range(self.num_classes)}
        scientific_attrs_dict = {col: float(attr_vals[i]) for i, col in enumerate(self.attribute_cols)}

        return {
            "predicted_class": pred_class,
            "class_confidence": round(confidence, 4),
            "class_probabilities": {k: round(v, 4) for k, v in class_probs_dict.items()},
            "scientific_attributes": {k: round(v, 4) for k, v in scientific_attrs_dict.items()},
            "embedding": emb_arr,
            "inference_time_ms": inference_time_ms
        }
