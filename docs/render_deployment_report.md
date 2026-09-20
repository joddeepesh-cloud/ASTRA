# ASTRA — Render Free Deployment Audit Report

**Date**: September 20, 2026  
**Git Commit**: `358fd01` (`main` branch)  

---

### PLATFORM AUDIT
- **Platform**: Render Free Web Service
- **Backend URL**: N/A (Deployment aborted due to 512 MB RAM limit violation)
- **Frontend URL**: `https://2ea36865.astra-3ll.pages.dev`
- **Memory Allocation**: 512 MB RAM (Render Free limit)
- **CPU Allocation**: 0.1 shared vCPU

---

### RESOURCE AUDIT
- **Model Memory**:
  - Base Python process: **9.41 MB**
  - PyTorch runtime: **190.61 MB**
  - OpenCLIP ViT-B/32 (Semantic Gate): **1,646.36 MB**
  - MobileNetV3 (Domain Gate V2): **1,646.36 MB**
  - EfficientNet-B0 (Galaxy Zoo Triage): **2,304.84 MB**
- **Peak RSS**: **2,304.84 MB RAM** (~2.25 GB RSS memory)
- **Memory Deficit**: **-1,792.84 MB RAM** (ASTRA requires 4.5x more memory than Render Free provides)

---

### LATENCY METRICS (LOCAL BASELINE)
- **Health Latency**: **0.69 ms** p50 (Local CPU benchmark)
- **Warm Triage**: **193.41 ms** p50 (Local CPU benchmark)
- **Cold Start (Render Free)**: Estimated **50 – 90 seconds** (Exceeds 10-second target by 6x)

---

### FINAL DECISION:
🔴 **RENDER FREE CANNOT RUN ASTRA'S EXISTING ML RUNTIME**

---

### REASON & BOTTLENECK
The existing, uncompromised ASTRA ML runtime requires **2,304.84 MB RAM** (2.25 GB) to load OpenCLIP ViT-B/32, MobileNetV3, and EfficientNet-B0 into PyTorch memory. Render Free enforces a hard **512 MB RAM limit**, which causes the FastAPI application process to be killed by the Linux kernel Out-Of-Memory (OOM) killer (`exit code 137`) during process startup. Per project instructions, models were not quantized, removed, or degraded to fit the free tier.
