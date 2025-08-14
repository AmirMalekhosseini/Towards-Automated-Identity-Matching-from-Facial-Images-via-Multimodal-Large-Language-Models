# Automated Identity Matching using Multimodal LLMs

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the code and resources for the project, **"Towards Automated Identity Matching from Facial Images via Multimodal Large Language Models."**

This project introduces a novel framework that goes beyond traditional facial recognition. Instead of just matching faces, it ascertains a person's real-world identity by synergizing computer vision techniques with the advanced reasoning capabilities of Multimodal Large Language Models (LLMs).

## 📜 Abstract

The proliferation of digital imagery has created significant challenges in automated identity verification. Traditional systems excel at matching images but lack the contextual understanding to determine a person's identity. This project proposes a novel pipeline that uses a facial image to perform a reverse image search, gathers a corpus of web pages, and then leverages a powerful LLM (Gemma) to analyze the textual and semantic content of these pages to confidently determine the individual's name, role, and background.

## ✨ Key Features

* **Image Preprocessing:** Cleans and prepares input images using Gaussian and Median filters for denoising.
* **Background Segmentation:** Employs a pre-trained **U-Net** to isolate the human subject from the background, reducing noise and focusing the analysis.
* **High-Fidelity Face Extraction:** Uses a **Multi-task Cascaded Convolutional Network (MTCNN)** for robust, multi-face detection and alignment.
* **AI-Powered Super-Resolution:** Enhances the resolution of extracted faces using a **Super-Resolution Generative Adversarial Network (SRGAN)** to ensure a high-quality query image.
* **Web-Scale Information Retrieval:** Submits the enhanced facial image to a reverse image search engine to gather relevant URLs.
* **LLM-Powered Analysis:** Leverages the **Gemma** multimodal model to analyze full-page screenshots of retrieved URLs, understanding text, images, and layout contextually.
* **Structured Data Output:** Synthesizes the findings into a structured JSON object containing the person's name, affiliations, a background summary, and the source URLs for transparency.

## 🚀 How It Works

The system operates as a multi-stage pipeline, systematically processing an input image to produce a confident identity claim.

1.  **Stage 1: Preprocessing:** The input image is enhanced and denoised. The background is removed using a U-Net to isolate the subject.
2.  **Stage 2: Face Extraction:** An MTCNN detects and crops faces from the image. The resulting low-resolution crop is then upscaled using an SRGAN to improve clarity.
3.  **Stage 3: Information Retrieval:** The high-resolution face is used as a query in a reverse image search to collect a list of web pages where the image appears.
4.  **Stage 4: LLM Analysis:** The system captures screenshots of the top search results and feeds them to the Gemma LLM, which analyzes the content—including headlines, captions, and text—to deduce the person's identity.
5.  **Output:** The final result is a structured JSON object containing the identified name, roles, a brief background, and source URLs.

## 💻 Technologies Used

* **AI / ML**
    * **Gemma:** For multimodal analysis of web content.
    * **U-Net:** For background-foreground segmentation.
    * **MTCNN (Multi-task Cascaded Convolutional Network):** For high-accuracy face detection.
    * **SRGAN (Super-Resolution Generative Adversarial Network):** For enhancing the quality of cropped facial images.
* **Computer Vision**
    * **OpenCV (implied):** Used for classic image processing filters like Gaussian Blur and Median Filter.
* **Core Stack**
    * **Python:** The primary programming language for the pipeline.
    * **Reverse Image Search API (e.g., Google Images):** For web-scale information retrieval.


