import os
import pandas as pd
import torch
from torch.utils.data import Dataset
from PIL import Image

CLASS_TO_IDX = {
    'SMOOTH': 0,
    'EDGE_ON': 1,
    'FEATURED_DISK': 2,
    'SPIRAL': 3
}

IDX_TO_CLASS = {v: k for k, v in CLASS_TO_IDX.items()}

ATTRIBUTE_COLS = [
    'prob_smooth',
    'prob_features',
    'prob_edgeon',
    'prob_spiral',
    'prob_bar',
    'prob_odd'
]

class GalaxyZooDataset(Dataset):
    def __init__(self, csv_path: str, img_dir: str, split: str = None, transform = None):
        super().__init__()
        self.csv_path = csv_path
        self.img_dir = img_dir
        self.transform = transform
        
        df = pd.read_csv(csv_path)
        if split is not None:
            df = df[df['split'] == split].reset_index(drop=True)
            
        self.df = df
        
        # Pre-verify file paths
        for fname in self.df['image_filename']:
            path = os.path.join(self.img_dir, fname)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing required image file: {path}")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        img_path = os.path.join(self.img_dir, row['image_filename'])
        
        image = Image.open(img_path).convert('RGB')
        if self.transform is not None:
            image = self.transform(image)
            
        class_label = CLASS_TO_IDX[row['target_4class']]
        attr_values = row[ATTRIBUTE_COLS].values.astype('float32')
        
        return {
            'image': image,
            'class_target': torch.tensor(class_label, dtype=torch.long),
            'attribute_targets': torch.tensor(attr_values, dtype=torch.float32),
            'asset_id': row['asset_id'],
            'image_filename': row['image_filename']
        }
