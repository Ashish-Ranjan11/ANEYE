# 👁️ ANEYE

> **AI-Powered Retinal Disease Analysis Platform for Early Ophthalmic Screening**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-red?logo=pytorch)
![Status](https://img.shields.io/badge/Status-Active%20Development-success)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

ANEYE is an AI-powered retinal disease analysis platform designed to assist in the early screening of ophthalmic diseases from retinal fundus images.

The project combines deep learning, medical image preprocessing, and modular AI engineering to build a scalable and research-ready clinical decision support system. It is currently built around an EfficientNet baseline and is designed to evolve into a comprehensive retinal intelligence platform with explainable AI and anatomical reasoning.

---

## Current Features

- ✅ ODIR-5K retinal dataset integration
- ✅ Automated dataset validation pipeline
- ✅ Metadata generation and label management
- ✅ Medical image preprocessing
- ✅ EfficientNet-B0 baseline classifier
- ✅ Class-balanced model training
- ✅ Evaluation pipeline (Accuracy, Precision, Recall, F1 Score)
- ✅ Retinal disease inference engine
- ✅ Confidence estimation
- ✅ Clinical recommendation generation

---

## Supported Diseases

- Normal
- Cataract
- Diabetic Retinopathy
- Glaucoma
- Age-related Macular Degeneration (AMD)
- Hypertensive Retinopathy
- Myopia
- Other Retinal Diseases

---

## Project Structure

```text
AnEye/
├── ai/
│   ├── datasets/
│   ├── preprocessing/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   └── models/
│
├── backend/
├── frontend/
├── datasets/
├── docs/
├── research/
├── scripts/
└── tests/
```

---

## Baseline Performance

| Metric | Score |
|---------|--------|
| Accuracy | **78.73%** |
| Precision | **80.71%** |
| Recall | **78.73%** |
| F1 Score | **78.88%** |

---

## Technology Stack

- Python
- PyTorch
- TorchVision
- OpenCV
- NumPy
- Pandas
- scikit-learn

---

## Current AI Pipeline

```text
Retinal Fundus Image
        │
        ▼
Image Validation
        │
        ▼
Preprocessing
        │
        ▼
EfficientNet-B0
        │
        ▼
Disease Classification
        │
        ▼
Confidence Estimation
        │
        ▼
Clinical Recommendation
```

---

## Future Roadmap

The platform is being developed toward a research-oriented retinal AI framework with planned support for:

- RETFound foundation model
- Image Quality Assessment
- CycleGAN-based image enhancement
- Anatomical segmentation
- Biomarker extraction
- Vessel graph representation
- Anatomy-aware feature fusion
- Multi-task learning
- Explainable AI
- FastAPI backend
- React frontend

---

## Disclaimer

ANEYE is an academic and research project intended for educational purposes only. It is **not** a medical device and should not be used for clinical diagnosis.

---

## License

MIT License

