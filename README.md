# 🎨 PaletteVision

A lightweight **FastAPI** service that extracts dominant colors from an uploaded image.
Uses **K-Means clustering** by default (fast and deterministic) and supports **Mean Shift** as an optional algorithm.

---

## ✨ Features

* Extracts **primary and secondary colors** (top N) from images.
* Supports multiple output formats: `hex`, `rgb`, `rgba`, `hsl`.
* Default algorithm: `kmeans` — optionally switch to `meanshift`.
* Returns percentage distribution of each dominant color.
* Handles both **file uploads** and **base64-encoded images**.

---

## ⚙️ Requirements

* Python **3.9+**
* Dependencies listed in `requirements.txt`

---

## 🚀 Quick Start (Virtual Environment)

```bash
python -m venv .venv
source .venv/Scripts/activate    # On Windows (Git Bash / bash.exe)
pip install -r requirements.txt
uvicorn main:app --reload
```

App will run locally at **[http://127.0.0.1:8000](http://127.0.0.1:8000)**
Swagger Docs: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
Redoc UI: **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)**

---

## 📤 Example (File Upload)

```bash
curl -X POST "http://127.0.0.1:8000/dominant-colors" \
  -F "file=@./sample.jpg" \
  -F "format=hex" \
  -F "algorithm=kmeans" \
  -F "k=3" \
  -F "top_n=2" \
  -F "include_percentage=true"
```

---

## 🧩 Example (Base64 JSON)

This method keeps the image fully in memory — useful for web clients or APIs that can’t send files directly.

```bash
curl -X POST "http://127.0.0.1:8000/dominant-colors/base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
    "format": "hex",
    "algorithm": "kmeans",
    "k": 3,
    "top_n": 2,
    "include_percentage": true
  }'
```

---

## 🧾 Example Response

```json
{
  "colors": [
    {"value": "#1f77b4", "percentage": 61.2345},
    {"value": "#ff7f0e", "percentage": 20.1234}
  ],
  "algorithm": "kmeans",
  "format": "hex"
}
```

---

## ⚠️ Notes & Edge Cases

* **MeanShift** may be slower and produce many small clusters —
  only the **top N clusters** (by pixel count) are returned.
* For large images, the app **auto-resizes** the largest dimension to **800px** for faster processing.
* If fewer clusters than requested are found, the **primary color** is duplicated to maintain output consistency.
