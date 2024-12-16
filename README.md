# AI YouTube Shorts Generator

Automatically generate engaging YouTube Shorts from long-form videos using AI.

## Features

- Convert long videos into short-form content
- Detect and extract engaging segments
- Support for multiple languages (English, Portuguese)
- Smart video processing with ffmpeg
- LLM-powered content analysis
- Configurable video output settings

## Requirements

- Python 3.8+
- FFmpeg
- ImageMagick
- CUDA-compatible GPU (optional, for faster processing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/danielthejoker18/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install system dependencies:
- FFmpeg: [Download](https://ffmpeg.org/download.html)
- ImageMagick: [Download](https://imagemagick.org/script/download.php)

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

## Usage

1. Add videos to process in `videos.json`:
```json
{
    "videos": [
        {
            "id": "video1",
            "path": "videos/example.mp4",
            "title": "Example Video",
            "language": "en"
        }
    ]
}
```

2. Run the script:
```bash
python main.py
```

## Configuration

### Environment Variables

- `LLM_PROVIDER`: Choose LLM provider (openai, groq, ollama)
- `OPENAI_API_KEY`: OpenAI API key
- `MAX_VIDEO_LENGTH`: Maximum output video length (seconds)
- `MIN_VIDEO_LENGTH`: Minimum output video length (seconds)

### Video Processing

- Supported input formats: MP4, MOV, AVI
- Output format: MP4 (1080x1920)
- Maximum input duration: 1 hour
- Supported languages: English (en), Portuguese (pt)

## Project Structure

```
.
├── Components/              # Core components
│   ├── core/               # Core utilities
│   ├── language/           # Language processing
│   ├── llm/                # LLM integration
│   └── media/              # Media processing
├── docs/                   # Documentation
├── tests/                  # Test files
├── .env.example           # Example environment variables
├── main.py                # Main script
├── moviepy_conf.py        # MoviePy configuration
├── requirements.txt       # Python dependencies
└── videos.json           # Video configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details
