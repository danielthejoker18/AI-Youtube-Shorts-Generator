import pytest
from pathlib import Path
from Components.video_manager import VideoManager
from Components.exceptions import VideoManagerError

@pytest.fixture
def video_manager(tmp_path):
    """Fixture que cria um VideoManager com diretório temporário"""
    videos_dir = tmp_path / "videos"
    db_file = tmp_path / "videos.json"
    return VideoManager(str(videos_dir), str(db_file))

def test_video_manager_initialization(video_manager):
    """Testa se o VideoManager é inicializado corretamente"""
    assert video_manager.videos == {}
    assert video_manager.videos_dir.exists()

def test_add_video(video_manager):
    """Testa a adição de um vídeo"""
    video_id = "test123"
    title = "Test Video"
    path = "test.mp4"
    url = "https://youtube.com/watch?v=test123"
    
    video_manager.add_video(video_id, title, path, url)
    
    assert video_id in video_manager.videos
    assert video_manager.videos[video_id].title == title
    assert video_manager.videos[video_id].path == path
    assert video_manager.videos[video_id].url == url
    assert not video_manager.videos[video_id].processed

def test_mark_as_processed(video_manager):
    """Testa a marcação de um vídeo como processado"""
    video_id = "test123"
    video_manager.add_video(video_id, "Test", "test.mp4", "url")
    
    video_manager.mark_as_processed(video_id)
    
    assert video_manager.videos[video_id].processed
    assert video_manager.videos[video_id].processed_at is not None

def test_mark_as_processed_with_error(video_manager):
    """Testa a marcação de um vídeo como processado com erro"""
    video_id = "test123"
    error_msg = "Test error"
    video_manager.add_video(video_id, "Test", "test.mp4", "url")
    
    video_manager.mark_as_processed(video_id, error=error_msg)
    
    assert video_manager.videos[video_id].processed
    assert video_manager.videos[video_id].failed
    assert video_manager.videos[video_id].error == error_msg

def test_get_unprocessed_videos(video_manager):
    """Testa a obtenção de vídeos não processados"""
    # Adiciona um vídeo não processado
    video_manager.add_video("test1", "Test 1", "test1.mp4", "url1")
    
    # Adiciona um vídeo processado
    video_manager.add_video("test2", "Test 2", "test2.mp4", "url2")
    video_manager.mark_as_processed("test2")
    
    unprocessed = video_manager.get_unprocessed_videos()
    assert len(unprocessed) == 1
    assert unprocessed[0]["id"] == "test1"
