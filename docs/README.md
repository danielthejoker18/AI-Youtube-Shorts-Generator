# AI YouTube Shorts Generator Documentation

## Table of Contents
1. [API Documentation](API.md)
   - Core Components
   - Pipeline Usage
   - Error Handling
   - Configuration
   - Logging

2. [Development Guide](DEVELOPMENT.md)
   - Project Structure
   - Setup Guide
   - Development Workflow
   - Testing
   - Adding Features
   - Performance
   - Security

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the application:
```bash
python main.py --video_url "https://youtube.com/watch?v=..."
```

## Key Features

- Intelligent viral video scraping
- Face detection and smart cropping
- Audio processing and enhancement
- Highlight detection using LLMs
- Automatic short generation
- Multi-language support

## Architecture Overview

```
User Input
    │
    ▼
YouTube Scraper ──► Video Download
    │
    ▼
Video Processor
    │
    ├──► Face Detection
    │
    ├──► Audio Processing
    │
    ├──► Transcription
    │
    ├──► Highlight Detection
    │
    └──► Short Generation
         │
         ▼
    Final Output
```

## Components

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

### Pipeline

- Modular design
- Configurable processing steps
- Progress tracking
- Error handling

## Configuration

Key configuration options in `.env`:

```env
# API Keys
OPENAI_API_KEY=your-key
GROQ_API_KEY=your-key

# Processing
MIN_VIEWS=10000
MAX_DURATION=600
TARGET_FPS=30

# Output
OUTPUT_DIR=results
CACHE_DIR=cache
```

## Best Practices

1. Video Processing
   - Process in chunks for memory efficiency
   - Implement proper cleanup
   - Monitor system resources

2. API Usage
   - Implement rate limiting
   - Cache responses
   - Handle errors gracefully

3. Output Quality
   - Validate video/audio quality
   - Check face detection confidence
   - Verify highlight relevance

## Common Issues

1. Installation
   - FFMPEG not found
   - Missing dependencies
   - Environment setup

2. Processing
   - Memory usage
   - Processing speed
   - Face detection accuracy

3. API
   - Rate limits
   - Authentication
   - Response handling

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Development setup
- Code style
- Testing
- Pull request process

## Support

- Create an issue for bugs
- Use discussions for questions
- Check existing issues first

## License

This project is licensed under the MIT License. See [LICENSE](../LICENSE) for details.
