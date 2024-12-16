# API Documentation

## Core Components

### VideoProcessor

Main class for video processing and shorts generation.

```python
from Components.video_processor import VideoProcessor

processor = VideoProcessor(
    video_path="path/to/video.mp4",
    output_dir="results",
    target_fps=30,
    face_detection_confidence=0.5,
    max_faces=3
)
```

#### Methods
- `process_video_segments(segments: List[dict], output_path: str)`: Process video segments into a short
- `process_frame(frame: np.ndarray)`: Process a single frame with face detection and smart crop

### YouTubeScraper

Handles video discovery and downloading from YouTube.

```python
from Components.youtube_scraper import YouTubeScraper

scraper = YouTubeScraper(
    download_path="downloads",
    min_views=10000,
    max_duration=600,
    max_days_old=7
)
```

#### Methods
- `search_videos(query: str, max_results: int = 10)`: Search for videos matching criteria
- `download_video(video_id: str)`: Download a specific video
- `get_video_info(video_id: str)`: Get metadata for a video

### AudioProcessor

Handles audio processing and analysis.

```python
from Components.media.audio_processor import AudioProcessor

processor = AudioProcessor(
    sample_rate=16000,
    vad_mode=3,
    noise_reduce_strength=0.75
)
```

#### Methods
- `remove_noise(audio_path: str)`: Remove background noise
- `normalize_volume(audio: np.ndarray)`: Normalize audio volume
- `detect_speech(audio: np.ndarray)`: Detect speech segments
- `detect_music(audio: np.ndarray)`: Detect music segments

### LLM Providers

Interface for different LLM providers (OpenAI, Groq, Ollama).

```python
from Components.llm_providers import OpenAIProvider, GroqProvider, OllamaProvider

provider = OpenAIProvider(
    api_key="your-api-key",
    model="gpt-4"
)
```

#### Methods
- `generate_text(prompt: str)`: Generate text from prompt
- `analyze_sentiment(text: str)`: Analyze text sentiment
- `detect_highlights(transcript: str)`: Detect interesting segments

## Pipeline Usage

### Complete Pipeline

```python
from Components.media.pipeline import VideoPipeline, PipelineConfig

config = PipelineConfig(
    min_highlight_duration=15.0,
    max_highlight_duration=60.0,
    target_duration=30.0,
    add_subtitles=True,
    add_zoom=True
)

pipeline = VideoPipeline(config=config, output_dir="shorts")
short_path = pipeline.process_video("video.mp4")
```

### Video Download

```python
from Components.youtube_scraper import YouTubeScraper

scraper = YouTubeScraper(download_path="downloads")
video_info = scraper.get_video_info("video_id")
video_path = scraper.download_video("video_id")
```

### Audio Processing

```python
from Components.media.audio_processor import AudioProcessor

processor = AudioProcessor()
denoised = processor.remove_noise("audio.wav")
normalized = processor.normalize_volume(denoised)
speech_segments = processor.detect_speech(normalized)
```

## Error Handling

All components use custom exceptions defined in `Components.exceptions`:

```python
from Components.exceptions import (
    VideoProcessingError,
    AudioProcessingError,
    DownloadError,
    TranscriptionError
)

try:
    # Process video
    pipeline.process_video("video.mp4")
except VideoProcessingError as e:
    logger.error(f"Video processing failed: {e}")
except DownloadError as e:
    logger.error(f"Download failed: {e}")
```

## Configuration

Environment variables in `.env`:

```env
# API Keys
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key

# Processing Settings
MIN_VIEWS=10000
MAX_DURATION=600
MAX_DAYS_OLD=7
TARGET_FPS=30

# Output Settings
OUTPUT_DIR=results
CACHE_DIR=cache
```

## Logging

Logging configuration in `Components.logger`:

```python
from Components.logger import get_logger

logger = get_logger(__name__)
logger.info("Processing started")
logger.error("Error occurred", exc_info=True)
```

Logs are saved in `logs/` with daily rotation.
