import pytest
from unittest.mock import Mock, patch, mock_open
import json
from pathlib import Path
import logging
from Components.youtube_scraper import YouTubeScraper

logger = logging.getLogger(__name__)

@pytest.fixture
def youtube_scraper():
    """Fixture que cria uma instância do YouTubeScraper com mocks"""
    with patch('Components.youtube_scraper.requests.Session') as mock_session:
        # Mock da sessão
        session_instance = Mock()
        session_instance.get.return_value = Mock(status_code=200)
        session_instance.post.return_value = Mock(status_code=200)
        mock_session.return_value = session_instance
        
        # Mock do arquivo de cookies
        cookies_content = {
            'cookie1': 'value1',
            'cookie2': 'value2'
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(cookies_content))):
            with patch('pathlib.Path.exists', return_value=True):
                scraper = YouTubeScraper()
                scraper.cookies = cookies_content
                yield scraper

@pytest.fixture
def mock_trending_response():
    """Fixture que retorna uma resposta mockada de vídeos em trending"""
    return {
        "contents": {
            "twoColumnBrowseResultsRenderer": {
                "tabs": [{
                    "tabRenderer": {
                        "content": {
                            "sectionListRenderer": {
                                "contents": [{
                                    "itemSectionRenderer": {
                                        "contents": [{
                                            "videoRenderer": {
                                                "videoId": "test123",
                                                "title": {
                                                    "runs": [{"text": "Test Video"}]
                                                },
                                                "lengthText": {
                                                    "simpleText": "10:00"
                                                },
                                                "viewCountText": {
                                                    "simpleText": "1M views"
                                                },
                                                "thumbnail": {
                                                    "thumbnails": [{
                                                        "url": "https://test.com/thumb.jpg"
                                                    }]
                                                }
                                            }
                                        }]
                                    }
                                }]
                            }
                        }
                    }
                }]
            }
        }
    }

def test_extract_video_id(youtube_scraper):
    """Testa extração de ID de vídeo de URLs do YouTube"""
    # URL padrão
    url = "https://www.youtube.com/watch?v=test123"
    assert youtube_scraper._extract_video_id(url) == "test123"
    
    # URL curta
    url = "https://youtu.be/test123"
    assert youtube_scraper._extract_video_id(url) == "test123"
    
    # URL com parâmetros adicionais
    url = "https://www.youtube.com/watch?v=test123&t=10s"
    assert youtube_scraper._extract_video_id(url) == "test123"
    
    # URL inválida
    url = "https://example.com"
    assert youtube_scraper._extract_video_id(url) is None

@patch('Components.youtube_scraper.requests.Session')
def test_get_trending_videos(mock_session, youtube_scraper):
    """Testa obtenção de vídeos em trending"""
    # Mock da sessão
    session_instance = Mock()
    
    # Mock para simular uma resposta HTTP para a primeira chamada (página inicial)
    mock_initial_response = Mock()
    mock_initial_response.text = '"INNERTUBE_API_KEY":"mock_api_key"'
    mock_initial_response.status_code = 200
    
    # Mock para simular uma resposta HTTP para a segunda chamada (API)
    mock_search_response = Mock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        'contents': {
            'twoColumnSearchResultsRenderer': {
                'primaryContents': {
                    'sectionListRenderer': {
                        'contents': [{
                            'itemSectionRenderer': {
                                'contents': [{
                                    'videoRenderer': {
                                        'videoId': 'test_video_id',
                                        'title': {'runs': [{'text': 'Test Video'}]},
                                        'lengthText': {'simpleText': '0:30'},
                                        'viewCountText': {'simpleText': '1000 views'},
                                        'thumbnail': {
                                            'thumbnails': [{
                                                'url': 'http://example.com/thumb.jpg'
                                            }]
                                        }
                                    }
                                }]
                            }
                        }]
                    }
                }
            }
        }
    }
    
    # Configure session mock
    mock_session.return_value.get.return_value = mock_initial_response
    mock_session.return_value.post.return_value = mock_search_response
    
    # Create scraper and get trending videos with test_mode=True
    videos = youtube_scraper.get_trending_videos(max_results=1, test_mode=True)
    
    # Verify we got the expected video
    assert len(videos) == 1
    video = videos[0]
    
    # Log the video data for debugging
    logger.info(f"Video data received: {json.dumps(video, indent=2)}")
    
    # Test assertions with actual field names
    assert 'test_video_id' in video['url']  # URL contains video ID
    assert video['title'] == 'Test Video'
    assert video['duration_text'] == '0:30'
    assert video['thumbnail'] == 'http://example.com/thumb.jpg'

@patch('Components.youtube_scraper.requests.Session')
def test_get_viral_video(mock_session, youtube_scraper):
    """Test getting viral videos."""
    logger.info("Starting test_get_viral_video")

    # Mock for simulating a successful initial request
    first_response = Mock()
    first_response.raise_for_status = Mock()
    first_response.text = '''{"INNERTUBE_API_KEY":"test_api_key"}'''
    
    # Mock for simulating a successful API request
    second_response = Mock()
    second_response.raise_for_status = Mock()
    second_response.json.return_value = {
        'contents': {
            'twoColumnBrowseResultsRenderer': {
                'tabs': [{
                    'tabRenderer': {
                        'content': {
                            'sectionListRenderer': {
                                'contents': [{
                                    'itemSectionRenderer': {
                                        'contents': [{
                                            'videoRenderer': {
                                                'videoId': 'test123',
                                                'title': {'runs': [{'text': 'Test Video'}]},
                                                'lengthText': {'simpleText': '10:00'},
                                                'viewCountText': {'simpleText': '1M views'},
                                                'thumbnail': {'thumbnails': [{'url': 'https://test.com/thumb.jpg'}]},
                                                'ownerText': {'runs': [{'text': 'Test Channel'}]},
                                                'navigationEndpoint': {
                                                    'commandMetadata': {
                                                        'webCommandMetadata': {
                                                            'url': '/watch?v=test123'
                                                        }
                                                    }
                                                }
                                            }
                                        }]
                                    }
                                }]
                            }
                        }
                    }
                }]
            }
        }
    }
    
    # Configure session mock
    mock_session.return_value.get.return_value = first_response
    mock_session.return_value.post.return_value = second_response
    
    logger.info("Mocks configured, calling get_viral_video")

    # Test the function
    videos = list(youtube_scraper.get_viral_video())
    logger.info(f"Got {len(videos)} videos")
    assert len(videos) > 0
    video = videos[0]
    
    # Log the video data for debugging
    logger.info(f"Viral video data received: {json.dumps(video, indent=2)}")
    
    # Test assertions with actual field names
    assert 'test123' in video['url']  # URL contains video ID
    assert video['title'] == 'Test Video'
    assert video['channel_name'] == 'Test Channel'
    assert video['view_count'] == 1000000
    assert video['duration'] == 600  # 10:00 in seconds
    
    logger.info("All assertions passed")

def test_duration_to_seconds(youtube_scraper):
    """Testa conversão de duração para segundos"""
    assert youtube_scraper._duration_to_seconds("1:00") == 60
    assert youtube_scraper._duration_to_seconds("1:30") == 90
    assert youtube_scraper._duration_to_seconds("2:00:00") == 7200
    assert youtube_scraper._duration_to_seconds("Invalid") == 0

def test_parse_view_count(youtube_scraper):
    """Testa parsing de contagem de visualizações"""
    assert youtube_scraper._parse_view_count("1M views") == 1000000
    assert youtube_scraper._parse_view_count("100K views") == 100000
    assert youtube_scraper._parse_view_count("1.5K views") == 1500
    assert youtube_scraper._parse_view_count("Invalid") == 0
