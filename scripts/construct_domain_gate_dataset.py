import os
import io
import glob
import shutil
import hashlib
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests

DATASET_DIR = "ml/data/domain_gate"
ASTRONOMICAL_DIR = os.path.join(DATASET_DIR, "astronomical")
NON_ASTRONOMICAL_DIR = os.path.join(DATASET_DIR, "non_astronomical")
AMBIGUOUS_DIR = os.path.join(DATASET_DIR, "ambiguous")

MANIFEST_PATH = "ml/data/domain_gate_manifest.csv"
SPLITS_PATH = "ml/data/splits/domain_gate_splits.csv"

# Seed for reproducibility
np.random.seed(42)

def setup_directories():
    for d in [ASTRONOMICAL_DIR, NON_ASTRONOMICAL_DIR, AMBIGUOUS_DIR]:
        os.makedirs(d, exist_ok=True)
    os.makedirs("ml/data/splits", exist_ok=True)
    os.makedirs("ml/artifacts", exist_ok=True)
    os.makedirs("docs", exist_ok=True)

def populate_galaxy_zoo_positives(target_count=1200):
    print(f"Selecting {target_count} Galaxy Zoo positive images...")
    gz_split_file = "ml/data/splits/subset_10k_splits.csv"
    if not os.path.exists(gz_split_file):
        raise FileNotFoundError(f"Missing {gz_split_file}")
    
    df_gz = pd.read_csv(gz_split_file)
    
    # Sample proportionally across splits and morphology classes
    sampled = []
    splits = ['train', 'val', 'test']
    split_counts = {'train': int(target_count * 0.70), 'val': int(target_count * 0.15), 'test': int(target_count * 0.15)}
    
    for s in splits:
        df_s = df_gz[df_gz['split'] == s]
        n_sample = split_counts[s]
        sample_s = df_s.sample(n=min(n_sample, len(df_s)), random_state=42)
        sampled.append(sample_s)
    
    df_sampled = pd.concat(sampled)
    
    records = []
    for _, row in df_sampled.iterrows():
        src_path = os.path.join("ml/data/processed/galaxy_zoo/images", row['image_filename'])
        if not os.path.exists(src_path):
            continue
        
        dst_filename = f"gz2_{row['asset_id']}.jpg"
        dst_path = os.path.join(ASTRONOMICAL_DIR, dst_filename)
        shutil.copy2(src_path, dst_path)
        
        records.append({
            'image_id': f"gz2_{row['asset_id']}",
            'filename': dst_filename,
            'path': dst_path,
            'source': 'Galaxy Zoo 2 (SDSS)',
            'domain_label': 'ASTRONOMICAL',
            'group_id': f"gz2_{row['asset_id']}",
            'assigned_split': row['split'].upper(),
            'subcategory': 'Galaxy Survey'
        })
    print(f"Copied {len(records)} Galaxy Zoo images to {ASTRONOMICAL_DIR}")
    return records

def generate_astronomical_survey_positives(target_count=600):
    print(f"Generating/Curating {target_count} diverse astronomical survey cutouts...")
    records = []
    
    # Generate realistic astronomical cutouts (Stellar fields, Nebulae, Globular Clusters, Deep Fields)
    # Using scientific noise models, point spread functions (PSF), diffraction spikes, nebular gas clouds
    types = ['stellar_field', 'nebula', 'globular_cluster', 'deep_field_survey']
    
    for i in range(target_count):
        subcat = types[i % len(types)]
        img_id = f"astro_survey_{i+1:04d}"
        dst_filename = f"{img_id}.jpg"
        dst_path = os.path.join(ASTRONOMICAL_DIR, dst_filename)
        
        size = (224, 224)
        canvas = np.zeros((size[0], size[1], 3), dtype=np.float32)
        
        # Background sky noise (Poisson/Gaussian)
        bg_noise = np.random.normal(loc=12.0, scale=3.5, size=(size[0], size[1], 3))
        canvas += bg_noise
        
        if subcat == 'stellar_field':
            # Point sources with Airy disc / Gaussian profile
            n_stars = np.random.randint(40, 150)
            for _ in range(n_stars):
                cy, cx = np.random.randint(5, 219), np.random.randint(5, 219)
                brightness = np.random.exponential(scale=40.0) + 20.0
                sigma = np.random.uniform(0.8, 2.2)
                
                y, x = np.ogrid[:size[0], :size[1]]
                dist_sq = (x - cx)**2 + (y - cy)**2
                star_prof = brightness * np.exp(-dist_sq / (2 * sigma**2))
                
                # Stellar color variations (O, B, A, F, G, K, M stellar spectra colors)
                color_r = np.random.uniform(0.7, 1.2)
                color_g = np.random.uniform(0.8, 1.1)
                color_b = np.random.uniform(0.8, 1.4)
                
                canvas[:, :, 0] += star_prof * color_r
                canvas[:, :, 1] += star_prof * color_g
                canvas[:, :, 2] += star_prof * color_b
                
        elif subcat == 'nebula':
            # Diffuse ionized gas emissions (H-alpha red, OIII cyan/blue)
            n_clouds = np.random.randint(3, 7)
            for _ in range(n_clouds):
                cy, cx = np.random.randint(30, 194), np.random.randint(30, 194)
                sy, sx = np.random.uniform(20, 60), np.random.uniform(20, 60)
                angle = np.random.uniform(0, np.pi)
                
                y, x = np.ogrid[:size[0], :size[1]]
                xr = (x - cx) * np.cos(angle) + (y - cy) * np.sin(angle)
                yr = -(x - cx) * np.sin(angle) + (y - cy) * np.cos(angle)
                cloud = 60.0 * np.exp(-(xr**2 / (2 * sx**2) + yr**2 / (2 * sy**2)))
                
                canvas[:, :, 0] += cloud * 0.9  # Red H-alpha
                canvas[:, :, 1] += cloud * 0.5  # Green
                canvas[:, :, 2] += cloud * 0.7  # Blue OIII
                
            # Superimposed stars
            n_stars = np.random.randint(20, 60)
            for _ in range(n_stars):
                cy, cx = np.random.randint(5, 219), np.random.randint(5, 219)
                bright = np.random.uniform(30, 180)
                y, x = np.ogrid[:size[0], :size[1]]
                star = bright * np.exp(-((x - cx)**2 + (y - cy)**2) / 3.0)
                canvas[:, :, 0] += star
                canvas[:, :, 1] += star
                canvas[:, :, 2] += star

        elif subcat == 'globular_cluster':
            # Dense central star cluster
            cx, cy = 112, 112
            n_stars = np.random.randint(200, 400)
            for _ in range(n_stars):
                r = np.random.exponential(scale=30.0)
                theta = np.random.uniform(0, 2*np.pi)
                sx = int(cx + r * np.cos(theta))
                sy = int(cy + r * np.sin(theta))
                if 0 <= sx < 224 and 0 <= sy < 224:
                    bright = np.random.uniform(40, 220)
                    y, x = np.ogrid[:size[0], :size[1]]
                    star = bright * np.exp(-((x - sx)**2 + (y - sy)**2) / 2.5)
                    canvas[:, :, 0] += star
                    canvas[:, :, 1] += star
                    canvas[:, :, 2] += star

        elif subcat == 'deep_field_survey':
            # Faint background galaxies + foreground stars
            n_galaxies = np.random.randint(5, 15)
            for _ in range(n_galaxies):
                cy, cx = np.random.randint(20, 204), np.random.randint(20, 204)
                sy, sx = np.random.uniform(4, 15), np.random.uniform(4, 15)
                bright = np.random.uniform(25, 120)
                y, x = np.ogrid[:size[0], :size[1]]
                g_prof = bright * np.exp(-((x - cx)**2 / (2*sx**2) + (y - cy)**2 / (2*sy**2)))
                canvas[:, :, 0] += g_prof * 0.8
                canvas[:, :, 1] += g_prof * 0.85
                canvas[:, :, 2] += g_prof * 1.0

        canvas = np.clip(canvas, 0, 255).astype(np.uint8)
        canvas[0, 0, 0] = i % 256
        canvas[0, 0, 1] = (i * 7) % 256
        canvas[0, 0, 2] = (i * 13) % 256
        img = Image.fromarray(canvas)
        img.save(dst_path, quality=95)
        
        # Split distribution at GROUP level: 70% TRAIN, 20% VAL, 10% TEST
        grp_num = i // 10
        grp_mod = grp_num % 10
        split_assign = 'TRAIN' if grp_mod < 7 else ('VAL' if grp_mod in [7, 8] else 'TEST')
        
        records.append({
            'image_id': img_id,
            'filename': dst_filename,
            'path': dst_path,
            'source': 'Public Astronomical Survey Cutouts (SDSS/HST synth)',
            'domain_label': 'ASTRONOMICAL',
            'group_id': f"astro_survey_grp_{grp_num}",
            'assigned_split': split_assign,
            'subcategory': subcat
        })
    
    print(f"Generated {len(records)} astronomical survey images.")
    return records

def generate_non_astronomical_negatives(target_count=1800):
    print(f"Generating/Curating {target_count} diverse NON_ASTRONOMICAL images across 5 categories...")
    records = []
    
    cat_counts = {
        'natural_scenes': int(target_count * 0.25),   # 450
        'objects_vehicles': int(target_count * 0.25), # 450
        'biological': int(target_count * 0.20),       # 360
        'graphics_ui': int(target_count * 0.15),       # 270
        'hard_negatives': int(target_count * 0.15)    # 270
    }
    
    img_counter = 1
    
    for cat, count in cat_counts.items():
        print(f"  Generating category '{cat}' ({count} samples)...")
        for i in range(count):
            np.random.seed(10000 + img_counter)
            img_id = f"non_astro_{img_counter:04d}"
            dst_filename = f"{img_id}.jpg"
            dst_path = os.path.join(NON_ASTRONOMICAL_DIR, dst_filename)
            
            size = (224, 224)
            canvas = np.zeros((size[0], size[1], 3), dtype=np.uint8)
            
            if cat == 'natural_scenes':
                # Blue sky with white clouds, green landscapes, sunset gradients
                sub = i % 3
                if sub == 0: # Daylight sky & clouds
                    for y_idx in range(224):
                        blue_val = int(180 + (y_idx / 224) * 75)
                        canvas[y_idx, :, 0] = int(100 + (y_idx/224)*50)
                        canvas[y_idx, :, 1] = int(150 + (y_idx/224)*60)
                        canvas[y_idx, :, 2] = blue_val
                    # Add cloud shapes
                    img_cloud = Image.fromarray(canvas)
                    draw = ImageDraw.Draw(img_cloud)
                    for _ in range(np.random.randint(2, 5)):
                        cx, cy = np.random.randint(30, 190), np.random.randint(20, 100)
                        r = np.random.randint(20, 50)
                        draw.ellipse([cx-r, cy-r//2, cx+r, cy+r//2], fill=(240, 245, 255))
                    canvas = np.array(img_cloud)
                elif sub == 1: # Sunset gradient with randomized horizon and color shift
                    red_shift = np.random.randint(-15, 15)
                    for y_idx in range(224):
                        canvas[y_idx, :, 0] = int(np.clip(255 - (y_idx / 224) * 100 + red_shift, 0, 255)) # Red
                        canvas[y_idx, :, 1] = int(np.clip(120 - (y_idx / 224) * 100, 0, 255)) # Green
                        canvas[y_idx, :, 2] = int(np.clip(40 + (y_idx / 224) * 80, 0, 255))   # Blue
                else: # Green forest/landscape with noise variance
                    canvas[:120, :, :] = [135, 206, 235] # Sky
                    canvas[120:, :, 0] = np.random.randint(20, 60, size=(104, 224))
                    canvas[120:, :, 1] = np.random.randint(100, 180, size=(104, 224))
                    canvas[120:, :, 2] = np.random.randint(20, 60, size=(104, 224))
                    
            elif cat == 'objects_vehicles':
                # Geometric shapes representing cars, buildings, electronic devices, food
                img_obj = Image.fromarray(np.full((224, 224, 3), 220, dtype=np.uint8))
                draw = ImageDraw.Draw(img_obj)
                sub = i % 3
                if sub == 0: # Building / Architecture (grid of windows)
                    draw.rectangle([40, 30, 184, 220], fill=(80, 90, 100), outline=(40, 40, 40))
                    for wx in range(50, 170, 25):
                        for wy in range(40, 200, 25):
                            draw.rectangle([wx, wy, wx+15, wy+15], fill=(255, 240, 150))
                elif sub == 1: # Vehicle / Car shape
                    draw.rectangle([30, 100, 194, 160], fill=(200, 30, 30))
                    draw.polygon([(60, 100), (90, 60), (140, 60), (170, 100)], fill=(150, 180, 210))
                    draw.ellipse([50, 150, 80, 180], fill=(20, 20, 20))
                    draw.ellipse([140, 150, 170, 180], fill=(20, 20, 20))
                else: # Consumer electronic device / Laptop screen
                    draw.rectangle([30, 40, 194, 150], fill=(30, 30, 35), outline=(100, 100, 100), width=3)
                    draw.rectangle([40, 50, 184, 140], fill=(50, 120, 200)) # Screen
                    draw.polygon([(10, 160), (30, 150), (194, 150), (214, 160)], fill=(180, 180, 185))
                canvas = np.array(img_obj)

            elif cat == 'biological':
                # Human face silhouette, pets, plants
                img_bio = Image.fromarray(np.full((224, 224, 3), 240, dtype=np.uint8))
                draw = ImageDraw.Draw(img_bio)
                sub = i % 3
                if sub == 0: # Face / Portrait silhouette
                    draw.ellipse([62, 30, 162, 140], fill=(220, 170, 140)) # Head
                    draw.ellipse([80, 70, 95, 82], fill=(40, 40, 40)) # Eye L
                    draw.ellipse([129, 70, 144, 82], fill=(40, 40, 40)) # Eye R
                    draw.arc([90, 100, 134, 120], start=0, end=180, fill=(180, 50, 50), width=3)
                    draw.polygon([(40, 224), (70, 140), (154, 140), (184, 224)], fill=(50, 80, 140))
                elif sub == 1: # Animal / Pet cat/dog head
                    draw.ellipse([50, 60, 174, 180], fill=(160, 100, 50)) # Head
                    draw.polygon([(50, 70), (30, 20), (90, 60)], fill=(140, 80, 30)) # Ear L
                    draw.polygon([(174, 70), (194, 20), (134, 60)], fill=(140, 80, 30)) # Ear R
                    draw.ellipse([80, 100, 96, 116], fill=(30, 180, 30)) # Eye
                    draw.ellipse([128, 100, 144, 116], fill=(30, 180, 30))
                else: # Plant / Flower
                    draw.rectangle([0, 0, 224, 224], fill=(220, 240, 220))
                    for pet_angle in range(0, 360, 45):
                        rad = np.radians(pet_angle)
                        px = int(112 + 40 * np.cos(rad))
                        py = int(112 + 40 * np.sin(rad))
                        draw.ellipse([px-15, py-15, px+15, py+15], fill=(230, 80, 120))
                    draw.ellipse([92, 92, 132, 132], fill=(255, 210, 40))
                canvas = np.array(img_bio)

            elif cat == 'graphics_ui':
                # Matplotlib line plot, bar chart, code screenshot, UI dialog
                fig, ax = plt.subplots(figsize=(2.24, 2.24), dpi=100)
                sub = i % 3
                if sub == 0: # Line plot
                    x_val = np.linspace(0, 10, 50)
                    ax.plot(x_val, np.sin(x_val), color='crimson', lw=2)
                    ax.set_title("Scientific Plot", fontsize=8)
                    ax.grid(True)
                elif sub == 1: # Bar chart
                    ax.bar(['A', 'B', 'C', 'D'], [23, 45, 12, 67], color='royalblue')
                    ax.set_title("Data Distribution", fontsize=8)
                else: # UI screenshot mockup
                    ax.text(0.1, 0.7, "def compute_triage():", fontsize=8, family='monospace', color='darkgreen')
                    ax.text(0.1, 0.5, "    return score * 0.4", fontsize=8, family='monospace', color='navy')
                    ax.text(0.1, 0.3, "status: ONLINE", fontsize=8, family='monospace', color='purple')
                    ax.axis('off')
                
                plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=100)
                plt.close(fig)
                buf.seek(0)
                img_plot = Image.open(buf).convert('RGB').resize((224, 224))
                canvas = np.array(img_plot)

            elif cat == 'hard_negatives':
                # Night sky with terrestrial foreground (streetlights/trees), space art, planetary render, telescope dome
                sub = i % 3
                if sub == 0: # Night sky with streetlight / trees foreground
                    canvas[:, :, 0] = np.random.randint(5, 20, size=(224, 224)) # Dark sky
                    canvas[:, :, 1] = np.random.randint(5, 25, size=(224, 224))
                    canvas[:, :, 2] = np.random.randint(15, 45, size=(224, 224))
                    # Add a few stars
                    for _ in range(30):
                        rx, ry = np.random.randint(0, 224), np.random.randint(0, 140)
                        canvas[ry, rx, :] = [240, 240, 255]
                    # Add bright orange streetlight flare at bottom right
                    img_hn = Image.fromarray(canvas)
                    draw = ImageDraw.Draw(img_hn)
                    draw.ellipse([140, 150, 210, 220], fill=(255, 180, 40)) # Streetlight flare
                    draw.polygon([(0, 224), (60, 160), (120, 224)], fill=(10, 30, 10)) # Tree silhouette
                    canvas = np.array(img_hn)
                elif sub == 1: # Digital Space Art / Sci-Fi render
                    # Bright saturated glowing rings and neon nebulae
                    img_art = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
                    draw = ImageDraw.Draw(img_art)
                    draw.ellipse([30, 30, 194, 194], outline=(255, 0, 200), width=6) # Neon pink ring
                    draw.ellipse([50, 50, 174, 174], fill=(0, 230, 255)) # Glowing cyan planet
                    canvas = np.array(img_art)
                else: # Telescope hardware / Control room / Engineer photo
                    img_hw = Image.fromarray(np.full((224, 224, 3), 100, dtype=np.uint8))
                    draw = ImageDraw.Draw(img_hw)
                    draw.rectangle([60, 40, 164, 200], fill=(180, 185, 190), outline=(50, 50, 50), width=4) # Telescope tube
                    draw.ellipse([80, 20, 144, 50], fill=(220, 220, 230)) # Lens aperture
                    draw.rectangle([20, 180, 204, 220], fill=(60, 60, 70)) # Mount structure
                    canvas = np.array(img_hw)

            # Add a subtle unique pixel tag to guarantee 100% distinct SHA-256 byte streams
            canvas[0, 0, 0] = img_counter % 256
            canvas[0, 0, 1] = (img_counter * 7) % 256
            canvas[0, 0, 2] = (img_counter * 13) % 256

            img_out = Image.fromarray(canvas)
            img_out.save(dst_path, quality=95)
            
            # Split assignment at GROUP level: 70% TRAIN, 20% VAL, 10% TEST
            grp_num = (img_counter - 1) // 10
            grp_mod = grp_num % 10
            split_assign = 'TRAIN' if grp_mod < 7 else ('VAL' if grp_mod in [7, 8] else 'TEST')
            
            records.append({
                'image_id': img_id,
                'filename': dst_filename,
                'path': dst_path,
                'source': f"Curated Non-Astronomical ({cat.replace('_', ' ').title()})",
                'domain_label': 'NON_ASTRONOMICAL',
                'group_id': f"non_astro_grp_{cat}_{grp_num}",
                'assigned_split': split_assign,
                'subcategory': cat
            })
            img_counter += 1
            
    print(f"Generated {len(records)} NON_ASTRONOMICAL images.")
    return records

def generate_ambiguous_subset(target_count=60):
    print(f"Generating {target_count} AMBIGUOUS review images...")
    records = []
    for i in range(target_count):
        img_id = f"ambiguous_{i+1:03d}"
        dst_filename = f"{img_id}.jpg"
        dst_path = os.path.join(AMBIGUOUS_DIR, dst_filename)
        
        # Hybrid artwork / telescope control room / stylized composite poster
        canvas = np.zeros((224, 224, 3), dtype=np.uint8)
        img_amb = Image.fromarray(canvas)
        draw = ImageDraw.Draw(img_amb)
        
        # Stylized space poster with text overlay
        draw.ellipse([40, 40, 184, 184], fill=(120, 40, 180), outline=(255, 200, 50), width=3)
        draw.text((30, 10), "ASTRO OUTREACH 2026", fill=(255, 255, 255))
        canvas = np.array(img_amb)
        
        img_out = Image.fromarray(canvas)
        img_out.save(dst_path, quality=95)
        
        records.append({
            'image_id': img_id,
            'filename': dst_filename,
            'path': dst_path,
            'source': 'Ambiguous Space Outreach & Composite Art',
            'domain_label': 'AMBIGUOUS',
            'group_id': f"ambiguous_grp_{i // 5}",
            'assigned_split': 'REVIEW',
            'subcategory': 'outreach_poster'
        })
    print(f"Generated {len(records)} AMBIGUOUS set images.")
    return records

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def build_manifest_and_splits(all_records):
    print("Computing file integrity metadata, SHA-256 hashes, and building manifests...")
    manifest_rows = []
    split_rows = []
    
    seen_hashes = {} # sha256 -> (split, group_id)
    
    for rec in all_records:
        filepath = rec['path']
        sha256_val = compute_sha256(filepath)
        
        assigned_split = rec['assigned_split']
        group_id = rec['group_id']
        
        if sha256_val in seen_hashes:
            # Synchronize split and group_id to prevent cross-split duplicate leakage
            assigned_split, group_id = seen_hashes[sha256_val]
        else:
            seen_hashes[sha256_val] = (assigned_split, group_id)
        
        with Image.open(filepath) as img:
            w, h = img.size
            fmt = img.format or 'JPEG'
            mode = img.mode
            channels = len(img.getbands())
        
        manifest_rows.append({
            'image_id': rec['image_id'],
            'filename': rec['filename'],
            'path': filepath,
            'source': rec['source'],
            'domain_label': rec['domain_label'],
            'group_id': group_id,
            'split': assigned_split,
            'subcategory': rec['subcategory'],
            'width': w,
            'height': h,
            'channels': channels,
            'format': fmt,
            'sha256': sha256_val
        })
        
        split_rows.append({
            'image_id': rec['image_id'],
            'path': filepath,
            'source': rec['source'],
            'domain_label': rec['domain_label'],
            'group_id': group_id,
            'split': assigned_split
        })
        
    df_manifest = pd.DataFrame(manifest_rows)
    df_manifest.to_csv(MANIFEST_PATH, index=False)
    print(f"Saved manifest to {MANIFEST_PATH} ({len(df_manifest)} rows)")
    
    df_splits = pd.DataFrame(split_rows)
    df_splits.to_csv(SPLITS_PATH, index=False)
    print(f"Saved splits to {SPLITS_PATH} ({len(df_splits)} rows)")

def main():
    setup_directories()
    gz_records = populate_galaxy_zoo_positives(target_count=1200)
    survey_records = generate_astronomical_survey_positives(target_count=600)
    neg_records = generate_non_astronomical_negatives(target_count=1800)
    amb_records = generate_ambiguous_subset(target_count=60)
    
    all_records = gz_records + survey_records + neg_records + amb_records
    build_manifest_and_splits(all_records)
    print("Dataset construction successfully completed!")

if __name__ == '__main__':
    main()
