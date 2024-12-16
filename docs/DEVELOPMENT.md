# Development Guide

## Development Environment Setup

### Prerequisites
1. Python 3.10+
2. FFmpeg
3. Git
4. VS Code (recommended)
5. CUDA toolkit (optional, for GPU support)

### VS Code Extensions
Install the following extensions for optimal development:
- Python (Microsoft)
- Pylance
- Python Test Explorer
- Python Docstring Generator
- Git lens
- Black Formatter
- isort

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator
```

2. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

5. Configure pre-commit hooks:
```bash
pre-commit install
```

## Project Structure

```
AI-Youtube-Shorts-Generator/
├── Components/
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logger.py
│   ├── media/
│   │   ├── video_processor.py
│   │   ├── audio_processor.py
│   │   └── face_detector.py
│   ├── language/
│   │   ├── transcription.py
│   │   └── highlight_detector.py
│   ├── youtube/
│   │   ├── downloader.py
│   │   └── auth.py
│   ├── llm_providers/
│   │   ├── base_provider.py
│   │   └── custom_provider.py
│   └── utils/
│       └── helpers.py
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
├── scripts/
├── cache/
├── downloads/
├── logs/
├── results/
└── shorts/
```

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use Black for formatting (88 characters line length)
- Use isort for import organization
- Use type hints for all function parameters and returns

### Naming Conventions
- Functions/Variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private methods/variables: `_leading_underscore`

### Example Function Style
```python
from typing import Dict, List, Optional

def process_video_segment(
    video_path: str,
    segment: Dict[str, float],
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Process a single video segment.

    Args:
        video_path: Path to the video file
        segment: Dictionary containing segment information
            - start_time: Start time in seconds
            - end_time: End time in seconds
        options: Optional processing parameters
            - resolution: Output resolution
            - format: Output format

    Returns:
        bool: True if processing successful, False otherwise

    Raises:
        ProcessingError: If video processing fails
        FileNotFoundError: If video file not found
    """
    pass
```

## Testing Guidelines

### Writing Tests
- Write tests for all new features
- Maintain minimum 70% code coverage
- Use pytest fixtures for common setup
- Mock external services
- Use meaningful test names

### Example Test
```python
import pytest
from Components.video_processor import VideoProcessor
from Components.exceptions import ProcessingError

def test_video_segment_processing():
    # Arrange
    processor = VideoProcessor()
    test_video = "tests/data/test_video.mp4"
    test_segment = {"start": 0.0, "end": 5.0}
    
    # Act
    result = processor.process_video_segment(test_video, test_segment)
    
    # Assert
    assert result is True

def test_video_processing_error_handling():
    # Arrange
    processor = VideoProcessor()
    invalid_video = "nonexistent.mp4"
    
    # Act & Assert
    with pytest.raises(FileNotFoundError):
        processor.process_video_segment(invalid_video, {})
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=Components

# Run specific test file
pytest tests/test_video_processor.py

# Run tests matching pattern
pytest -k "video"
```

## Git Workflow

### Branches
- `main`: Production code
- `develop`: Development branch
- `feature/*`: New features
- `hotfix/*`: Urgent fixes
- `release/*`: Release preparation

### Commit Messages
Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Example:
```
feat: implement face tracking in video segments
```

### Pull Requests
1. Create feature branch
2. Implement changes
3. Write/update tests
4. Update documentation
5. Create pull request
6. Address review comments
7. Merge after approval

## Deployment

### Production Setup
1. Update version in `setup.py`
2. Create release branch
3. Run full test suite
4. Generate documentation
5. Create release tag
6. Merge to main

### Docker Deployment
```bash
# Build image
docker build -t ai-shorts-generator .

# Run container
docker run -d --name ai-shorts \
    -v /path/to/videos:/app/videos \
    -e OPENAI_API_KEY=your_key \
    ai-shorts-generator
```

## Performance Optimization

### Guidelines
1. Use caching for expensive operations
2. Implement multiprocessing for CPU-intensive tasks
3. Use GPU acceleration when available
4. Optimize I/O operations
5. Use generators for large datasets

### Example Optimization
```python
from functools import lru_cache
import torch

@lru_cache(maxsize=128)
def process_frame(frame_data: bytes) -> torch.Tensor:
    """Process video frame with caching."""
    # Implementation
    pass
```

## Troubleshooting Development Issues

### Common Issues

1. **FFmpeg Problems**
   - Check PATH environment variable
   - Verify FFmpeg installation
   - Check FFmpeg version compatibility

2. **CUDA Issues**
   - Verify CUDA installation
   - Check PyTorch CUDA compatibility
   - Monitor GPU memory usage

3. **Memory Management**
   - Use memory profiling tools
   - Implement batch processing
   - Clean up temporary files

### Debugging Tips
1. Use logging extensively
2. Enable debug mode in config
3. Use VS Code debugger
4. Monitor system resources
5. Check application logs

## Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. Install FFMPEG:
   - Windows: Use chocolatey: `choco install ffmpeg`
   - Mac: Use homebrew: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

## Development Workflow

### Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting
- Use isort for import sorting
- Maximum line length: 88 characters
- Use type hints

### Git Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit:
```bash
git add .
git commit -m "feat: description of changes"
```

3. Push changes and create PR:
```bash
git push origin feature/your-feature-name
```

### Commit Message Format

- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test changes
- chore: Build/dependency changes

## Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=Components tests/
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use pytest fixtures for setup
- Mock external services
- Test both success and failure cases

Example test:
```python
def test_video_processor():
    processor = VideoProcessor(
        video_path="test.mp4",
        output_dir="test_results"
    )
    result = processor.process_frame(mock_frame)
    assert result.shape == (720, 1280, 3)
```

## Adding New Features

1. Create new module in appropriate directory
2. Add tests for new functionality
3. Update documentation
4. Add type hints and docstrings
5. Run test suite
6. Create pull request

### Example: Adding New LLM Provider

1. Create provider class:
```python
# Components/llm_providers/custom_provider.py
from .base_provider import BaseLLMProvider

class CustomProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
    
    def generate_text(self, prompt: str) -> str:
        # Implementation
        pass
```

2. Add tests:
```python
# tests/test_custom_provider.py
def test_custom_provider():
    provider = CustomProvider("test-key")
    result = provider.generate_text("test prompt")
    assert isinstance(result, str)
```

## Debugging

### Logging

Use the logger module:
```python
from Components.logger import get_logger

logger = get_logger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message", exc_info=True)
```

### Common Issues

1. FFMPEG not found:
   - Ensure FFMPEG is installed
   - Add to system PATH
   - Check installation: `ffmpeg -version`

2. API Rate Limits:
   - Implement exponential backoff
   - Use API key rotation
   - Cache responses

3. Memory Issues:
   - Process videos in chunks
   - Clear cache regularly
   - Monitor memory usage

## Performance Optimization

1. Video Processing:
   - Use frame skipping
   - Implement batch processing
   - Optimize face detection

2. Memory Management:
   - Clear unused caches
   - Process large files in chunks
   - Use generators for large datasets

3. API Usage:
   - Implement caching
   - Use batch requests
   - Rate limit requests

## Security

1. API Keys:
   - Never commit .env file
   - Rotate keys regularly
   - Use environment variables

2. Input Validation:
   - Validate all user inputs
   - Sanitize file paths
   - Check file types

3. Error Handling:
   - Never expose stack traces
   - Log securely
   - Handle all exceptions

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Create pull request

## Release Process

1. Update version number
2. Update changelog
3. Run test suite
4. Create release branch
5. Tag release
6. Deploy to production

## Resources

- [Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [FFMPEG Documentation](https://ffmpeg.org/documentation.html)
- [YouTube Data API](https://developers.google.com/youtube/v3)
