# Galaxy Zoo 2 Multi-Head CNN Training Documentation

- **Date**: 2026-09-12 00:34:27
- **Hardware**: Apple Silicon M4
- **PyTorch Version**: 2.14.0
- **Device**: mps
- **Dataset Counts**: Train: 8,000 | Validation: 1,000 | Test: 1,000 | Total: 10,000
- **Model Architecture**: Multi-Head CNN with `efficientnet_b0` backbone
- **Embedding Dimension**: 1280
- **Input Resolution**: 224 × 224 RGB

## Training Parameters
- **Optimizer**: AdamW
- **Scheduler**: CosineAnnealingLR
- **Batch Size**: 64
- **Total Epochs**: 15
- **Best Epoch**: 10

## Test Set Performance (Untouched 1,000 Samples)
- **Accuracy**: `68.50%`
- **Macro F1 Score**: `0.6648`
- **Weighted F1 Score**: `0.6770`
- **Attribute MAE**: `0.1544`
- **Attribute RMSE**: `0.2130`

## Artifacts Generated
- Model Checkpoint: `ml/models/best_model.pt`
- Test Metrics JSON: `ml/artifacts/galaxy_zoo_metrics.json`
- Confusion Matrix Plot: `ml/artifacts/galaxy_zoo_confusion_matrix.png`
- Embeddings Matrix: `ml/artifacts/galaxy_zoo_embeddings.npy` ((10000, 1280))
- Embedding Index: `ml/artifacts/galaxy_zoo_embedding_index.csv`
