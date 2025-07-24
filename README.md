<div align="center">

# 🎤 SWHA Backend API

**A comprehensive Software with Human-AI (SWHA) backend built with FastAPI, featuring real-time AI capabilities, video streaming, and secure cloud integration.**

</div>

---

## ✨ Key Features

A robust platform designed for modern AI-driven applications, providing a wide array of features out-of-the-box.

| Category               | Feature                                                              |
| ---------------------- | -------------------------------------------------------------------- |
| 🤖 **AI & Machine Learning** | Real-time Speech-to-Text (WebSocket), Text-to-Speech, QA, Lip Sync |
| 🎥 **Media Processing**    | Video Streaming (Range Support), Uploads, Thumbnail Generation       |
| 🔐 **Core Services**     | JWT Authentication, User Management, Database with Migrations        |
| ☁️ **DevOps & Deployment** | Docker & Nginx Deployment, AWS S3 Integration, Health Checks         |

---

## 🚀 Getting Started

Get the application up and running in minutes. Docker is the recommended method for a seamless setup.

### Option 1: Docker Deployment (Recommended)

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd swha-backend
    ```

2.  **Configure Environment**
    ```bash
    cp .env.template .env
    # Edit .env with your database, secrets, and AWS credentials
    ```

3.  **Run the Quick Deploy Script**
    ```bash
    chmod +x quick-deploy.sh
    ./quick-deploy.sh
    ```
    This script handles Docker installation, builds the images, and starts the services.

### Option 2: Manual Local Setup

1.  **Create Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure & Run**
    ```bash
    # Set up your .env file as in the Docker setup
    alembic upgrade head
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

---

## 🔌 API Endpoints & Usage

The API is structured logically by resource. All endpoints are prefixed with `/api/v1`. Interactive documentation is available at `/docs` when the server is running.

### Feature Highlight: Real-time Speech-to-Text (WebSocket)

This endpoint provides continuous, low-latency transcription of audio streams.

#### 1. Connection

-   **Endpoint**: `ws://<HOST>/api/v1/stt/ws/transcribe?token=<ACCESS_TOKEN>`
-   **Authentication**: A valid JWT must be passed as the `token` query parameter.

#### 2. Message Protocol

The client-server communication follows a simple, event-driven protocol:

| From         | Message                  | Type     | Description                                         |
| ------------ | ------------------------ | -------- | --------------------------------------------------- |
| **Client**   | `start_recording`        | `Text`   | Initializes a new transcription session.            |
| **Client**   | `<audio_data>`           | `Binary` | An audio chunk (e.g., from MediaRecorder).          |
| **Client**   | `stop_recording`         | `Text`   | Ends the session and requests the final summary.    |
| **Server**   | `{"type":"connected"}`   | `JSON`   | Confirms the WebSocket connection is ready.         |
| **Server**   | `{"type":"chunk_received"}`| `JSON`   | Acknowledges receipt of an audio chunk.             |
| **Server**   | `{"type":"partial_transcription"}`| `JSON`| A real-time transcription result.                   |
| **Server**   | `{"type":"session_complete"}`| `JSON` | The final, aggregated transcription for the session.|

#### 3. Frontend Integration Example (JavaScript)

This example demonstrates how to connect, stream audio from the browser's microphone, and handle real-time results.

```javascript
// 1. Setup WebSocket and Audio Recorder
const token = 'YOUR_JWT_TOKEN';
const ws = new WebSocket(`ws://localhost:8000/api/v1/stt/ws/transcribe?token=${token}`);
const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });

// 2. Handle Connection and Server Messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'partial_transcription') {
        console.log('Live transcription:', data.text);
    } else if (data.type === 'session_complete') {
        console.log('Final transcription:', data.full_text);
    }
};

ws.onopen = () => {
    console.log('Connection ready. Starting recording session...');
    ws.send('start_recording');
    recorder.start(250); // Send a chunk every 250ms
};

// 3. Send Audio Data
recorder.ondataavailable = async (event) => {
    if (event.data.size > 0) {
        const audioBuffer = await event.data.arrayBuffer();
        ws.send(audioBuffer);
    }
};

// 4. Stop the Session
function stop() {
    recorder.stop();
    ws.send('stop_recording');
}
```

### Other Key Endpoints

-   **Authentication**: `POST /auth/login`, `POST /auth/register`
-   **Question Answering**: `POST /qa/answer`
-   **Text-to-Speech**: `POST /tts/generate`
-   **Lip Synchronization**: `POST /lipsync/create`
-   **Video Management**: `GET /videos`, `GET /videos/{id}/stream`
-   **File Uploads**: `POST /upload/video`

---

## 🛠️ Technology Stack

| Area                   | Technologies                                                                 |
| ---------------------- | ---------------------------------------------------------------------------- |
| **Framework & Server** | FastAPI, Uvicorn, Starlette                                                  |
| **AI & ML**            | PyTorch, Transformers, Whisper, Kokoro                                       |
| **Database**           | PostgreSQL, SQLAlchemy, Alembic                                              |
| **Media**              | OpenCV, FFmpeg, Pillow                                                       |
| **Deployment**         | Docker, Docker Compose, Nginx, AWS S3                                        |

---

## 🔧 Development & Contributing

### Running Tests

```bash
pytest
```

### Code Style

This project uses `black` for code formatting.
```bash
black .
```

### Database Migrations

When you change a SQLAlchemy model, create a new migration:
```bash
alembic revision --autogenerate -m "Your migration description"
alembic upgrade head
```

### Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details. 