# ASTRA — Free Backend Feasibility & Resource Audit

**Date**: September 20, 2026  
**Git Commit**: `7ecb31e` (`main` branch)  
**Target Platform**: Render Free Web Service  
**Final Decision**: 🔴 **FREE BACKEND UNSUITABLE FOR ASTRA**  

---

## 1. Executive Summary

Render Free provides **512 MB RAM** (0.5 GB) and **0.1 shared vCPU**. Empirical memory profiling of the untampered ASTRA ML pipeline demonstrates that process startup and model loading requires **2,304.84 MB RAM** (~2.25 GB RSS memory). 

Because ASTRA requires **4.5x more memory than Render Free provides**, deploying the existing ASTRA ML backend to Render Free triggers an immediate Linux kernel Out-Of-Memory (OOM) process termination (`exit code 137` / SIGKILL) during application lifespan startup. Per project requirements, no models were quantized, removed, or degraded to fit the free tier.

---

## 2. Empirical Memory Footprint Breakdown

All measurements were executed directly on the repository codebase using PyTorch 2.4 CPU runtime (`ASTRA_DEVICE=cpu`):

| Pipeline Stage / Component | Memory (RSS) | Incremental RAM | Render Free Limit | Margin / Deficit |
| :--- | :--- | :--- | :--- | :--- |
| **Base Python 3.11 Process** | 9.41 MB | +9.41 MB | 512.0 MB | +502.59 MB |
| **PyTorch Runtime Import** | 190.61 MB | +181.20 MB | 512.0 MB | +321.39 MB |
| **OpenCLIP ViT-B/32 (Semantic Gate)** | 1,646.36 MB | +1,455.75 MB | 512.0 MB | 🔴 **-1,134.36 MB (OOM)** |
| **MobileNetV3 (Domain Gate V2)** | 1,646.36 MB | +0.00 MB | 512.0 MB | 🔴 **-1,134.36 MB (OOM)** |
| **EfficientNet-B0 (Galaxy Zoo Triage)** | 2,304.84 MB | +658.48 MB | 512.0 MB | 🔴 **-1,792.84 MB (OOM)** |
| **Full Lifespan Startup & Warmup Pass** | **2,304.84 MB** | — | **512.0 MB** | 🔴 **-1,792.84 MB (OOM)** |
| **Peak RSS During Triage Inference** | **2,304.84 MB** | — | **512.0 MB** | 🔴 **-1,792.84 MB (OOM)** |

---

## 3. CPU & Inactivity Latency Audit

- **Render Free CPU Allocation**: 0.1 vCPU (shared CPU time-slice).
- **Estimated Cold-Start Spin-Up**: **50 – 90 seconds** (Container spin-up + PyTorch CPU package initialization + OpenCLIP weight deserialization).
- **Target Comparison**:
  - Required Cold-Start Target: **≤ 10 seconds**
  - Render Free Cold-Start Behavior: **~60 seconds** (FAILS requirement by 6x).
  - Required Warm Triage Target: **≤ 5 seconds**

---

## 4. Hardware Resource Requirements for ASTRA

To run the full, uncompromised ASTRA ML backend in production with warm triage latency < 500 ms:

- **RAM**: **2 GB minimum** (4 GB recommended for OS & system overhead).
- **CPU**: **2 vCPU minimum** (x86_64 or ARM64).
- **Process Supervisor**: Systemd or Gunicorn with 1 warm worker process.
- **Recommended Free Hosting Options**:
  1. **Oracle Cloud Infrastructure (OCI) Always Free**: 4 ARM vCPU / 24 GB RAM instance (100% Free forever, requires standard credit card verification during signup).
  2. **Dedicated Cloud VPS**: 2 vCPU / 4 GB RAM instance.

---

## 5. Final Decision Matrix

```
[ ] 🟢 FREE DEMO BACKEND WORKS
[ ] 🟡 FREE BACKEND WORKS BUT HAS COLD-START / PERFORMANCE LIMITATIONS
[X] 🔴 FREE BACKEND UNSUITABLE FOR ASTRA
```
