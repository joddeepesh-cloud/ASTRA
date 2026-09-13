# ASTRA Demo Data Pack

This directory contains representative test images for live upload demonstration and end-to-end verification.

---

## Demo Files & Expected Domain Behavior

| Filename | Source Origin | Target Visual Domain | Expected Domain Decision | Expected Downstream Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `astronomy_galaxy_smooth.jpg` | Galaxy Zoo 2 (`20027.jpg`) | Smooth astronomical galaxy cutout | `COMPATIBLE` ($P \ge 0.80$) | Executes Galaxy Zoo morphology (`SMOOTH`) & scientific triage engine. |
| `astronomy_galaxy_disk.jpg` | Galaxy Zoo 2 (`100035.jpg`) | Disk/Featured galaxy cutout | `COMPATIBLE` ($P \ge 0.80$) | Executes Galaxy Zoo morphology (`FEATURED_DISK`) & scientific triage engine. |
| `astronomy_galaxy_edgeon.jpg` | Galaxy Zoo 2 (`100047.jpg`) | Edge-on disk galaxy cutout | `COMPATIBLE` ($P \ge 0.80$) | Executes Galaxy Zoo morphology (`EDGE_ON`) & scientific triage engine. |
| `non_astronomy_terrestrial.jpg` | Non-Astronomy Dataset (`non_astro_0001.jpg`) | Terrestrial photo (Dog/Pet) | `INCOMPATIBLE` ($P \le 0.20$) | Rejects upload. Skips Galaxy Zoo classifier & triage engine. |
| `non_astronomy_artwork.jpg` | Non-Astronomy Dataset (`non_astro_0010.jpg`) | Digital space artwork / graphic | `INCOMPATIBLE` ($P \le 0.20$) | Rejects upload. Skips Galaxy Zoo classifier & triage engine. |

---

## Demo Golden Path
1. Open Research Mode in ASTRA Frontend.
2. Upload `astronomy_galaxy_smooth.jpg` $\rightarrow$ Observe `ASTRONOMICAL DOMAIN VERIFIED`, predicted `SMOOTH` class, and triage score.
3. Upload `non_astronomy_terrestrial.jpg` $\rightarrow$ Observe `DOMAIN VALIDATION FAILED — INCOMPATIBLE` rejection banner with safe scientific message.
