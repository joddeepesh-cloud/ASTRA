import numpy as np
from PIL import Image
from typing import Dict, Any

def analyze_point_source_structure(image: Image.Image) -> Dict[str, Any]:
    """
    Computes image-derived structural & morphology metrics from a single astronomical image cutout.
    
    Calculates 10 robust, lightweight structural measurements:
    1. Background estimate (median bg level, std)
    2. Peak intensity
    3. Peak/background ratio
    4. Radial energy concentration (r<=4px / r<=16px)
    5. Compactness
    6. FWHM approximation in pixels
    7. Extended-vs-point-source indication score
    8. Diffuse emission indication score
    9. Bright connected-region characteristics (area, asymmetry/eccentricity proxy)
    10. Spatial concentration / dispersion (r^2 moment of intensity)

    Returns pure image-derived measurements (NOT probabilities).
    """
    try:
        # Convert PIL image to grayscale numpy float array [0, 1]
        gray = np.array(image.convert("L"), dtype=np.float32) / 255.0
        h, w = gray.shape

        if h < 8 or w < 8:
            return {
                "bg_level": 0.0,
                "bg_std": 0.0,
                "peak_intensity": 0.0,
                "peak_to_bg": 1.0,
                "concentration_ratio": 0.0,
                "compactness": 0.0,
                "fwhm_proxy_px": 0.0,
                "extent_px": 0,
                "extended_score": 0.0,
                "diffuse_emission_score": 0.0,
                "point_source_score": 0.0,
                "connected_region_area": 0,
                "connected_asymmetry": 0.0,
                "spatial_dispersion": 0.0,
                "is_point_source_like": False,
                "is_diffuse_like": False,
                "is_extended_like": False,
                "evidence_strength": "NONE"
            }

        # 1. Background estimate (median and std of outer border pixels)
        border_mask = np.ones((h, w), dtype=bool)
        border_mask[2:-2, 2:-2] = False
        bg_level = float(np.median(gray[border_mask]))
        bg_std = float(np.std(gray[border_mask])) + 1e-6

        # Subtract background
        sub = np.maximum(gray - bg_level, 0.0)

        # 2. Peak intensity
        peak_intensity = float(np.max(gray))

        # 3. Peak to background ratio
        peak_to_bg = float((peak_intensity + 1e-6) / (bg_level + 1e-6))

        cy, cx = h / 2.0, w / 2.0
        y_indices, x_indices = np.indices((h, w))
        r_dist = np.sqrt((x_indices - cx) ** 2 + (y_indices - cy) ** 2)

        # 4. Concentric energy sums & radial energy concentration
        inner_energy = float(np.sum(sub[r_dist <= 4.0]))
        outer_energy = float(np.sum(sub[r_dist <= 16.0])) + 1e-8
        concentration = float(inner_energy / outer_energy)

        # Active pixel count above 3-sigma noise threshold
        active_mask = sub > (3.0 * bg_std)
        extent_px = int(np.sum(active_mask))

        # 6. FWHM proxy (radius/diameter where intensity drops below 50% of peak above background)
        peak_diff = peak_intensity - bg_level
        if peak_diff > 1e-4:
            half_peak_mask = sub >= (peak_diff * 0.5)
            fwhm_proxy_px = float(2.0 * np.sqrt(np.sum(half_peak_mask) / np.pi))
        else:
            fwhm_proxy_px = float(max(h, w))

        # 5. Compactness
        compactness = float(min(1.0, concentration * (1.0 / (1.0 + fwhm_proxy_px * 0.08))))

        # 10. Spatial dispersion (second radial moment of intensity)
        total_sub_intensity = float(np.sum(sub)) + 1e-8
        spatial_dispersion = float(np.sum(sub * (r_dist ** 2)) / total_sub_intensity)

        # 9. Connected region characteristics (area & asymmetry/eccentricity proxy)
        connected_region_area = extent_px
        mu20 = float(np.sum(((x_indices - cx) ** 2) * sub) / total_sub_intensity)
        mu02 = float(np.sum(((y_indices - cy) ** 2) * sub) / total_sub_intensity)
        mu11 = float(np.sum(((x_indices - cx) * (y_indices - cy)) * sub) / total_sub_intensity)
        denom = mu20 + mu02 + 1e-8
        connected_asymmetry = float(np.sqrt(max(0.0, (mu20 - mu02) ** 2 + 4.0 * (mu11 ** 2))) / denom)

        # 7 & 8. Structural scores (Extended, Diffuse, Point Source)
        total_pixels = float(h * w)
        extended_score = float(np.clip(
            (extent_px / (total_pixels * 0.15)) * 0.4 +
            (1.0 - min(1.0, concentration)) * 0.4 +
            (min(1.0, fwhm_proxy_px / 18.0)) * 0.2,
            0.0, 1.0
        ))

        diffuse_emission_score = float(np.clip(
            (extent_px / (total_pixels * 0.25)) * 0.4 +
            (1.0 - min(1.0, concentration)) * 0.4 +
            (min(1.0, spatial_dispersion / 200.0)) * 0.2,
            0.0, 1.0
        ))

        point_source_score = float(np.clip(
            concentration * 0.45 +
            (1.0 - min(1.0, fwhm_proxy_px / 14.0)) * 0.35 +
            min(1.0, (peak_to_bg - 1.0) / 3.0) * 0.20,
            0.0, 1.0
        ))

        # Structural classification heuristics
        is_point_source = bool(point_source_score >= 0.55 and concentration >= 0.50 and fwhm_proxy_px <= 14.0 and peak_to_bg >= 1.3)
        is_diffuse = bool(diffuse_emission_score >= 0.45 and extent_px > 100 and concentration < 0.42)
        is_extended = bool(extended_score >= 0.45 and extent_px > 75)

        if is_point_source and concentration >= 0.70:
            strength = "STRONG"
        elif is_point_source:
            strength = "MODERATE"
        elif is_diffuse:
            strength = "DIFFUSE"
        elif is_extended:
            strength = "EXTENDED"
        else:
            strength = "WEAK"

        return {
            "bg_level": round(bg_level, 4),
            "bg_std": round(bg_std, 4),
            "peak_intensity": round(peak_intensity, 4),
            "peak_to_bg": round(peak_to_bg, 2),
            "concentration_ratio": round(concentration, 4),
            "compactness": round(compactness, 4),
            "fwhm_proxy_px": round(fwhm_proxy_px, 2),
            "extent_px": extent_px,
            "extended_score": round(extended_score, 4),
            "diffuse_emission_score": round(diffuse_emission_score, 4),
            "point_source_score": round(point_source_score, 4),
            "connected_region_area": connected_region_area,
            "connected_asymmetry": round(connected_asymmetry, 4),
            "spatial_dispersion": round(spatial_dispersion, 2),
            "is_point_source_like": is_point_source,
            "is_diffuse_like": is_diffuse,
            "is_extended_like": is_extended,
            "evidence_strength": strength
        }

    except Exception:
        return {
            "bg_level": 0.0,
            "bg_std": 0.0,
            "peak_intensity": 0.0,
            "peak_to_bg": 1.0,
            "concentration_ratio": 0.0,
            "compactness": 0.0,
            "fwhm_proxy_px": 0.0,
            "extent_px": 0,
            "extended_score": 0.0,
            "diffuse_emission_score": 0.0,
            "point_source_score": 0.0,
            "connected_region_area": 0,
            "connected_asymmetry": 0.0,
            "spatial_dispersion": 0.0,
            "is_point_source_like": False,
            "is_diffuse_like": False,
            "is_extended_like": False,
            "evidence_strength": "NONE"
        }
