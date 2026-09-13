import sys
import os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import time
import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, mean_absolute_error, mean_squared_error

from ml.src.galaxy_zoo_dataset import GalaxyZooDataset, CLASS_TO_IDX, IDX_TO_CLASS, ATTRIBUTE_COLS
from ml.src.model import GalaxyZooMultiHeadCNN

def print_log(msg):
    print(msg, flush=True)

def parse_args():
    parser = argparse.ArgumentParser(description="ASTRA Galaxy Zoo Multi-Head CNN Training & Resumption")
    parser.add_argument('--resume', type=str, nargs='?', const='DEFAULT_RESUME', default=None,
                        help="Path to checkpoint to resume training from (default: latest_model.pt if exists, else best_model.pt)")
    parser.add_argument('--end-epoch', type=int, default=None,
                        help="Ending epoch number for a resumed or constrained run (e.g. --end-epoch 11)")
    parser.add_argument('--dry-run', action='store_true',
                        help="Perform lightweight verification of checkpoint, model, optimizer, and scheduler without training")
    parser.add_argument('--skip-final-eval', action='store_true',
                        help="Skip post-training test set evaluation and 10k embedding extraction for intermediate runs")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print_log("=" * 60)
    print_log("ASTRA — GALAXY ZOO MULTI-HEAD CNN TRAINING & EVALUATION")
    print_log("=" * 60)
    
    # 1. Device Setup
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print_log("Using Device: Apple Silicon MPS (Metal Performance Shaders)")
    else:
        device = torch.device("cpu")
        print_log("Using Device: CPU")
        
    print_log(f"PyTorch Version: {torch.__version__}")
    
    # 2. File Paths
    project_root = os.getcwd()
    csv_path = os.path.join(project_root, "ml/data/splits/subset_10k_scientific_targets.csv")
    img_dir = os.path.join(project_root, "ml/data/processed/galaxy_zoo/images")
    models_dir = os.path.join(project_root, "ml/models")
    artifacts_dir = os.path.join(project_root, "ml/artifacts")
    docs_dir = os.path.join(project_root, "docs")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    best_model_path = os.path.join(models_dir, "best_model.pt")
    latest_model_path = os.path.join(models_dir, "latest_model.pt")
    metrics_path = os.path.join(artifacts_dir, "galaxy_zoo_metrics.json")
    cm_path = os.path.join(artifacts_dir, "galaxy_zoo_confusion_matrix.png")
    emb_npy_path = os.path.join(artifacts_dir, "galaxy_zoo_embeddings.npy")
    emb_idx_path = os.path.join(artifacts_dir, "galaxy_zoo_embedding_index.csv")
    doc_path = os.path.join(docs_dir, "galaxy_zoo_training.md")

    # 3. Data Transformations
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # 4. Datasets & DataLoaders
    print_log("Loading Datasets...")
    train_dataset = GalaxyZooDataset(csv_path, img_dir, split='train', transform=train_transform)
    val_dataset = GalaxyZooDataset(csv_path, img_dir, split='val', transform=eval_transform)
    test_dataset = GalaxyZooDataset(csv_path, img_dir, split='test', transform=eval_transform)
    full_dataset = GalaxyZooDataset(csv_path, img_dir, split=None, transform=eval_transform)
    
    batch_size = 64
    num_workers = 0
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    full_loader = DataLoader(full_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    
    print_log(f"Dataset Counts -> Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}, Total: {len(full_dataset)}")
    
    # 5. Model, Loss Functions
    backbone_name = 'efficientnet_b0'
    model = GalaxyZooMultiHeadCNN(backbone_name=backbone_name, num_classes=4, num_attributes=6, pretrained=True).to(device)
    
    criterion_cls = nn.CrossEntropyLoss()
    criterion_attr = nn.SmoothL1Loss()
    attr_weight = 0.25
    
    # ORIGINAL 15-EPOCH PLAN HYPERPARAMETERS
    phase1_epochs = 3
    phase2_epochs = 12
    total_epochs = phase1_epochs + phase2_epochs
    
    start_epoch = 1
    completed_epoch = 0
    best_val_loss = float('inf')
    best_val_macro_f1 = 0.0
    best_epoch = 1
    checkpoint = None

    # Resumption Setup
    resume_path = args.resume
    if resume_path == 'DEFAULT_RESUME':
        resume_path = latest_model_path if os.path.exists(latest_model_path) else best_model_path

    if resume_path is not None:
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Resume checkpoint not found: {resume_path}")
            
        print_log(f"\n---> Loading Checkpoint for Resumption: {resume_path}")
        checkpoint = torch.load(resume_path, map_location=device)
        
        # Verify architecture parameters match
        ck_backbone = checkpoint.get('backbone', 'efficientnet_b0')
        ck_num_classes = checkpoint.get('num_classes', 4)
        if ck_backbone != backbone_name or ck_num_classes != 4:
            raise ValueError(f"Checkpoint architecture mismatch: {ck_backbone} vs {backbone_name}")
            
        # Load weights
        model.load_state_dict(checkpoint['model_state_dict'])
        
        completed_epoch = checkpoint.get('epoch', 0)
        start_epoch = completed_epoch + 1
        
        # Maintain historical best validation loss benchmark from best_model.pt if available
        if os.path.exists(best_model_path):
            best_ckpt = torch.load(best_model_path, map_location='cpu')
            best_val_loss = best_ckpt.get('val_loss', float('inf'))
            best_val_macro_f1 = best_ckpt.get('val_macro_f1', 0.0)
            best_epoch = best_ckpt.get('epoch', 0)
        else:
            best_val_loss = checkpoint.get('val_loss', float('inf'))
            best_val_macro_f1 = checkpoint.get('val_macro_f1', 0.0)
            best_epoch = completed_epoch
        
        print_log(f"Successfully loaded model weights from Completed Epoch {completed_epoch}")
        print_log(f"Checkpoint Metrics -> Val Loss: {checkpoint.get('val_loss', float('inf')):.4f}, Val Acc: {checkpoint.get('val_acc', 0.0)*100:.2f}%, Val F1: {checkpoint.get('val_macro_f1', 0.0):.4f}")
        print_log(f"Current Best Val Loss Benchmark: {best_val_loss:.4f} (from Epoch {best_epoch})")

    # Constrained ending epoch if specified (e.g. --end-epoch 11)
    target_end_epoch = args.end_epoch if args.end_epoch is not None else total_epochs

    # Set up Optimizer based on starting phase
    if start_epoch > phase1_epochs:
        print_log(f"---> Phase 2 Fine-Tuning Active (Unfrozen Backbone)")
        model.unfreeze_upper_layers()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    else:
        print_log(f"---> Phase 1 Head Warmup Active (Frozen Backbone)")
        model.freeze_backbone()
        optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3, weight_decay=1e-4)
        
    optimizer_restored = False
    if resume_path is not None and 'optimizer_state_dict' in checkpoint:
        try:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            optimizer_restored = True
            print_log("Successfully restored optimizer state dict.")
        except Exception as e:
            print_log(f"Warning: Could not restore optimizer state dict ({e}). Continuing with fresh optimizer.")

    # RECONSTRUCT ORIGINAL 15-EPOCH SCHEDULER TRAJECTORY
    if start_epoch > phase1_epochs:
        phase2_base_lr = 1e-4
        # Restore initial_lr and lr in param_groups before creating CosineAnnealingLR
        for group in optimizer.param_groups:
            group['lr'] = phase2_base_lr
            group['initial_lr'] = phase2_base_lr

        # Phase 2 CosineAnnealingLR for original 12 phase2_epochs (Epochs 4 to 15)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=phase2_epochs)
        
        if resume_path is not None and 'scheduler_state_dict' in checkpoint and checkpoint['scheduler_state_dict'] is not None:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            print_log("Successfully loaded scheduler_state_dict from checkpoint.")
        else:
            # Deterministically reconstruct scheduler state for completed Phase 2 steps
            completed_phase2_steps = completed_epoch - phase1_epochs  # e.g. 6 - 3 = 3
            for _ in range(completed_phase2_steps):
                scheduler.step()
            print_log(f"Reconstructed original 15-epoch Phase 2 scheduler (stepped {completed_phase2_steps} times for completed Epoch {completed_epoch}).")
    else:
        phase1_base_lr = 1e-3
        for group in optimizer.param_groups:
            group['lr'] = phase1_base_lr
            group['initial_lr'] = phase1_base_lr

        # Phase 1 CosineAnnealingLR for original 3 phase1_epochs
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=phase1_epochs)
        if resume_path is not None and 'scheduler_state_dict' in checkpoint and checkpoint['scheduler_state_dict'] is not None:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        else:
            for _ in range(completed_epoch):
                scheduler.step()

    next_epoch_lr = scheduler.get_last_lr()[0]
    print_log(f"Learning rate ready for Epoch {start_epoch}: {next_epoch_lr:.6e}")

    # 6. Dry-Run Verification Mode
    if args.dry_run:
        print_log("\n" + "=" * 60)
        print_log("[DRY-RUN VERIFICATION SUCCESSFUL]")
        print_log(f"Checkpoint Loaded: {resume_path if resume_path else 'None'}")
        print_log(f"Completed Epoch in Checkpoint: EPOCH {completed_epoch}")
        print_log(f"Resumption Starting Epoch: EPOCH {start_epoch}")
        print_log(f"Target Ending Epoch for Run: EPOCH {target_end_epoch}")
        print_log(f"Total Planned Epochs (Original Plan): {total_epochs}")
        print_log(f"Optimizer Restored: {'Yes' if optimizer_restored else 'Fresh'}")
        print_log(f"Scheduler Trajectory: Original 15-Epoch Schedule (Phase 2 T_max={phase2_epochs})")
        print_log(f"Learning Rate for Epoch {start_epoch}: {next_epoch_lr:.6e}")
        print_log(f"Current Best Val Loss Benchmark: {best_val_loss:.4f}")
        print_log(f"Skip Final Eval Flag: {'Enabled' if args.skip_final_eval else 'Disabled'}")
        print_log(f"No dataset/model modifications or heavy GPU compute performed.")
        print_log("=" * 60)
        return

    # 7. Execute Training Loop
    print_log(f"\n" + "=" * 60)
    print_log(f"RESUMING FROM EPOCH {start_epoch} UP TO EPOCH {target_end_epoch} (ORIGINAL 15-EPOCH PLAN)")
    print_log("=" * 60 + "\n")
    
    start_time = time.time()
    
    for epoch in range(start_epoch, target_end_epoch + 1):
        if epoch == phase1_epochs + 1 and start_epoch <= phase1_epochs:
            print_log("\n---> Transitioning to Phase 2: Unfreezing backbone for fine-tuning...")
            model.unfreeze_upper_layers()
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=phase2_epochs)
            
        model.train()
        running_cls_loss = 0.0
        running_attr_loss = 0.0
        running_total_loss = 0.0
        correct_cls = 0
        total_samples = 0
        
        epoch_start = time.time()
        for batch_idx, batch in enumerate(train_loader):
            imgs = batch['image'].to(device)
            cls_targets = batch['class_target'].to(device)
            attr_targets = batch['attribute_targets'].to(device)
            
            optimizer.zero_grad()
            cls_logits, attr_probs, _ = model(imgs)
            
            loss_c = criterion_cls(cls_logits, cls_targets)
            loss_a = criterion_attr(attr_probs, attr_targets)
            loss = loss_c + attr_weight * loss_a
            
            loss.backward()
            optimizer.step()
            
            running_cls_loss += loss_c.item() * imgs.size(0)
            running_attr_loss += loss_a.item() * imgs.size(0)
            running_total_loss += loss.item() * imgs.size(0)
            
            preds = torch.argmax(cls_logits, dim=1)
            correct_cls += (preds == cls_targets).sum().item()
            total_samples += imgs.size(0)
            
        scheduler.step()
        
        train_cls_loss = running_cls_loss / total_samples
        train_attr_loss = running_attr_loss / total_samples
        train_total_loss = running_total_loss / total_samples
        train_acc = correct_cls / total_samples
        
        # Validation Step
        model.eval()
        val_cls_loss = 0.0
        val_attr_loss = 0.0
        val_total_loss = 0.0
        val_preds_list = []
        val_targets_list = []
        val_samples = 0
        
        with torch.no_grad():
            for batch in val_loader:
                imgs = batch['image'].to(device)
                cls_targets = batch['class_target'].to(device)
                attr_targets = batch['attribute_targets'].to(device)
                
                cls_logits, attr_probs, _ = model(imgs)
                
                loss_c = criterion_cls(cls_logits, cls_targets)
                loss_a = criterion_attr(attr_probs, attr_targets)
                loss = loss_c + attr_weight * loss_a
                
                val_cls_loss += loss_c.item() * imgs.size(0)
                val_attr_loss += loss_a.item() * imgs.size(0)
                val_total_loss += loss.item() * imgs.size(0)
                
                preds = torch.argmax(cls_logits, dim=1)
                val_preds_list.extend(preds.cpu().numpy())
                val_targets_list.extend(cls_targets.cpu().numpy())
                val_samples += imgs.size(0)
                
        val_total_loss = val_total_loss / val_samples
        val_acc = accuracy_score(val_targets_list, val_preds_list)
        _, _, val_macro_f1, _ = precision_recall_fscore_support(val_targets_list, val_preds_list, average='macro', zero_division=0)
        
        epoch_sec = time.time() - epoch_start
        print_log(f"Epoch [{epoch:2d}/{total_epochs:2d}] ({epoch_sec:.1f}s) | Train Loss: {train_total_loss:.4f} (Acc: {train_acc*100:.2f}%) | Val Loss: {val_total_loss:.4f} (Acc: {val_acc*100:.2f}%, F1: {val_macro_f1:.4f})")
        
        # Save Latest Checkpoint at the end of EVERY completed epoch
        epoch_checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'val_loss': val_total_loss,
            'val_acc': val_acc,
            'val_macro_f1': val_macro_f1,
            'train_loss': train_total_loss,
            'train_acc': train_acc,
            'backbone': backbone_name,
            'embedding_dim': model.embedding_dim,
            'num_classes': 4,
            'class_to_idx': CLASS_TO_IDX,
            'idx_to_class': IDX_TO_CLASS,
            'attribute_cols': ATTRIBUTE_COLS,
            'input_size': (224, 224),
            'normalization': {'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225]}
        }
        torch.save(epoch_checkpoint, latest_model_path)
        print_log(f"---> Saved latest checkpoint for Epoch {epoch} to {latest_model_path}")
        
        # Save Best Checkpoint ONLY when validation loss improves below historical best benchmark
        if val_total_loss < best_val_loss:
            best_val_loss = val_total_loss
            best_val_macro_f1 = val_macro_f1
            best_epoch = epoch
            
            torch.save(epoch_checkpoint, best_model_path)
            print_log(f"---> Saved improved best checkpoint to {best_model_path} (Val Loss: {val_total_loss:.4f}, Val Acc: {val_acc*100:.2f}%)")
            
    training_duration = time.time() - start_time
    print_log(f"\nResumed Training Block Complete in {training_duration:.2f}s! Best Epoch: {best_epoch} (Val Loss: {best_val_loss:.4f}, Val Macro F1: {best_val_macro_f1:.4f})")

    # 8. Skip Final Evaluation & Embedding Extraction if requested for intermediate runs
    if args.skip_final_eval:
        print_log("\n" + "=" * 60)
        print_log("[SKIP-FINAL-EVAL] Skipping test set evaluation and 10k embedding extraction for this intermediate run.")
        print_log(f"Resumed training completed up to epoch {target_end_epoch}. Best model saved at {best_model_path}")
        print_log("=" * 60)
        return

    # 9. Evaluation on Untouched Test Set
    print_log("\n" + "=" * 60)
    print_log("EVALUATING BEST MODEL ON TEST SPLIT (1,000 SAMPLES)...")
    print_log("=" * 60)
    
    checkpoint = torch.load(best_model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    test_cls_preds = []
    test_cls_targets = []
    test_attr_preds = []
    test_attr_targets = []
    
    with torch.no_grad():
        for batch in test_loader:
            imgs = batch['image'].to(device)
            cls_targets = batch['class_target'].to(device)
            attr_targets = batch['attribute_targets'].to(device)
            
            cls_logits, attr_probs, _ = model(imgs)
            preds = torch.argmax(cls_logits, dim=1)
            
            test_cls_preds.extend(preds.cpu().numpy())
            test_cls_targets.extend(cls_targets.cpu().numpy())
            test_attr_preds.extend(attr_probs.cpu().numpy())
            test_attr_targets.extend(attr_targets.cpu().numpy())
            
    test_cls_preds = np.array(test_cls_preds)
    test_cls_targets = np.array(test_cls_targets)
    test_attr_preds = np.array(test_attr_preds)
    test_attr_targets = np.array(test_attr_targets)
    
    # Calculate Classification Metrics
    test_acc = accuracy_score(test_cls_targets, test_cls_preds)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(test_cls_targets, test_cls_preds, average='macro')
    prec_weighted, rec_weighted, f1_weighted, _ = precision_recall_fscore_support(test_cls_targets, test_cls_preds, average='weighted')
    
    prec_per_class, rec_per_class, f1_per_class, support_per_class = precision_recall_fscore_support(test_cls_targets, test_cls_preds, average=None)
    
    per_class_metrics = {}
    for idx, class_name in IDX_TO_CLASS.items():
        per_class_metrics[class_name] = {
            "precision": float(prec_per_class[idx]),
            "recall": float(rec_per_class[idx]),
            "f1_score": float(f1_per_class[idx]),
            "support": int(support_per_class[idx])
        }
        
    # Calculate Attribute Regression Metrics
    attr_mae_per_col = mean_absolute_error(test_attr_targets, test_attr_preds, multioutput='raw_values')
    attr_rmse_per_col = np.sqrt(mean_squared_error(test_attr_targets, test_attr_preds, multioutput='raw_values'))
    
    overall_attr_mae = float(mean_absolute_error(test_attr_targets, test_attr_preds))
    overall_attr_rmse = float(np.sqrt(mean_squared_error(test_attr_targets, test_attr_preds)))
    
    attribute_metrics = {}
    for i, col in enumerate(ATTRIBUTE_COLS):
        attribute_metrics[col] = {
            "mae": float(attr_mae_per_col[i]),
            "rmse": float(attr_rmse_per_col[i])
        }

    # Confusion Matrix
    cm = confusion_matrix(test_cls_targets, test_cls_preds)
    class_names = [IDX_TO_CLASS[i] for i in range(4)]
    
    # Save Metrics JSON
    metrics_json = {
        "dataset_summary": {
            "total_samples": len(full_dataset),
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset),
            "test_samples": len(test_dataset)
        },
        "training_metadata": {
            "date": datetime.datetime.now().isoformat(),
            "hardware": "Apple Silicon M4",
            "device": str(device),
            "pytorch_version": torch.__version__,
            "backbone": backbone_name,
            "best_epoch": best_epoch,
            "training_duration_seconds": round(training_duration, 2)
        },
        "test_classification_metrics": {
            "accuracy": float(test_acc),
            "macro_precision": float(prec_macro),
            "macro_recall": float(rec_macro),
            "macro_f1": float(f1_macro),
            "weighted_precision": float(prec_weighted),
            "weighted_recall": float(rec_weighted),
            "weighted_f1": float(f1_weighted),
            "per_class": per_class_metrics
        },
        "test_attribute_regression_metrics": {
            "overall_mae": overall_attr_mae,
            "overall_rmse": overall_attr_rmse,
            "per_attribute": attribute_metrics
        },
        "confusion_matrix": cm.tolist()
    }
    
    with open(metrics_path, "w") as f:
        json.dump(metrics_json, f, indent=2)
    print_log(f"Saved Test Metrics JSON to: {metrics_path}")
    
    # Plot & Save Confusion Matrix
    plt.figure(figsize=(7, 6))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Galaxy Zoo 2 Morphology Confusion Matrix')
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45, ha='right')
    plt.yticks(tick_marks, class_names)
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
            
    plt.tight_layout()
    plt.ylabel('True Morphology Label')
    plt.xlabel('Predicted Morphology Label')
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print_log(f"Saved Confusion Matrix Plot to: {cm_path}")
    
    # Print Test Results Summary
    print_log("\n" + "=" * 60)
    print_log(f"TEST ACCURACY:     {test_acc * 100:.2f}%")
    print_log(f"TEST MACRO F1:     {f1_macro:.4f}")
    print_log(f"TEST WEIGHTED F1:  {f1_weighted:.4f}")
    print_log(f"ATTRIBUTE MAE:     {overall_attr_mae:.4f}")
    print_log("=" * 60)

    # 10. Extract Latent Embeddings for Full 10,000 Dataset
    print_log("\n" + "=" * 60)
    print_log("EXTRACTING LATENT EMBEDDINGS FOR ALL 10,000 IMAGES...")
    print_log("=" * 60)
    
    all_embeddings = []
    with torch.no_grad():
        for batch in full_loader:
            imgs = batch['image'].to(device)
            embeddings = model.extract_embedding(imgs)
            all_embeddings.append(embeddings.cpu().numpy())

    full_df = full_dataset.df
    all_embeddings_arr = np.concatenate(all_embeddings, axis=0)
    
    np.save(emb_npy_path, all_embeddings_arr)
    print_log(f"Saved Embeddings Array to: {emb_npy_path} (Shape: {all_embeddings_arr.shape})")
    
    emb_idx_df = pd.DataFrame({
        'asset_id': full_df['asset_id'],
        'dr7objid': full_df['dr7objid'],
        'image_filename': full_df['image_filename'],
        'split': full_df['split'],
        'target_4class': full_df['target_4class'],
        'embedding_index': np.arange(len(full_df))
    })
    emb_idx_df.to_csv(emb_idx_path, index=False)
    print_log(f"Saved Embedding Index CSV to: {emb_idx_path}")

    # 11. Write Training Documentation
    doc_content = f"""# Galaxy Zoo 2 Multi-Head CNN Training Documentation

- **Date**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Hardware**: Apple Silicon M4
- **PyTorch Version**: {torch.__version__}
- **Device**: {device}
- **Dataset Counts**: Train: 8,000 | Validation: 1,000 | Test: 1,000 | Total: 10,000
- **Model Architecture**: Multi-Head CNN with `{backbone_name}` backbone
- **Embedding Dimension**: {model.embedding_dim}
- **Input Resolution**: 224 × 224 RGB

## Training Parameters
- **Optimizer**: AdamW
- **Scheduler**: CosineAnnealingLR
- **Batch Size**: {batch_size}
- **Total Epochs**: {total_epochs}
- **Best Epoch**: {best_epoch}

## Test Set Performance (Untouched 1,000 Samples)
- **Accuracy**: `{test_acc * 100:.2f}%`
- **Macro F1 Score**: `{f1_macro:.4f}`
- **Weighted F1 Score**: `{f1_weighted:.4f}`
- **Attribute MAE**: `{overall_attr_mae:.4f}`
- **Attribute RMSE**: `{overall_attr_rmse:.4f}`

## Artifacts Generated
- Model Checkpoint: `ml/models/best_model.pt`
- Test Metrics JSON: `ml/artifacts/galaxy_zoo_metrics.json`
- Confusion Matrix Plot: `ml/artifacts/galaxy_zoo_confusion_matrix.png`
- Embeddings Matrix: `ml/artifacts/galaxy_zoo_embeddings.npy` ({all_embeddings_arr.shape})
- Embedding Index: `ml/artifacts/galaxy_zoo_embedding_index.csv`
"""

    with open(doc_path, "w") as f:
        f.write(doc_content)
    print_log(f"Saved Training Log Documentation to: {doc_path}")

if __name__ == '__main__':
    main()
