# ReelShot - Backend

This is the backend for the **ReelShot** application. It provides APIs to upload a video, extract frames based on similarity, and serve the extracted frames.

---

## Features

- Upload a video file.
- Extract frames using **SSIM** (Structural Similarity) or **Pixel Difference** methods.
- Store frames in a directory structure organized by unique IDs.
- Serve extracted frames as images via API.

---

## Technologies Used

- **Python**: Programming language.
- **FastAPI**: Web framework for building APIs.
- **OpenCV**: For video processing and frame extraction.
- **scikit-image**: For SSIM calculation.
- **UUID**: For generating unique IDs for each video upload.


## Directory Structure
├── main.py # FastAPI app and endpoints
├── utils/
│ ├── video_utils.py # Frame extraction logic
├── storage/ # Directory to store extracted frames
├── requirements.txt # Python dependencies
├── README.md # Project documentation


---

## **Steps to Run the Backend**

### 1. **Clone the Repository**
```bash
git clone <repository-url>
cd reel_shot
```


### 2. **Set Up a Virtual Environment (Optional but Recommended)**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Start the FastAPI server**
```bash
uvicorn main:app --reload
```

### 5. **Access API Documentation**
-Swagger UI: Visit http://127.0.0.1:8000/docs to interact with the API.

-ReDoc: Visit http://127.0.0.1:8000/redoc for API documentation.

