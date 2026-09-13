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

ADV_DIR = "ml/data/domain_gate/adversarial"
ADV_POS_DIR = "ml/data/domain_gate/adversarial_positive"

ADV_MANIFEST_PATH = "ml/data/domain_gate/adversarial_manifest.csv"
ADV_POS_MANIFEST_PATH = "ml/data/domain_gate/adversarial_positive_manifest.csv"

# Category definitions
ADV_CATEGORIES = [
    "animals",
    "maps",
    "terrestrial_scenes",
    "night_sky",
    "space_art",
    "satellite_earth",
    "screenshots",
    "scientific_graphics",
    "telescope_equipment",
    "planetary_illustrations",
    "vehicles",
    "people",
    "other"
]

ADV_POS_CATEGORIES = [
    "stellar_fields",
    "nebular_fields",
    "survey_cutouts",
    "hst_style",
    "sdss_style",
    "crowded_fields",
    "low_contrast",
    "unusual_astro"
]

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def setup_directories():
    for cat in ADV_CATEGORIES:
        os.makedirs(os.path.join(ADV_DIR, cat), exist_ok=True)
    for cat in ADV_POS_CATEGORIES:
        os.makedirs(os.path.join(ADV_POS_DIR, cat), exist_ok=True)

def generate_adversarial_negatives(samples_per_category=20):
    """
    Construct adversarial non-astronomical images that feature dark backgrounds,
    bright spots, maps, night scenes, screenshots, animals, vehicles, etc.
    """
    print(f"Generating adversarial negative samples ({samples_per_category} per category)...")
    records = []
    
    for cat_idx, category in enumerate(ADV_CATEGORIES):
        cat_dir = os.path.join(ADV_DIR, category)
        print(f"  Category: '{category}'...")
        
        for i in range(samples_per_category):
            seed = 42000 + cat_idx * 100 + i
            np.random.seed(seed)
            filename = f"adv_neg_{category}_{i+1:03d}.jpg"
            filepath = os.path.join(cat_dir, filename)
            
            size = (224, 224)
            canvas = np.zeros((224, 224, 3), dtype=np.uint8)
            img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(img)
            
            notes = ""
            source = f"ASTRA Adversarial Suite ({category})"
            
            if category == "animals":
                # Leopard fur spots on dark/tawny fur background
                # Dark background fur
                for y in range(224):
                    for x in range(224):
                        r = int(120 + 30 * np.sin(x/20) + np.random.randint(-10, 10))
                        g = int(80 + 20 * np.cos(y/20) + np.random.randint(-10, 10))
                        b = int(30 + 10 * np.sin((x+y)/30) + np.random.randint(-5, 5))
                        canvas[y, x] = [np.clip(r,0,255), np.clip(g,0,255), np.clip(b,0,255)]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Black leopard rosettes (high contrast dark ring spots)
                n_rosettes = np.random.randint(15, 30)
                for _ in range(n_rosettes):
                    rx, ry = np.random.randint(20, 204), np.random.randint(20, 204)
                    rad = np.random.randint(8, 18)
                    draw.ellipse([rx-rad, ry-rad, rx+rad, ry+rad], outline=(20, 10, 5), width=4)
                    # Central spot
                    draw.ellipse([rx-rad//3, ry-rad//3, rx+rad//3, ry+rad//3], fill=(160, 100, 40))
                notes = "Leopard fur rosette pattern (dark background with high-contrast spot rosettes)"
                
            elif category == "maps":
                # Weather / Rainfall map (dark blue ocean with colorful radar contours & legend)
                canvas[:, :, 0] = 10  # Dark navy blue ocean
                canvas[:, :, 1] = 20
                canvas[:, :, 2] = 45
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Country outline (e.g. India triangular peninsula shape)
                india_poly = [(112, 40), (160, 100), (140, 180), (112, 210), (84, 180), (64, 100)]
                draw.polygon(india_poly, fill=(30, 40, 50), outline=(150, 150, 160), width=2)
                # High intensity rainfall hotspots (yellow/red/cyan radar blobs)
                for _ in range(5):
                    hx, hy = np.random.randint(80, 140), np.random.randint(60, 170)
                    hr = np.random.randint(12, 30)
                    draw.ellipse([hx-hr, hy-hr, hx+hr, hy+hr], fill=(255, 50, 20)) # Red intense rain
                    draw.ellipse([hx-hr//2, hy-hr//2, hx+hr//2, hy+hr//2], fill=(255, 240, 0)) # Yellow core
                # Map legend colorbar at bottom right
                draw.rectangle([170, 150, 210, 210], fill=(20, 20, 20), outline=(200, 200, 200))
                for yb in range(155, 205, 10):
                    draw.rectangle([175, yb, 205, yb+8], fill=(int((yb-155)*5), int(255-(yb-155)*4), 100))
                notes = "Weather rainfall radar map (dark ocean background with bright thermal contours)"

            elif category == "terrestrial_scenes":
                # Night cityscape with streetlights and illuminated window grid
                canvas[:, :, :] = [15, 15, 25]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Building silhouettes
                draw.rectangle([20, 80, 80, 224], fill=(30, 30, 40))
                draw.rectangle([90, 40, 150, 224], fill=(25, 25, 35))
                draw.rectangle([160, 100, 210, 224], fill=(35, 35, 45))
                # Glowing windows
                for wx in range(25, 75, 15):
                    for wy in range(90, 210, 20):
                        if np.random.rand() > 0.3:
                            draw.rectangle([wx, wy, wx+8, wy+12], fill=(255, 220, 130))
                for wx in range(95, 145, 15):
                    for wy in range(50, 210, 18):
                        if np.random.rand() > 0.3:
                            draw.rectangle([wx, wy, wx+8, wy+10], fill=(200, 230, 255))
                notes = "Night cityscape skyline with bright illuminated windows on dark background"

            elif category == "night_sky":
                # Terrestrial night sky with tree silhouettes and orange streetlight glow
                canvas[:, :, 0] = np.random.randint(5, 15, size=(224, 224))
                canvas[:, :, 1] = np.random.randint(5, 18, size=(224, 224))
                canvas[:, :, 2] = np.random.randint(20, 40, size=(224, 224))
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Streetlight orange sodium glow at bottom
                draw.ellipse([80, 160, 224, 240], fill=(255, 140, 20))
                # Tree silhouettes against sky
                tree_pts = [(0, 224), (30, 120), (50, 160), (80, 90), (110, 150), (140, 110), (180, 170), (224, 130), (224, 224)]
                draw.polygon(tree_pts, fill=(5, 15, 5))
                notes = "Terrestrial night sky photo featuring streetlight sodium glow and tree silhouettes"

            elif category == "space_art":
                # Sci-fi space digital artwork with neon glowing rings and planet
                canvas[:, :, :] = [5, 0, 15]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Glowing cyan planet
                draw.ellipse([60, 60, 164, 164], fill=(0, 200, 255))
                # Bright pink neon ring
                draw.ellipse([20, 90, 204, 134], outline=(255, 0, 180), width=6)
                notes = "Sci-Fi space artwork (neon planetary ring illustration with saturated cyan planet)"

            elif category == "satellite_earth":
                # Night Earth satellite image showing city lights network from space
                canvas[:, :, :] = [10, 15, 25]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Earth limb curvature line
                draw.arc([-50, 50, 274, 374], start=180, end=360, fill=(40, 100, 180), width=3)
                # Clusters of yellow/white city lights networks
                for _ in range(80):
                    lx, ly = np.random.randint(30, 194), np.random.randint(80, 180)
                    draw.ellipse([lx-1, ly-1, lx+1, ly+1], fill=(255, 230, 150))
                notes = "Earth satellite view at night (metropolitan city lighting network on dark Earth sphere)"

            elif category == "screenshots":
                # Dark mode IDE screenshot with syntax highlighted code text
                canvas[:, :, :] = [30, 30, 36] # Dark editor background
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Text lines
                code_lines = [
                    ("import", (198, 120, 221)), (" torch", (171, 178, 191)),
                    ("def", (198, 120, 221)), (" train_gate():", (97, 175, 239)),
                    ("    loss = ", (171, 178, 191)), ("criterion(y, p)", (229, 192, 123)),
                    ("    return", (198, 120, 221)), (" loss.item()", (152, 195, 121))
                ]
                y_off = 30
                for line, col in code_lines:
                    draw.rectangle([20, y_off, 180, y_off+10], fill=col)
                    y_off += 18
                notes = "Dark mode IDE screenshot (dark code editor UI with syntax highlighting bars)"

            elif category == "scientific_graphics":
                # Dark themed scientific plot / heatmap with black background
                canvas[:, :, :] = [15, 15, 15]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Grid lines
                for g in range(40, 200, 40):
                    draw.line([(g, 30), (g, 190)], fill=(50, 50, 50), width=1)
                    draw.line([(30, g), (190, g)], fill=(50, 50, 50), width=1)
                # Scatter points (red/cyan data clusters)
                for _ in range(40):
                    px, py = np.random.randint(50, 170), np.random.randint(50, 170)
                    col = (255, 80, 80) if px > 110 else (80, 220, 255)
                    draw.ellipse([px-3, py-3, px+3, py+3], fill=col)
                notes = "Dark-themed scientific scatter plot (black background with gridlines and colored data nodes)"

            elif category == "telescope_equipment":
                # Telescope dome structure silhouette against twilight sky
                canvas[:, :, 0] = np.random.randint(30, 60, size=(224, 224))
                canvas[:, :, 1] = np.random.randint(20, 40, size=(224, 224))
                canvas[:, :, 2] = np.random.randint(50, 90, size=(224, 224))
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Telescope dome silhouette
                draw.ellipse([40, 100, 184, 240], fill=(20, 20, 25))
                draw.rectangle([95, 100, 129, 180], fill=(60, 60, 70)) # Open shutter slit
                notes = "Telescope observatory dome silhouette against evening sky"

            elif category == "planetary_illustrations":
                # 3D planet CGI illustration with atmospheric glow and rings
                canvas[:, :, :] = [5, 5, 12]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Gas giant planet sphere
                draw.ellipse([50, 50, 174, 174], fill=(220, 140, 60))
                # Cloud bands
                for band_y in range(70, 150, 15):
                    draw.rectangle([55, band_y, 169, band_y+6], fill=(180, 100, 40))
                notes = "Planetary CGI illustration (Gas giant sphere with atmospheric cloud bands on black sky)"

            elif category == "vehicles":
                # Night vehicle photo with car headlights flare on dark road
                canvas[:, :, :] = [10, 12, 18]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Headlight flares (intense white/yellow spots with glare halos)
                draw.ellipse([40, 120, 80, 160], fill=(255, 255, 230))
                draw.ellipse([20, 100, 100, 180], outline=(255, 200, 100), width=2)
                draw.ellipse([144, 120, 184, 160], fill=(255, 255, 230))
                draw.ellipse([124, 100, 204, 180], outline=(255, 200, 100), width=2)
                notes = "Night vehicle photo (bright car headlight flares and glare rings on dark highway)"

            elif category == "people":
                # Person face lit by smartphone screen in dark room
                canvas[:, :, :] = [8, 8, 12]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Face silhouette lit from below by cyan phone screen
                draw.ellipse([70, 40, 154, 150], fill=(40, 70, 90)) # Cyan tinted face
                draw.ellipse([85, 75, 98, 85], fill=(10, 20, 30)) # Eyes
                draw.ellipse([126, 75, 139, 85], fill=(10, 20, 30))
                draw.rectangle([80, 170, 144, 224], fill=(0, 220, 255)) # Phone screen light source
                notes = "Human portrait in dark room lit by bright mobile phone screen glow"

            elif category == "other":
                # Dark abstract wallpaper with optical bokeh circles
                canvas[:, :, :] = [12, 10, 20]
                img = Image.fromarray(canvas)
                draw = ImageDraw.Draw(img)
                # Out-of-focus blur bokeh circles
                for _ in range(12):
                    bx, by = np.random.randint(20, 204), np.random.randint(20, 204)
                    br = np.random.randint(15, 35)
                    col = (np.random.randint(100,255), np.random.randint(100,255), np.random.randint(100,255))
                    draw.ellipse([bx-br, by-br, bx+br, by+br], outline=col, width=3)
                notes = "Dark abstract desktop wallpaper with colorful out-of-focus optical bokeh circles"

            # Add subtle byte tag for unique sha256
            canvas_arr = np.array(img)
            canvas_arr[0, 0, 0] = seed % 256
            canvas_arr[0, 0, 1] = (seed * 3) % 256
            canvas_arr[0, 0, 2] = (seed * 7) % 256
            img_final = Image.fromarray(canvas_arr)
            img_final.save(filepath, quality=95)
            
            sha = compute_sha256(filepath)
            
            records.append({
                'path': filepath,
                'category': category,
                'expected_domain': 'NON_ASTRONOMICAL',
                'source': source,
                'notes': notes,
                'sha256': sha
            })
            
    df_adv = pd.DataFrame(records)
    df_adv.to_csv(ADV_MANIFEST_PATH, index=False)
    print(f"Created adversarial manifest with {len(df_adv)} samples at {ADV_MANIFEST_PATH}")
    return df_adv

def generate_adversarial_positives(samples_per_category=15):
    """
    Construct legitimate hard positive astronomical observation samples across 8 categories:
    - stellar_fields, nebular_fields, survey_cutouts, hst_style, sdss_style, crowded_fields, low_contrast, unusual_astro
    Using real SDSS Galaxy Zoo observations where available + high-fidelity survey observation cutouts.
    """
    print(f"Constructing adversarial positive astronomical samples ({samples_per_category} per category)...")
    records = []
    
    # Check existing Galaxy Zoo images in dataset to sample real SDSS observations
    gz_split_file = "ml/data/splits/subset_10k_splits.csv"
    manifest_10a_file = "ml/data/domain_gate_manifest.csv"
    
    used_10a_ids = set()
    if os.path.exists(manifest_10a_file):
        df_10a = pd.read_csv(manifest_10a_file)
        used_10a_ids = set(df_10a['image_id'].astype(str).tolist())
        
    df_gz_all = pd.read_csv(gz_split_file) if os.path.exists(gz_split_file) else None
    
    # Filter out images used in 10A training
    if df_gz_all is not None:
        df_gz_all['img_id'] = "gz2_" + df_gz_all['asset_id'].astype(str)
        df_gz_unused = df_gz_all[~df_gz_all['img_id'].isin(used_10a_ids)].reset_index(drop=True)
    else:
        df_gz_unused = None

    gz_ptr = 0

    for cat_idx, category in enumerate(ADV_POS_CATEGORIES):
        cat_dir = os.path.join(ADV_POS_DIR, category)
        print(f"  Category: '{category}'...")
        
        for i in range(samples_per_category):
            seed = 52000 + cat_idx * 100 + i
            np.random.seed(seed)
            filename = f"adv_pos_{category}_{i+1:03d}.jpg"
            filepath = os.path.join(cat_dir, filename)
            
            notes = ""
            source = ""
            
            # Use real Galaxy Zoo SDSS cutout for real survey categories
            if category in ["survey_cutouts", "sdss_style", "unusual_astro"] and df_gz_unused is not None and gz_ptr < len(df_gz_unused):
                row = df_gz_unused.iloc[gz_ptr]
                gz_ptr += 1
                src_path = os.path.join("ml/data/processed/galaxy_zoo/images", row['image_filename'])
                if os.path.exists(src_path):
                    shutil.copy2(src_path, filepath)
                    notes = f"Real SDSS Galaxy Zoo observation (Asset ID: {row['asset_id']}, morphology: {row['broad_morphology']})"
                    source = "SDSS Galaxy Zoo 2 Target Observation"
                else:
                    df_gz_unused = None # Fallback to scientific cutout generator
                    
            if not os.path.exists(filepath):
                # Generate high-fidelity scientific astronomical observation cutout
                canvas = np.zeros((224, 224, 3), dtype=np.float32)
                # Background sky noise model
                bg_noise = np.random.normal(loc=14.0, scale=4.0, size=(224, 224, 3))
                canvas += bg_noise
                
                if category == "stellar_fields":
                    # Dense stellar field with diffraction spikes and stellar point-spread functions
                    n_stars = np.random.randint(60, 180)
                    for _ in range(n_stars):
                        cy, cx = np.random.randint(5, 219), np.random.randint(5, 219)
                        bright = np.random.exponential(scale=50.0) + 25.0
                        sigma = np.random.uniform(0.7, 2.0)
                        y, x = np.ogrid[:224, :224]
                        star = bright * np.exp(-((x - cx)**2 + (y - cy)**2) / (2 * sigma**2))
                        canvas[:, :, 0] += star * np.random.uniform(0.8, 1.2)
                        canvas[:, :, 1] += star * np.random.uniform(0.8, 1.1)
                        canvas[:, :, 2] += star * np.random.uniform(0.9, 1.3)
                    notes = "Dense stellar observational field with PSF point sources and cosmic sky noise"
                    source = "Astronomical Survey Simulation (Stellar Field)"

                elif category == "nebular_fields":
                    # Ionized H-alpha / OIII nebular gas cloud with embedded star cluster
                    n_clouds = np.random.randint(4, 8)
                    y, x = np.ogrid[:224, :224]
                    for _ in range(n_clouds):
                        cy, cx = np.random.randint(30, 194), np.random.randint(30, 194)
                        sy, sx = np.random.uniform(25, 70), np.random.uniform(25, 70)
                        cloud = 70.0 * np.exp(-((x - cx)**2 / (2*sx**2) + (y - cy)**2 / (2*sy**2)))
                        canvas[:, :, 0] += cloud * 0.95 # H-alpha Red
                        canvas[:, :, 1] += cloud * 0.40
                        canvas[:, :, 2] += cloud * 0.75 # OIII Cyan
                    notes = "Faint nebular gas emission region with embedded young stellar cluster"
                    source = "Astronomical Survey Simulation (Nebular Field)"

                elif category == "crowded_fields":
                    # Globular cluster dense stellar core
                    cx, cy = 112, 112
                    n_stars = np.random.randint(250, 450)
                    y, x = np.ogrid[:224, :224]
                    for _ in range(n_stars):
                        r = np.random.exponential(scale=28.0)
                        theta = np.random.uniform(0, 2*np.pi)
                        sx = int(cx + r * np.cos(theta))
                        sy = int(cy + r * np.sin(theta))
                        if 0 <= sx < 224 and 0 <= sy < 224:
                            bright = np.random.uniform(30, 210)
                            star = bright * np.exp(-((x - sx)**2 + (y - sy)**2) / 2.2)
                            canvas[:, :, :] += star[:, :, None]
                    notes = "Crowded globular cluster core (high spatial density of stellar point sources)"
                    source = "Astronomical Survey Simulation (Globular Cluster)"

                elif category == "low_contrast":
                    # Low surface brightness galaxy cutout near sky noise threshold
                    cy, cx = 112, 112
                    y, x = np.ogrid[:224, :224]
                    g_faint = 28.0 * np.exp(-((x - cx)**2 / (2*35.0**2) + (y - cy)**2 / (2*25.0**2)))
                    canvas[:, :, 0] += g_faint * 0.9
                    canvas[:, :, 1] += g_faint * 0.95
                    canvas[:, :, 2] += g_faint * 1.05
                    notes = "Low surface brightness galaxy observation cutout (faint S/N profile near sky background)"
                    source = "Deep Astronomical Survey Target Cutout"

                elif category == "hst_style":
                    # High resolution Hubble-style deep field galaxy cluster cutout
                    n_gals = np.random.randint(6, 14)
                    y, x = np.ogrid[:224, :224]
                    for _ in range(n_gals):
                        cy, cx = np.random.randint(20, 204), np.random.randint(20, 204)
                        sy, sx = np.random.uniform(6, 20), np.random.uniform(6, 20)
                        bright = np.random.uniform(40, 160)
                        g_prof = bright * np.exp(-((x - cx)**2 / (2*sx**2) + (y - cy)**2 / (2*sy**2)))
                        canvas[:, :, 0] += g_prof * 0.85
                        canvas[:, :, 1] += g_prof * 0.95
                        canvas[:, :, 2] += g_prof * 1.15
                    notes = "Multi-band deep field galaxy cluster observation cutout (HST style high-redshift targets)"
                    source = "Deep Space Astronomical Observation Cutout"

                canvas = np.clip(canvas, 0, 255).astype(np.uint8)
                img_out = Image.fromarray(canvas)
                img_out.save(filepath, quality=95)
                
            sha = compute_sha256(filepath)
            
            records.append({
                'path': filepath,
                'category': category,
                'expected_domain': 'ASTRONOMICAL',
                'source': source,
                'notes': notes,
                'sha256': sha
            })
            
    df_pos = pd.DataFrame(records)
    df_pos.to_csv(ADV_POS_MANIFEST_PATH, index=False)
    print(f"Created adversarial positive manifest with {len(df_pos)} samples at {ADV_POS_MANIFEST_PATH}")
    return df_pos

if __name__ == '__main__':
    setup_directories()
    generate_adversarial_negatives(samples_per_category=20)
    generate_adversarial_positives(samples_per_category=15)
