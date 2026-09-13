import os
import json
import numpy as np
import pandas as pd
from PIL import Image

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
from torchvision.models import mobilenet_v3_small
from sklearn.metrics import brier_score_loss

SPLITS_PATH = "ml/data/splits/domain_gate_v2_splits.csv"
MODEL_V2_PATH = "ml/models/domain_gate_v2_best.pt"

CALIBRATION_JSON = "ml/artifacts/domain_gate_v2_calibration.json"
THRESHOLD_CSV = "ml/artifacts/domain_gate_v2_threshold_analysis.csv"

class DomainGateDatasetV2(Dataset):
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

def compute_ece(probs, labels, n_bins=10):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower, bin_upper = bin_boundaries[i], bin_boundaries[i+1]
        in_bin = (probs >= bin_lower) & (probs < bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(labels[in_bin])
            avg_confidence_in_bin = np.mean(probs[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin
    return float(ece)

class TemperatureScaler(nn.Module):
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits):
        return logits / self.temperature

    def fit(self, logits, labels):
        optimizer = optim.LBFGS([self.temperature], lr=0.01, max_iter=50)
        criterion = nn.BCEWithLogitsLoss()

        def eval_loss():
            optimizer.zero_grad()
            loss = criterion(self.forward(logits), labels)
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        return float(self.temperature.item())

def calibrate_and_analyze_thresholds():
    device = torch.device('mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu'))
    print(f"Calibrating Domain Gate V2 on device '{device}' using VALIDATION split...")
    
    df_splits = pd.read_csv(SPLITS_PATH)
    df_val = df_splits[df_splits['split'] == 'VAL'].reset_index(drop=True)
    
    transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_dataset = DomainGateDatasetV2(df_val, transform=transform)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    # Load V2 Model Checkpoint
    checkpoint = torch.load(MODEL_V2_PATH, map_location=device)
    model = mobilenet_v3_small()
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, 1)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    val_logits = []
    val_labels = []
    
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            logits = model(images)
            val_logits.extend(logits.cpu().numpy().flatten())
            val_labels.extend(labels.numpy().flatten())
            
    val_logits_t = torch.tensor(val_logits, dtype=torch.float32).unsqueeze(1)
    val_labels_t = torch.tensor(val_labels, dtype=torch.float32).unsqueeze(1)
    
    uncalibrated_probs = torch.sigmoid(val_logits_t).numpy().flatten()
    val_labels_np = np.array(val_labels)
    
    uncal_ece = compute_ece(uncalibrated_probs, val_labels_np)
    uncal_brier = float(brier_score_loss(val_labels_np, uncalibrated_probs))
    
    # Temperature Scaling
    scaler = TemperatureScaler()
    optimal_temp = scaler.fit(val_logits_t, val_labels_t)
    
    calibrated_logits = val_logits_t / optimal_temp
    calibrated_probs = torch.sigmoid(calibrated_logits).detach().numpy().flatten()
    
    cal_ece = compute_ece(calibrated_probs, val_labels_np)
    cal_brier = float(brier_score_loss(val_labels_np, calibrated_probs))
    
    print(f"\n--- CALIBRATION METRICS (VALIDATION SPLIT) ---")
    print(f"Optimal Temperature Scale (T): {optimal_temp:.4f}")
    print(f"Uncalibrated ECE: {uncal_ece:.4f} | Brier Score: {uncal_brier:.4f}")
    print(f"Calibrated ECE:   {cal_ece:.4f} | Brier Score: {cal_brier:.4f}")
    
    # Save Calibration Artifact
    calib_meta = {
        'model_version': 'mobilenet_v3_small_domain_gate_v2',
        'calibration_method': 'Temperature Scaling',
        'optimal_temperature_T': round(optimal_temp, 4),
        'uncalibrated': {
            'expected_calibration_error_ece': round(uncal_ece, 4),
            'brier_score': round(uncal_brier, 4)
        },
        'calibrated': {
            'expected_calibration_error_ece': round(cal_ece, 4),
            'brier_score': round(cal_brier, 4)
        }
    }
    
    with open(CALIBRATION_JSON, 'w') as f:
        json.dump(calib_meta, f, indent=2)
        
    # Threshold Analysis Sweep on Validation Set
    candidate_compatible = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    candidate_incompatible = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    
    threshold_records = []
    
    total_pos = (val_labels_np == 1).sum()
    total_neg = (val_labels_np == 0).sum()
    
    for c_thresh in candidate_compatible:
        for i_thresh in candidate_incompatible:
            if i_thresh >= c_thresh:
                continue
                
            n_pos_comp = ((val_labels_np == 1) & (calibrated_probs >= c_thresh)).sum()
            n_pos_incomp = ((val_labels_np == 1) & (calibrated_probs <= i_thresh)).sum()
            n_pos_uncert = ((val_labels_np == 1) & (calibrated_probs > i_thresh) & (calibrated_probs < c_thresh)).sum()
            
            n_neg_comp = ((val_labels_np == 0) & (calibrated_probs >= c_thresh)).sum()
            n_neg_incomp = ((val_labels_np == 0) & (calibrated_probs <= i_thresh)).sum()
            n_neg_uncert = ((val_labels_np == 0) & (calibrated_probs > i_thresh) & (calibrated_probs < c_thresh)).sum()
            
            astro_recall = n_pos_comp / total_pos if total_pos > 0 else 0.0
            non_astro_spec = n_neg_incomp / total_neg if total_neg > 0 else 0.0
            far = n_neg_comp / total_neg if total_neg > 0 else 0.0
            frr = n_pos_incomp / total_pos if total_pos > 0 else 0.0
            uncertain_rate = (n_pos_uncert + n_neg_uncert) / len(val_labels_np)
            
            threshold_records.append({
                'compatible_threshold': c_thresh,
                'incompatible_threshold': i_thresh,
                'astronomy_recall': round(astro_recall, 4),
                'non_astronomy_specificity': round(non_astro_spec, 4),
                'false_acceptance_rate': round(far, 4),
                'false_rejection_rate': round(frr, 4),
                'uncertain_rate': round(uncertain_rate, 4)
            })
            
    df_thresh = pd.DataFrame(threshold_records)
    df_thresh.to_csv(THRESHOLD_CSV, index=False)
    print(f"Saved threshold analysis sweep ({len(df_thresh)} combinations) to {THRESHOLD_CSV}")

if __name__ == '__main__':
    calibrate_and_analyze_thresholds()
