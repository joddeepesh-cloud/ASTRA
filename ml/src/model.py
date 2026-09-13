import torch
import torch.nn as nn
import torchvision.models as models

class GalaxyZooMultiHeadCNN(nn.Module):
    def __init__(self, backbone_name: str = 'efficientnet_b0', num_classes: int = 4, num_attributes: int = 6, pretrained: bool = True):
        super().__init__()
        self.backbone_name = backbone_name
        self.num_classes = num_classes
        self.num_attributes = num_attributes
        
        if backbone_name == 'efficientnet_b0':
            weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
            base_model = models.efficientnet_b0(weights=weights)
            # Remove original classifier
            self.features = base_model.features
            self.pool = nn.AdaptiveAvgPool2d(1)
            embedding_dim = 1280
        elif backbone_name == 'resnet18':
            weights = models.ResNet18_Weights.DEFAULT if pretrained else None
            base_model = models.resnet18(weights=weights)
            # Features up to avgpool
            self.features = nn.Sequential(*list(base_model.children())[:-1])
            self.pool = nn.Identity()
            embedding_dim = 512
        else:
            raise ValueError(f"Unsupported backbone: {backbone_name}")
            
        self.embedding_dim = embedding_dim
        
        # Classification Head (Morphology 4-class)
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(embedding_dim, 256),
            nn.BatchNorm1d(256),
            nn.SiLU() if backbone_name == 'efficientnet_b0' else nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes)
        )
        
        # Attribute Regression Head (6 continuous debiased vote fractions)
        self.attribute_regressor = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(embedding_dim, 128),
            nn.BatchNorm1d(128),
            nn.SiLU() if backbone_name == 'efficientnet_b0' else nn.ReLU(),
            nn.Linear(128, num_attributes),
            nn.Sigmoid()  # Clamp to [0, 1] range
        )

    def extract_embedding(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.features(x)
        pooled = self.pool(feat)
        flattened = torch.flatten(pooled, 1)
        return flattened

    def forward(self, x: torch.Tensor):
        embedding = self.extract_embedding(x)
        class_logits = self.classifier(embedding)
        attribute_probs = self.attribute_regressor(embedding)
        return class_logits, attribute_probs, embedding

    def unfreeze_upper_layers(self):
        """Unfreeze upper layers for fine-tuning"""
        if self.backbone_name == 'efficientnet_b0':
            # Unfreeze blocks 5, 6, 7 and features head
            for param in self.features.parameters():
                param.requires_grad = True
        elif self.backbone_name == 'resnet18':
            for param in self.features.parameters():
                param.requires_grad = True

    def freeze_backbone(self):
        """Freeze backbone for Phase 1 head warm-up"""
        for param in self.features.parameters():
            param.requires_grad = False
