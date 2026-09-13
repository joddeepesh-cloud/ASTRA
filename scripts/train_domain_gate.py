import os
import json
import random
import time
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc
)

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights

MANIFEST_PATH = "ml/data/domain_gate_manifest.csv"
BEST_MODEL_PATH = "ml/models/domain_gate_best.pt"
LATEST_MODEL_PATH = "ml/models/domain_gate_latest.pt"
HISTORY_PATH = "ml/artifacts/domain_gate_history.json"

# Set Seeds for Reproducibility
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class DomainGateDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = row['path']
        label = 1.0 if row['domain_label'] == 'ASTRONOMICAL' else 0.0
        
        with Image.open(img_path) as img:
            img = img.convert('RGB')
            if self.transform:
                img = self.transform(img)
                
        return img, torch.tensor(label, dtype=torch.float32)

def get_transforms():
    train_transform = T.Compose([
        T.Resize((224, 224)),
        T.RandomHorizontalFlip(p=0.5),
        T.RandomRotation(degrees=10),
        T.ColorJitter(brightness=0.1, contrast=0.1),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    eval_transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, eval_transform

def evaluate_metrics(y_true, y_probs, threshold=0.5):
    y_pred = (y_probs >= threshold).astype(int)
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    try:
        roc = roc_auc_score(y_true, y_probs)
    except Exception:
        roc = 0.5
        
    p_prec, p_rec, _ = precision_recall_curve(y_true, y_probs)
    pr_auc = auc(p_rec, p_prec)
    
    # Class-specific recalls
    astro_mask = (y_true == 1)
    non_astro_mask = (y_true == 0)
    
    astro_rec = recall_score(y_true[astro_mask], y_pred[astro_mask], zero_division=0) if astro_mask.sum() > 0 else 0.0
    non_astro_spec = recall_score(1 - y_true[non_astro_mask], 1 - y_pred[non_astro_mask], zero_division=0) if non_astro_mask.sum() > 0 else 0.0
    
    return {
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1': float(f1),
        'roc_auc': float(roc),
        'pr_auc': float(pr_auc),
        'astronomy_recall': float(astro_rec),
        'non_astronomy_specificity': float(non_astro_spec)
    }

def train_model():
    set_seed(42)
    os.makedirs("ml/models", exist_ok=True)
    os.makedirs("ml/artifacts", exist_ok=True)
    
    device = torch.device('mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu'))
    print(f"Using compute device: '{device}'")
    
    df_manifest = pd.read_csv(MANIFEST_PATH)
    
    # Strictly exclude AMBIGUOUS / REVIEW split from training
    df_train = df_manifest[df_manifest['split'] == 'TRAIN']
    df_val = df_manifest[df_manifest['split'] == 'VAL']
    
    print(f"Loaded datasets -> Train: {len(df_train)}, Val: {len(df_val)} (Test & Review held out).")
    
    train_tf, eval_tf = get_transforms()
    
    train_dataset = DomainGateDataset(df_train, transform=train_tf)
    val_dataset = DomainGateDataset(df_val, transform=eval_tf)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)
    
    # Initialize MobileNetV3-Small
    weights = MobileNet_V3_Small_Weights.DEFAULT
    model = mobilenet_v3_small(weights=weights)
    
    # Replace classification head for binary classification (1 output logit)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, 1)
    
    model = model.to(device)
    criterion = nn.BCEWithLogitsLoss()
    
    # Phase 1: Freeze backbone, train classifier head (Epochs 1-5)
    for name, param in model.named_parameters():
        if "classifier" not in name:
            param.requires_grad = False
            
    optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3, weight_decay=1e-2)
    
    epochs_phase1 = 5
    epochs_phase2 = 10
    total_epochs = epochs_phase1 + epochs_phase2
    
    history = []
    best_val_roc = 0.0
    
    print("\nStarting Training Pipeline (Phase 1: Frozen Backbone, Phase 2: End-to-End Fine-Tuning)...")
    
    for epoch in range(1, total_epochs + 1):
        if epoch == epochs_phase1 + 1:
            print("\n--- Transitioning to Phase 2: Unfreezing Backbone for Fine-Tuning ---")
            for param in model.parameters():
                param.requires_grad = True
            optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-2)
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs_phase2, eta_min=1e-6)
        
        start_t = time.time()
        model.train()
        train_loss_sum = 0.0
        train_preds, train_targets = [], []
        
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device).unsqueeze(1)
            
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            
            train_loss_sum += loss.item() * len(labels)
            probs = torch.sigmoid(logits).detach().cpu().numpy().flatten()
            train_preds.extend(probs)
            train_targets.extend(labels.cpu().numpy().flatten())
            
        if epoch > epochs_phase1:
            scheduler.step()
            
        train_loss = train_loss_sum / len(train_dataset)
        train_metrics = evaluate_metrics(np.array(train_targets), np.array(train_preds))
        
        # Validation Pass (VAL dataset only)
        model.eval()
        val_loss_sum = 0.0
        val_preds, val_targets = [], []
        
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device).unsqueeze(1)
                logits = model(images)
                loss = criterion(logits, labels)
                
                val_loss_sum += loss.item() * len(labels)
                probs = torch.sigmoid(logits).cpu().numpy().flatten()
                val_preds.extend(probs)
                val_targets.extend(labels.cpu().numpy().flatten())
                
        val_loss = val_loss_sum / len(val_dataset)
        val_metrics = evaluate_metrics(np.array(val_targets), np.array(val_preds))
        epoch_ms = (time.time() - start_t) * 1000
        
        print(f"Epoch {epoch:02d}/{total_epochs:02d} ({epoch_ms:.0f}ms) | "
              f"Train Loss: {train_loss:.4f}, Acc: {train_metrics['accuracy']*100:.1f}% | "
              f"Val Loss: {val_loss:.4f}, Acc: {val_metrics['accuracy']*100:.1f}%, "
              f"ROC-AUC: {val_metrics['roc_auc']:.4f}, Astro Rec: {val_metrics['astronomy_recall']*100:.1f}%", flush=True)
        
        epoch_record = {
            'epoch': epoch,
            'train_loss': train_loss,
            'train_metrics': train_metrics,
            'val_loss': val_loss,
            'val_metrics': val_metrics,
            'duration_ms': epoch_ms
        }
        history.append(epoch_record)
        
        # Checkpoint Saving
        checkpoint_meta = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'architecture': 'mobilenet_v3_small',
            'num_classes': 1,
            'val_metrics': val_metrics,
            'val_loss': val_loss,
            'model_version': f"mobilenet_v3_small_domain_gate_epoch{epoch}"
        }
        
        torch.save(checkpoint_meta, LATEST_MODEL_PATH)
        
        if val_metrics['roc_auc'] >= best_val_roc:
            best_val_roc = val_metrics['roc_auc']
            torch.save(checkpoint_meta, BEST_MODEL_PATH)
            print(f"  [SAVED] New best validation checkpoint (ROC-AUC: {best_val_roc:.4f}) -> {BEST_MODEL_PATH}", flush=True)
            
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)
        
    print(f"\nTraining Complete! Best Validation ROC-AUC: {best_val_roc:.4f}")

if __name__ == '__main__':
    train_model()
