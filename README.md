<div align="center">

# 👁️ AnEye

### AI-Powered Retinal Disease Analysis Platform for Early Ophthalmic Screening

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Vision%20Transformer-purple?style=for-the-badge)

---

**AnEye is an AI-assisted retinal disease screening platform designed to support early ophthalmic diagnosis using deep learning, explainable AI, and retinal biomarker analysis.**

</div>

---

# 📖 Overview

AnEye is a research-oriented intelligent eye disease screening platform that combines modern computer vision, explainable AI, retinal biomarker extraction, and deep learning to detect retinal diseases from fundus images.

The platform is designed to assist clinicians by providing:

- Disease prediction
- Severity estimation
- Explainable AI visualizations
- Retinal biomarker measurements
- Clinical recommendation support

---

# ✨ Features

## 🧠 AI Disease Detection

- Vision Transformer (ViT)
- RETFound pretrained backbone
- Multi-class retinal disease classification
- Confidence scoring

Supported diseases:

- Diabetic Retinopathy
- Glaucoma
- Age Related Macular Degeneration
- Cataract
- Hypertensive Retinopathy
- Macular Edema
- Retinal Vein Occlusion
- Healthy Retina

---

## 🔬 Explainable AI

- Grad-CAM++
- Attention Maps
- Saliency Visualization
- Clinical Region Highlighting

---

## 👁 Retinal Biomarker Extraction

Automatically measures

- Cup-to-Disc Ratio
- Vessel Density
- Vessel Tortuosity
- Exudate Area
- Hemorrhage Count
- Microaneurysm Count
- Drusen Area
- Optic Disc Measurements

---

## 📊 Severity Analysis

- Mild
- Moderate
- Severe
- Proliferative

Disease progression tracking included.

---

## 🤖 Clinical Decision Support

Provides

- Risk Assessment
- Referral Recommendation
- Follow-up Suggestions
- Confidence Score

---

# 🏗 System Architecture

```text
Fundus Image
      │
      ▼
Image Enhancement
      │
      ▼
Retinal Segmentation
      │
      ▼
Biomarker Extraction
      │
      ▼
Vision Transformer
      │
      ▼
Disease Classification
      │
      ▼
Explainable AI
      │
      ▼
Clinical Report
```

---

# 🧬 AI Pipeline

```
Input Fundus Image

↓

GAN Image Enhancement

↓

U-Net Segmentation

↓

Biomarker Extraction

↓

Vision Transformer

↓

Disease Prediction

↓

Severity Grading

↓

Explainable AI

↓

Clinical Recommendation
```

---

# 🛠 Tech Stack

| Category | Technology |
|-----------|------------|
| Backend | FastAPI |
| AI Framework | PyTorch |
| Computer Vision | OpenCV |
| Explainability | GradCAM |
| Segmentation | U-Net |
| Transformer | Vision Transformer |
| Database | PostgreSQL |
| Frontend | React |
| Deployment | Docker |

---

# 📂 Project Structure

```
AnEye/

├── backend/
│   ├── api/
│   ├── models/
│   ├── inference/
│   ├── segmentation/
│   ├── biomarkers/
│   ├── xai/
│   └── reports/
│
├── frontend/
│   ├── src/
│   ├── components/
│   └── assets/
│
├── datasets/
├── notebooks/
├── weights/
├── docs/
└── README.md
```

---

# 📈 Roadmap

- [x] Disease Classification
- [x] Explainable AI
- [x] Biomarker Extraction
- [ ] Clinical Dashboard
- [ ] Progress Tracking
- [ ] Doctor Portal
- [ ] Multi-language Reports
- [ ] Cloud Deployment

---

# 📚 Datasets

The project utilizes publicly available retinal datasets including:

- APTOS 2019
- IDRiD
- MESSIDOR-2
- PAPILA
- REFUGE
- OCTID
- EyePACS

---

# 📄 Research Motivation

Millions of people worldwide suffer from preventable blindness due to delayed diagnosis of retinal diseases.

AnEye aims to bridge the gap between AI and ophthalmology by providing an explainable, biomarker-aware, clinician-friendly screening platform.

---

# 👨‍💻 Author

**Ashish Ranjan**

AI Research • Computer Vision • Deep Learning

GitHub: https://github.com/Ashish-Ranjan11

LinkedIn: https://www.linkedin.com/in/ashish-ranjan-77a422371

---

<div align="center">

### ⭐ If you like this project, consider giving it a star ⭐

</div>

## License

MIT License
