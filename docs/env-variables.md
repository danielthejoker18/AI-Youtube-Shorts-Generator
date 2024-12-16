# Environment Variables Documentation

This document describes all environment variables used in the AI YouTube Shorts Generator project.

## API Keys and Providers

### `LLM_PROVIDER`
- **Description**: Specifies which Language Model provider to use
- **Options**: `groq`, `openai`, `ollama`
- **Default**: `groq`
- **Example**: `LLM_PROVIDER=groq`

### `OPENAI_API_KEY`
- **Description**: API key for OpenAI services
- **Format**: String
- **Required**: Only if using OpenAI
- **Example**: `OPENAI_API_KEY=sk-...`

### `GROQ_API_KEY`
- **Description**: API key for Groq services
- **Format**: String
- **Required**: Only if using Groq
- **Example**: `GROQ_API_KEY=gsk-...`

### `OLLAMA_HOST`
- **Description**: Host for Ollama services
- **Format**: String
- **Required**: Only if using Ollama
- **Example**: `OLLAMA_HOST=http://localhost:8000`

### `YOUTUBE_API_KEY`
- **Description**: API key for YouTube Data API
- **Format**: String
- **Required**: For YouTube operations
- **Example**: `YOUTUBE_API_KEY=AIza...`

## Audio Processing

### `WHISPER_MODEL`
- **Description**: Model size for OpenAI Whisper speech recognition
- **Options**: `tiny`, `base`, `small`, `medium`, `large`
- **Default**: `base`
- **Example**: `WHISPER_MODEL=base`

### `SPEAKER_MIN_DURATION`
- **Description**: Minimum duration (in seconds) for speaker segments
- **Format**: Float
- **Default**: `0.5`
- **Example**: `SPEAKER_MIN_DURATION=0.5`

### `FACE_DETECTION_CONFIDENCE`
- **Description**: Confidence threshold for face detection
- **Format**: Float between 0 and 1
- **Default**: `0.5`
- **Example**: `FACE_DETECTION_CONFIDENCE=0.5`

## Video Processing

### `TARGET_FPS`
- **Description**: Target frames per second for output videos
- **Format**: Integer
- **Default**: `30`
- **Example**: `TARGET_FPS=30`

### `MAX_FACES`
- **Description**: Maximum number of faces to track simultaneously
- **Format**: Integer
- **Default**: `5`
- **Example**: `MAX_FACES=5`

### `CROP_RATIO`
- **Description**: Ratio for video cropping (1.0 means no crop)
- **Format**: Float between 0 and 1
- **Default**: `0.9`
- **Example**: `CROP_RATIO=0.9`

### `VERTICAL_RATIO`
- **Description**: Aspect ratio for vertical video (9:16 for Shorts)
- **Format**: Float
- **Default**: `0.5625` (9/16)
- **Example**: `VERTICAL_RATIO=0.5625`

## System Configuration

### `LOG_LEVEL`
- **Description**: Logging verbosity level
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Default**: `INFO`
- **Example**: `LOG_LEVEL=INFO`

### `CACHE_DIR`
- **Description**: Directory for caching temporary files
- **Format**: Path string
- **Default**: `cache`
- **Example**: `CACHE_DIR=cache`

## Usage

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   # Required: Choose your LLM provider and add API key
   LLM_PROVIDER=groq
   GROQ_API_KEY=your-key-here
   
   # Optional: Customize video processing
   TARGET_FPS=30
   MAX_FACES=3
   CROP_RATIO=0.85
   ```

3. The application will automatically load these variables when started.

## Security Notes

1. Never commit `.env` to version control
2. Keep API keys secure and rotate them regularly
3. Use environment-specific values for different deployments
4. Consider using a secrets manager for production
