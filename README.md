# AI YouTube Shorts Generator

An intelligent system that automatically generates engaging YouTube Shorts from longer videos using AI-powered face detection, highlight detection, and smart cropping.

## Features

- **Intelligent Video Scraping**: Automatically find viral-worthy content
- **Smart Face Detection**: Dynamic face tracking and smooth cropping
- **Highlight Detection**: Uses LLMs to identify engaging moments
- **Advanced Audio Processing**: Noise reduction and volume normalization
- **Multi-Language Support**: Works with videos in any language
- **Automatic Short Generation**: Creates ready-to-upload shorts

## Quick Start

### Prerequisites
- Python 3.10+
- FFmpeg
- CUDA (optional, for GPU acceleration)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Usage

1. Basic usage:
```bash
python main.py --video_url "https://youtube.com/watch?v=..."
```

2. Advanced options:
```bash
python main.py \
    --video_url "https://youtube.com/watch?v=..." \
    --output_dir "shorts" \
    --min_duration 15 \
    --max_duration 60 \
    --target_fps 30
```

## Configuration

Key settings in `.env`:
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

## Project Structure

```
.
├── Components/           # Core components
│   ├── media/           # Media processing modules
│   ├── youtube/         # YouTube interaction modules
│   ├── llm_providers/   # LLM provider interfaces
│   └── utils/           # Utility functions
├── docs/                # Documentation
├── tests/               # Test files
├── cache/               # Cache directory
├── downloads/           # Downloaded videos
├── logs/                # Log files
├── results/             # Processed videos
└── shorts/              # Generated shorts
```

## Documentation

- [API Documentation](docs/API.md): Component APIs and usage
- [Development Guide](docs/DEVELOPMENT.md): Setup and contribution
- [Full Documentation](docs/README.md): Detailed guides and examples

## Features in Detail

### Video Processing
- Smart cropping with face detection
- Temporal smoothing for stable output
- Multiple face handling
- Dynamic zoom effects

### Audio Processing
- Background noise reduction
- Volume normalization
- Speech detection
- Music detection

### Language Processing
- Multi-language transcription
- Highlight detection using LLMs
- Sentiment analysis
- Content filtering

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed guidelines.

## Common Issues

1. FFMPEG not found:
   ```bash
   # Windows (using chocolatey)
   choco install ffmpeg
   # Mac
   brew install ffmpeg
   # Linux
   sudo apt-get install ffmpeg
   ```

2. Memory issues:
   - Reduce `MAX_DURATION` in `.env`
   - Process videos in smaller chunks
   - Use CPU mode if GPU memory is insufficient

3. API rate limits:
   - Implement exponential backoff
   - Use API key rotation
   - Cache responses when possible

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI](https://openai.com/) for GPT models
- [Groq](https://groq.com/) for LLM inference
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video downloading
- [moviepy](https://zulko.github.io/moviepy/) for video processing
- [OpenCV](https://opencv.org/) for face detection
