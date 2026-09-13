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

DATASET_V2_DIR = "ml/data/domain_gate_v2"
ASTRO_DIR = os.path.join(DATASET_V2_DIR, "astronomical")
NON_ASTRO_DIR = os.path.join(DATASET_V2_DIR, "non_astronomical")
HARD_NEG_DIR = os.path.join(DATASET_V2_DIR, "hard_negatives")
HARD_POS_DIR = os.path.join(DATASET_V2_DIR, "hard_positives")

MANIFEST_V2_PATH = os.path.join(DATASET_V2_DIR, "manifest.csv")
SPLITS_V2_PATH = "ml/data/splits/domain_gate_v2_splits.csv"

ADV_NEG_MANIFEST = "ml/data/domain_gate/adversarial_manifest.csv"
ADV_POS_MANIFEST = "ml/data/domain_gate/adversarial_positive_manifest.csv"

np.random.seed(42)

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_adversarial_hashes():
    hashes = set()
    for path in [ADV_NEG_MANIFEST, ADV_POS_MANIFEST]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            for h in df['sha256'].dropna():
                hashes.add(str(h))
    return hashes

def setup_directories():
    for d in [ASTRO_DIR, NON_ASTRO_DIR, HARD_NEG_DIR, HARD_POS_DIR]:
        os.makedirs(d, exist_ok=True)
    os.makedirs("ml/data/splits", exist_ok=True)

def populate_galaxy_zoo_positives(target_count=1500, adv_hashes=set()):
    print(f"Selecting {target_count} Galaxy Zoo positive images for V2 dataset...")
    gz_split_file = "ml/data/splits/subset_10k_splits.csv"
    if not os.path.exists(gz_split_file):
        raise FileNotFoundError(f"Missing {gz_split_file}")
        
    df_gz = pd.read_csv(gz_split_file)
    records = []
    
    # Proportional sampling across GZ splits
    sampled = df_gz.sample(n=min(target_count, len(df_gz)), random_state=42).reset_index(drop=True)
    
    for idx, row in sampled.iterrows():
        src_path = os.path.join("ml/data/processed/galaxy_zoo/images", row['image_filename'])
        if not os.path.exists(src_path):
            continue
            
        sha = compute_sha256(src_path)
        if sha in adv_hashes:
            print(f"Skipping adversarial duplicate hash: {sha}")
            continue
            
        dst_filename = f"v2_astro_gz2_{row['asset_id']}.jpg"
        dst_path = os.path.join(ASTRO_DIR, dst_filename)
        shutil.copy2(src_path, dst_path)
        
        records.append({
            'image_id': f"v2_astro_gz2_{row['asset_id']}",
            'filename': dst_filename,
            'path': dst_path,
            'category': 'galaxy_zoo_sdss',
            'domain_label': 'ASTRONOMICAL',
            'is_hard_sample': False,
            'source': 'SDSS Galaxy Zoo 2 Target Observation',
            'group_id': f"gz2_{row['asset_id']}",
            'sha256': sha,
            'notes': f"Real SDSS galaxy observation cutout (morphology: {row['broad_morphology']})"
        })
    print(f"Copied {len(records)} Galaxy Zoo images to {ASTRO_DIR}")
    return records

def generate_astronomical_survey_cutouts(target_count=500, adv_hashes=set()):
    print(f"Generating {target_count} diverse astronomical survey cutouts...")
    records = []
    types = ['stellar_field', 'nebula', 'globular_cluster', 'deep_field_survey']
    
    for i in range(target_count):
        subcat = types[i % len(types)]
        img_id = f"v2_astro_survey_{i+1:04d}"
        dst_filename = f"{img_id}.jpg"
        dst_path = os.path.join(ASTRO_DIR, dst_filename)
        
        seed = 70000 + i
        np.random.seed(seed)
        size = (224, 224)
        canvas = np.zeros((size[0], size[1], 3), dtype=np.float32)
        
        # Background sky noise
        bg_noise = np.random.normal(loc=12.0, scale=3.5, size=(size[0], size[1], 3))
        canvas += bg_noise
        
        if subcat == 'stellar_field':
            n_stars = np.random.randint(40, 150)
            y, x = np.ogrid[:size[0], :size[1]]
            for _ in range(n_stars):
                cy, cx = np.random.randint(5, 219), np.random.randint(5, 219)
                brightness = np.random.exponential(scale=40.0) + 20.0
                sigma = np.random.uniform(0.8, 2.2)
                star_prof = brightness * np.exp(-((x - cx)**2 + (y - cy)**2) / (2 * sigma**2))
                canvas[:, :, 0] += star_prof * np.random.uniform(0.7, 1.2)
                canvas[:, :, 1] += star_prof * np.random.uniform(0.8, 1.1)
                canvas[:, :, 2] += star_prof * np.random.uniform(0.8, 1.4)
                
        elif subcat == 'nebula':
            n_clouds = np.random.randint(3, 7)
            y, x = np.ogrid[:size[0], :size[1]]
            for _ in range(n_clouds):
                cy, cx = np.random.randint(30, 194), np.random.randint(30, 194)
                sy, sx = np.random.uniform(20, 60), np.random.uniform(20, 60)
                cloud = 60.0 * np.exp(-((x - cx)**2 / (2*sx**2) + (y - cy)**2 / (2*sy**2)))
                canvas[:, :, 0] += cloud * 0.9
                canvas[:, :, 1] += cloud * 0.5
                canvas[:, :, 2] += cloud * 0.7
                
        elif subcat == 'globular_cluster':
            cx, cy = 112, 112
            n_stars = np.random.randint(200, 400)
            y, x = np.ogrid[:size[0], :size[1]]
            for _ in range(n_stars):
                r = np.random.exponential(scale=30.0)
                theta = np.random.uniform(0, 2*np.pi)
                sx_pos = int(cx + r * np.cos(theta))
                sy_pos = int(cy + r * np.sin(theta))
                if 0 <= sx_pos < 224 and 0 <= sy_pos < 224:
                    bright = np.random.uniform(40, 220)
                    star = bright * np.exp(-((x - sx_pos)**2 + (y - sy_pos)**2) / 2.5)
                    canvas[:, :, 0] += star
                    canvas[:, :, 1] += star
                    canvas[:, :, 2] += star

        elif subcat == 'deep_field_survey':
            n_galaxies = np.random.randint(5, 15)
            y, x = np.ogrid[:size[0], :size[1]]
            for _ in range(n_galaxies):
                cy, cx = np.random.randint(20, 204), np.random.randint(20, 204)
                sy, sx = np.random.uniform(4, 15), np.random.uniform(4, 15)
                bright = np.random.uniform(25, 120)
                g_prof = bright * np.exp(-((x - cx)**2 / (2*sx**2) + (y - cy)**2 / (2*sy**2)))
                canvas[:, :, 0] += g_prof * 0.8
                canvas[:, :, 1] += g_prof * 0.85
                canvas[:, :, 2] += g_prof * 1.0

        canvas = np.clip(canvas, 0, 255).astype(np.uint8)
        canvas[0, 0, 0] = seed % 256
        canvas[0, 0, 1] = (seed * 3) % 256
        canvas[0, 0, 2] = (seed * 7) % 256
        
        img = Image.fromarray(canvas)
        img.save(dst_path, quality=95)
        sha = compute_sha256(dst_path)
        
        if sha in adv_hashes:
            continue
            
        records.append({
            'image_id': img_id,
            'filename': dst_filename,
            'path': dst_path,
            'category': subcat,
            'domain_label': 'ASTRONOMICAL',
            'is_hard_sample': False,
            'source': 'Astronomical Survey Cutout Generator',
            'group_id': f"astro_survey_grp_{i // 10}",
            'sha256': sha,
            'notes': f"Survey cutout ({subcat})"
        })
    return records

def generate_hard_positives(target_count=1000, adv_hashes=set()):
    """
    Construct hard astronomical positive training pool:
    - faint galaxies
    - low surface brightness targets
    - diffuse nebulae with sky noise
    - low S/N observation cutouts
    - crowded stellar fields
    """
    print(f"Generating {target_count} HARD POSITIVE astronomical training samples...")
    records = []
    categories = ['faint_galaxy', 'low_contrast_lsb', 'diffuse_nebula', 'crowded_field_cluster', 'high_redshift_deep']
    
    for i in range(target_count):
        subcat = categories[i % len(categories)]
        img_id = f"v2_hard_pos_{i+1:04d}"
        dst_filename = f"{img_id}.jpg"
        dst_path = os.path.join(HARD_POS_DIR, dst_filename)
        
        seed = 80000 + i
        np.random.seed(seed)
        size = (224, 224)
        canvas = np.zeros((size[0], size[1], 3), dtype=np.float32)
        
        # Sky background noise level
        bg = np.random.normal(loc=15.0, scale=4.5, size=(224, 224, 3))
        canvas += bg
        y, x = np.ogrid[:224, :224]
        
        if subcat == 'faint_galaxy':
            # Faint low signal-to-noise galaxy profile
            cy, cx = np.random.randint(80, 144), np.random.randint(80, 144)
            sy, sx = np.random.uniform(15, 35), np.random.uniform(15, 35)
            peak_bright = np.random.uniform(22.0, 45.0) # Near sky background level!
            g_prof = peak_bright * np.exp(-((x - cx)**2 / (2*sx**2) + (y - cy)**2 / (2*sy**2)))
            canvas[:, :, 0] += g_prof * 0.9
            canvas[:, :, 1] += g_prof * 0.95
            canvas[:, :, 2] += g_prof * 1.05
            
        elif subcat == 'low_contrast_lsb':
            # Low surface brightness galaxy diffuse disk
            cy, cx = 112, 112
            sy, sx = np.random.uniform(30, 60), np.random.uniform(20, 50)
            lsb_prof = np.random.uniform(18.0, 32.0) * np.exp(-((x - cx)**2 / (2*sx**2) + (y - cy)**2 / (2*sy**2)))
            canvas[:, :, 0] += lsb_prof * 0.85
            canvas[:, :, 1] += lsb_prof * 0.90
            canvas[:, :, 2] += lsb_prof * 1.0
            
        elif subcat == 'diffuse_nebula':
            # Faint ionized emission region
            cy, cx = np.random.randint(60, 164), np.random.randint(60, 164)
            cloud = np.random.uniform(25.0, 50.0) * np.exp(-((x - cx)**2 / (2*40.0**2) + (y - cy)**2 / (2*30.0**2)))
            canvas[:, :, 0] += cloud * 0.95 # H-alpha
            canvas[:, :, 1] += cloud * 0.35
            canvas[:, :, 2] += cloud * 0.65
            
        elif subcat == 'crowded_field_cluster':
            # Globular cluster core
            n_stars = np.random.randint(180, 350)
            for _ in range(n_stars):
                r = np.random.exponential(scale=25.0)
                th = np.random.uniform(0, 2*np.pi)
                sx_p = int(112 + r * np.cos(th))
                sy_p = int(112 + r * np.sin(th))
                if 0 <= sx_p < 224 and 0 <= sy_p < 224:
                    bright = np.random.uniform(25, 180)
                    star = bright * np.exp(-((x - sx_p)**2 + (y - sy_p)**2) / 2.0)
                    canvas[:, :, :] += star[:, :, None]
                    
        elif subcat == 'high_redshift_deep':
            # Small distant high-redshift smudge galaxies
            for _ in range(np.random.randint(4, 10)):
                cy, cx = np.random.randint(20, 204), np.random.randint(20, 204)
                sy, sx = np.random.uniform(3, 8), np.random.uniform(3, 8)
                bright = np.random.uniform(20, 60)
                g_p = bright * np.exp(-((x - cx)**2 / (2*sx**2) + (y - cy)**2 / (2*sy**2)))
                canvas[:, :, 0] += g_p * 1.1
                canvas[:, :, 1] += g_p * 0.8
                canvas[:, :, 2] += g_p * 0.7

        canvas = np.clip(canvas, 0, 255).astype(np.uint8)
        canvas[0, 0, 0] = seed % 256
        canvas[0, 0, 1] = (seed * 3) % 256
        canvas[0, 0, 2] = (seed * 7) % 256
        
        img = Image.fromarray(canvas)
        img.save(dst_path, quality=95)
        sha = compute_sha256(dst_path)
        
        if sha in adv_hashes:
            continue
            
        records.append({
            'image_id': img_id,
            'filename': dst_filename,
            'path': dst_path,
            'category': subcat,
            'domain_label': 'ASTRONOMICAL',
            'is_hard_sample': True,
            'source': 'Hard Positive Astronomical Target Generator',
            'group_id': f"hard_pos_grp_{i // 10}",
            'sha256': sha,
            'notes': f"Hard positive astronomical observation ({subcat})"
        })
    return records

def generate_non_astronomical_positives(target_count=1500, adv_hashes=set()):
    print(f"Generating {target_count} standard NON_ASTRONOMICAL images...")
    records = []
    categories = ['natural_scenes', 'objects_vehicles', 'biological', 'graphics_ui', 'daylight_sky']
    
    for i in range(target_count):
        subcat = categories[i % len(categories)]
        img_id = f"v2_non_astro_{i+1:04d}"
        dst_filename = f"{img_id}.jpg"
        dst_path = os.path.join(NON_ASTRO_DIR, dst_filename)
        
        seed = 90000 + i
        np.random.seed(seed)
        canvas = np.zeros((224, 224, 3), dtype=np.uint8)
        
        if subcat == 'natural_scenes':
            # Forest / Landscape with bright sky
            canvas[:120, :, :] = [135, 206, 235]
            canvas[120:, :, 0] = np.random.randint(20, 60, size=(104, 224))
            canvas[120:, :, 1] = np.random.randint(100, 180, size=(104, 224))
            canvas[120:, :, 2] = np.random.randint(20, 60, size=(104, 224))
        elif subcat == 'objects_vehicles':
            # Building shape on light background
            canvas[:, :, :] = 220
            img_obj = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img_obj)
            draw.rectangle([40, 30, 184, 220], fill=(80, 90, 100))
            for wx in range(50, 170, 25):
                for wy in range(40, 200, 25):
                    draw.rectangle([wx, wy, wx+15, wy+15], fill=(255, 240, 150))
            canvas = np.array(img_obj)
        elif subcat == 'biological':
            # Portrait silhouette on light background
            canvas[:, :, :] = 240
            img_bio = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img_bio)
            draw.ellipse([62, 30, 162, 140], fill=(220, 170, 140))
            canvas = np.array(img_bio)
        elif subcat == 'graphics_ui':
            # Light mode plot
            fig, ax = plt.subplots(figsize=(2.24, 2.24), dpi=100)
            x_val = np.linspace(0, 10, 50)
            ax.plot(x_val, np.sin(x_val), color='blue')
            ax.set_title("Line Plot", fontsize=8)
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            plt.close(fig)
            buf.seek(0)
            img_p = Image.open(buf).convert('RGB').resize((224, 224))
            canvas = np.array(img_p)
        elif subcat == 'daylight_sky':
            # Blue sky gradient
            for y_idx in range(224):
                canvas[y_idx, :, 0] = int(100 + (y_idx/224)*50)
                canvas[y_idx, :, 1] = int(150 + (y_idx/224)*60)
                canvas[y_idx, :, 2] = int(180 + (y_idx/224)*75)

        canvas[0, 0, 0] = seed % 256
        canvas[0, 0, 1] = (seed * 3) % 256
        canvas[0, 0, 2] = (seed * 7) % 256
        
        img = Image.fromarray(canvas)
        img.save(dst_path, quality=95)
        sha = compute_sha256(dst_path)
        
        if sha in adv_hashes:
            continue
            
        records.append({
            'image_id': img_id,
            'filename': dst_filename,
            'path': dst_path,
            'category': subcat,
            'domain_label': 'NON_ASTRONOMICAL',
            'is_hard_sample': False,
            'source': 'Standard Non-Astronomical Generator',
            'group_id': f"non_astro_grp_{i // 10}",
            'sha256': sha,
            'notes': f"Standard non-astronomical sample ({subcat})"
        })
    return records

def generate_hard_negatives(target_count=1500, adv_hashes=set()):
    """
    Construct HARD NEGATIVE non-astronomical training pool:
    - leopard spot textures on dark tawny fur
    - India/weather rainfall radar maps with dark ocean backgrounds
    - terrestrial night scenes with streetlight sodium flares and tree silhouettes
    - sci-fi space artwork and neon planetary ring illustrations
    - dark-mode IDE screenshots and dashboard UIs
    - dark themed scientific scatter plots / heatmaps
    - telescope observatory dome silhouettes at night
    - car headlight flares on dark highway
    - concert crowd phone lights in dark
    - dark optical bokeh circles
    """
    print(f"Generating {target_count} HARD NEGATIVE non-astronomical training samples...")
    records = []
    categories = [
        "leopard_fur_textures",
        "weather_rainfall_maps",
        "night_cityscapes_streetlights",
        "scifi_space_artwork",
        "dark_ide_ui_screenshots",
        "dark_scientific_heatmaps",
        "telescope_domes_equipment",
        "vehicle_headlight_flares",
        "phone_screen_portraits",
        "dark_bokeh_wallpapers"
    ]
    
    for i in range(target_count):
        subcat = categories[i % len(categories)]
        img_id = f"v2_hard_neg_{i+1:04d}"
        dst_filename = f"{img_id}.jpg"
        dst_path = os.path.join(HARD_NEG_DIR, dst_filename)
        
        seed = 95000 + i
        np.random.seed(seed)
        size = (224, 224)
        canvas = np.zeros((224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(canvas)
        draw = ImageDraw.Draw(img)
        
        notes = f"Hard negative sample ({subcat})"
        
        if subcat == "leopard_fur_textures":
            # Leopard fur rosettes on dark tawny background
            for y in range(224):
                for x in range(224):
                    r = int(100 + 30 * np.sin(x/25) + np.random.randint(-15, 15))
                    g = int(65 + 20 * np.cos(y/25) + np.random.randint(-10, 10))
                    b = int(25 + 10 * np.sin((x+y)/35) + np.random.randint(-5, 5))
                    canvas[y, x] = [np.clip(r,0,255), np.clip(g,0,255), np.clip(b,0,255)]
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            n_rosettes = np.random.randint(12, 28)
            for _ in range(n_rosettes):
                rx, ry = np.random.randint(15, 209), np.random.randint(15, 209)
                rad = np.random.randint(7, 16)
                draw.ellipse([rx-rad, ry-rad, rx+rad, ry+rad], outline=(15, 8, 4), width=3)
                draw.ellipse([rx-rad//3, ry-rad//3, rx+rad//3, ry+rad//3], fill=(140, 85, 30))
            notes = "Leopard fur rosettes (dark tawny fur background with high contrast spot rings)"

        elif subcat == "weather_rainfall_maps":
            # Weather radar map with dark ocean background
            canvas[:, :, 0] = np.random.randint(8, 15)
            canvas[:, :, 1] = np.random.randint(15, 25)
            canvas[:, :, 2] = np.random.randint(35, 55)
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            # India map peninsula outline
            india_poly = [(112, 35), (165, 95), (145, 175), (112, 215), (79, 175), (59, 95)]
            draw.polygon(india_poly, fill=(25, 35, 45), outline=(140, 140, 150), width=2)
            # Rainfall intensity contours (yellow/red radar blobs)
            for _ in range(6):
                hx, hy = np.random.randint(75, 145), np.random.randint(55, 175)
                hr = np.random.randint(10, 25)
                draw.ellipse([hx-hr, hy-hr, hx+hr, hy+hr], fill=(255, 40, 10))
                draw.ellipse([hx-hr//2, hy-hr//2, hx+hr//2, hy+hr//2], fill=(255, 230, 0))
            # Legend bar
            draw.rectangle([175, 155, 208, 208], fill=(15, 15, 15), outline=(180, 180, 180))
            notes = "Weather radar rainfall map (dark ocean background with intense thermal contours)"

        elif subcat == "night_cityscapes_streetlights":
            # Night city skyline with sodium streetlight flares
            canvas[:, :, 0] = np.random.randint(5, 15, size=(224, 224))
            canvas[:, :, 1] = np.random.randint(5, 20, size=(224, 224))
            canvas[:, :, 2] = np.random.randint(15, 35, size=(224, 224))
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            draw.ellipse([50, 150, 190, 230], fill=(255, 140, 20)) # Streetlight sodium flare
            tree_pts = [(0, 224), (40, 130), (70, 170), (100, 100), (140, 160), (190, 110), (224, 224)]
            draw.polygon(tree_pts, fill=(5, 12, 5))
            notes = "Terrestrial night sky photo with sodium streetlight flare and tree silhouette"

        elif subcat == "scifi_space_artwork":
            # Sci-fi space artwork
            canvas[:, :, :] = [8, 2, 18]
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            draw.ellipse([50, 50, 174, 174], fill=(0, 220, 255)) # Glowing cyan planet
            draw.ellipse([15, 85, 209, 139], outline=(255, 0, 200), width=5) # Neon ring
            notes = "Sci-fi space artwork (glowing planet sphere with neon pink ring)"

        elif subcat == "dark_ide_ui_screenshots":
            # Dark mode IDE screenshot
            canvas[:, :, :] = [28, 28, 34]
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            y_off = 25
            for _ in range(8):
                draw.rectangle([20, y_off, np.random.randint(80, 190), y_off+8], fill=(97, 175, 239))
                y_off += 20
            notes = "Dark mode IDE code screenshot with syntax highlighting lines"

        elif subcat == "dark_scientific_heatmaps":
            # Dark scientific scatter plot
            canvas[:, :, :] = [12, 12, 12]
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            for _ in range(35):
                px, py = np.random.randint(30, 194), np.random.randint(30, 194)
                draw.ellipse([px-3, py-3, px+3, py+3], fill=(255, 70, 70))
            notes = "Dark scientific scatter plot (black background with bright red data points)"

        elif subcat == "telescope_domes_equipment":
            # Telescope dome at night
            canvas[:, :, 0] = np.random.randint(20, 45, size=(224, 224))
            canvas[:, :, 1] = np.random.randint(15, 30, size=(224, 224))
            canvas[:, :, 2] = np.random.randint(40, 75, size=(224, 224))
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            draw.ellipse([45, 90, 179, 235], fill=(18, 18, 22))
            draw.rectangle([95, 90, 129, 175], fill=(55, 55, 65))
            notes = "Telescope observatory dome silhouette against twilight sky"

        elif subcat == "vehicle_headlight_flares":
            # Car headlights flare on dark road
            canvas[:, :, :] = [8, 10, 15]
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            draw.ellipse([40, 110, 85, 155], fill=(255, 255, 220))
            draw.ellipse([139, 110, 184, 155], fill=(255, 255, 220))
            notes = "Night vehicle photo with bright headlight flares on dark highway"

        elif subcat == "phone_screen_portraits":
            # Face lit by smartphone screen in dark
            canvas[:, :, :] = [6, 8, 12]
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            draw.ellipse([65, 35, 159, 145], fill=(35, 65, 85))
            draw.rectangle([75, 165, 149, 224], fill=(0, 210, 255))
            notes = "Human portrait in dark room lit by mobile phone screen glow"

        elif subcat == "dark_bokeh_wallpapers":
            # Dark bokeh wallpaper
            canvas[:, :, :] = [10, 8, 16]
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            for _ in range(10):
                bx, by = np.random.randint(20, 204), np.random.randint(20, 204)
                br = np.random.randint(12, 30)
                draw.ellipse([bx-br, by-br, bx+br, by+br], outline=(255, 180, 50), width=3)
            notes = "Dark optical bokeh wallpaper with out-of-focus light rings"

        canvas_arr = np.array(img)
        canvas_arr[0, 0, 0] = seed % 256
        canvas_arr[0, 0, 1] = (seed * 3) % 256
        canvas_arr[0, 0, 2] = (seed * 7) % 256
        img_final = Image.fromarray(canvas_arr)
        img_final.save(dst_path, quality=95)
        
        sha = compute_sha256(dst_path)
        if sha in adv_hashes:
            continue
            
        records.append({
            'image_id': img_id,
            'filename': dst_filename,
            'path': dst_path,
            'category': subcat,
            'domain_label': 'NON_ASTRONOMICAL',
            'is_hard_sample': True,
            'source': 'Hard Negative Non-Astronomical Target Generator',
            'group_id': f"hard_neg_grp_{i // 10}",
            'sha256': sha,
            'notes': notes
        })
    return records

def construct_dataset_v2():
    setup_directories()
    adv_hashes = get_adversarial_hashes()
    print(f"Loaded {len(adv_hashes)} Phase 10D adversarial hashes for strict exclusion filtering.")
    
    rec_astro_gz = populate_galaxy_zoo_positives(target_count=1500, adv_hashes=adv_hashes)
    rec_astro_surv = generate_astronomical_survey_cutouts(target_count=500, adv_hashes=adv_hashes)
    rec_hard_pos = generate_hard_positives(target_count=1000, adv_hashes=adv_hashes)
    rec_non_astro = generate_non_astronomical_positives(target_count=1500, adv_hashes=adv_hashes)
    rec_hard_neg = generate_hard_negatives(target_count=1500, adv_hashes=adv_hashes)
    
    all_records = rec_astro_gz + rec_astro_surv + rec_hard_pos + rec_non_astro + rec_hard_neg
    df_all = pd.DataFrame(all_records)
    
    # Verify zero SHA256 overlap with Phase 10D adversarial test set
    overlap = set(df_all['sha256']).intersection(adv_hashes)
    if len(overlap) > 0:
        raise ValueError(f"CRITICAL ERROR: {len(overlap)} SHA256 duplicates from Phase 10D benchmark found in V2 dataset!")
    print(f"Verification Passed: 0 SHA256 duplicates with Phase 10D adversarial suite.")
    
    # Assign Group-Level TRAIN / VAL / TEST splits (70% Train, 15% Val, 15% Test)
    # Ensure all images in the same group_id stay in the same split!
    unique_groups = df_all['group_id'].unique()
    np.random.seed(42)
    np.random.shuffle(unique_groups)
    
    n_grps = len(unique_groups)
    n_train = int(n_grps * 0.70)
    n_val = int(n_grps * 0.15)
    
    train_groups = set(unique_groups[:n_train])
    val_groups = set(unique_groups[n_train:n_train+n_val])
    test_groups = set(unique_groups[n_train+n_val:])
    
    def assign_split(grp):
        if grp in train_groups:
            return 'TRAIN'
        elif grp in val_groups:
            return 'VAL'
        else:
            return 'TEST'
            
    df_all['split'] = df_all['group_id'].apply(assign_split)
    
    df_all.to_csv(MANIFEST_V2_PATH, index=False)
    df_all[['path', 'split', 'domain_label', 'category', 'is_hard_sample', 'source', 'sha256']].to_csv(SPLITS_V2_PATH, index=False)
    
    print(f"\n--- DATASET V2 CONSTRUCTION COMPLETE ---")
    print(f"Total Images: {len(df_all)}")
    print(f"Splits: TRAIN = {len(df_all[df_all['split']=='TRAIN'])}, VAL = {len(df_all[df_all['split']=='VAL'])}, TEST = {len(df_all[df_all['split']=='TEST'])}")
    print(f"Classes: ASTRONOMICAL = {len(df_all[df_all['domain_label']=='ASTRONOMICAL'])}, NON_ASTRONOMICAL = {len(df_all[df_all['domain_label']=='NON_ASTRONOMICAL'])}")
    print(f"Hard Samples: Hard Positives = {len(rec_hard_pos)}, Hard Negatives = {len(rec_hard_neg)}")
    print(f"Manifest saved to: {MANIFEST_V2_PATH}")
    print(f"Splits CSV saved to: {SPLITS_V2_PATH}")

if __name__ == '__main__':
    construct_dataset_v2()
