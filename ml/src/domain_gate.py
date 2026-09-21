import os
import io
import gc
import time
import torch
import torch.nn as nn
from PIL import Image
import torchvision.transforms as T
from torchvision.models import mobilenet_v3_small

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "domain_gate_v2_best.pt")

class DomainGate:
    """
    Standalone Astronomy Domain Compatibility Gate for ASTRA (V2 Production).
    Estimates whether an input image is visually compatible with astronomical
    observation imagery before performing Galaxy Zoo morphology classification.
    """
    def __init__(self, model_path=None, device=None, compatible_threshold=0.80, incompatible_threshold=0.20):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Domain Gate model checkpoint missing: {self.model_path}")
            
        if device is None:
            self.device = torch.device('mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu'))
        else:
            self.device = torch.device(device)
            
        self.compatible_threshold = compatible_threshold
        self.incompatible_threshold = incompatible_threshold
        
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self._load_model()

    def _load_model(self):
        t0 = time.time()
        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=True)
        
        self.model = mobilenet_v3_small()
        in_features = self.model.classifier[3].in_features
        self.model.classifier[3] = nn.Linear(in_features, 1)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()
        for p in self.model.parameters():
            p.requires_grad = False
        
        self.temperature = float(checkpoint.get('temperature', 1.4996))
        ckpt_version = str(checkpoint.get('model_version', 'mobilenet_v3_small_domain_gate_v2'))
        if "v2" not in ckpt_version:
            ckpt_version = "mobilenet_v3_small_domain_gate_v2"
        self.model_version = ckpt_version
        del checkpoint
        gc.collect()
        self.load_duration_ms = (time.time() - t0) * 1000.0

    def predict(self, image_input):
        """
        Predict domain compatibility for an image with temperature-scaled probabilities.
        image_input can be a filepath (str), PIL Image, or raw bytes.
        """
        t0 = time.time()
        
        if isinstance(image_input, str):
            with Image.open(image_input) as img:
                pil_img = img.convert('RGB')
        elif isinstance(image_input, bytes):
            with Image.open(io.BytesIO(image_input)) as img:
                pil_img = img.convert('RGB')
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert('RGB')
        else:
            raise ValueError("Unsupported image input type. Provide filepath, PIL Image, or bytes.")
            
        tensor_img = self.transform(pil_img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logit = self.model(tensor_img)
            scaled_logit = logit / self.temperature
            prob_astro = float(torch.sigmoid(scaled_logit).cpu().numpy()[0][0])
            
        prob_non_astro = float(1.0 - prob_astro)
        
        # Exact boundary threshold policy
        if prob_astro >= self.compatible_threshold:
            decision = "COMPATIBLE"
        elif prob_astro <= self.incompatible_threshold:
            decision = "INCOMPATIBLE"
        else:
            decision = "UNCERTAIN"
            
        inf_ms = (time.time() - t0) * 1000.0
        
        return {
            'probability_astronomical': round(prob_astro, 4),
            'probability_non_astronomical': round(prob_non_astro, 4),
            'decision': decision,
            'thresholds': {
                'compatible_threshold': self.compatible_threshold,
                'incompatible_threshold': self.incompatible_threshold
            },
            'temperature_scale': round(self.temperature, 4),
            'model_version': self.model_version,
            'inference_time_ms': round(inf_ms, 2)
        }
