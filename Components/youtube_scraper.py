"""
YouTube Scraper Component for finding trending and viral videos.
Uses requests and BeautifulSoup to scrape trending videos without requiring API access.
"""

import random
from typing import List, Dict, Optional, Tuple
import logging
from logging.handlers import RotatingFileHandler
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, quote, parse_qs, urlparse
import time
import json
import os
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import hashlib
from pathlib import Path
import math
from urllib.parse import urlencode
import yt_dlp

# Configure logging
def setup_logger():
    """Configure logging with detailed formatting and file rotation."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # File handler with rotation
    log_file = os.path.join('logs', 'youtube_scraper.log')
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatters and add it to the handlers
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

class YouTubeScraper:
    def __init__(self):
        """Initialize YouTube scraper."""
        logger.info("Inicializando YouTubeScraper")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'X-YouTube-Client-Name': '1',
            'X-YouTube-Client-Version': '2.20240101',
        }
        
        # Load authentication cookies
        self.cookies_file = Path('youtube.cookies')
        self.cookies = requests.cookies.RequestsCookieJar()
        if self.cookies_file.exists():
            logger.info("Loading YouTube authentication cookies")
            try:
                with open(self.cookies_file, 'r') as f:
                    for line in f:
                        if line.startswith('#') or not line.strip():
                            continue
                        fields = line.strip().split('\t')
                        if len(fields) >= 7:
                            domain, domain_specified, path, secure, expires, name, value = fields[:7]
                            secure = secure.lower() == 'true'
                            expires = int(expires) if expires.isdigit() else None
                            if domain.startswith('.'):
                                domain = domain[1:]
                            self.cookies.set(name, value, domain=domain, path=path, secure=secure, expires=expires)
            except Exception as e:
                logger.warning(f"Error loading cookies: {e}")
                self.cookies = requests.cookies.RequestsCookieJar()
        else:
            logger.warning("No authentication cookies found. Some videos may be inaccessible.")
        
        self.base_url = 'https://www.youtube.com'
        self.search_url = 'https://www.youtube.com/results'
        self.trending_url = 'https://www.youtube.com/feed/trending'
        self.api_url = 'https://www.youtube.com/youtubei/v1/browse'
        self.client = {
            'clientName': 'WEB',
            'clientVersion': '2.20240101',
        }
        
        # Cache settings
        self.cache_dir = Path('cache/youtube_scraper')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Processed videos cache
        self.processed_videos_file = self.cache_dir / 'processed_videos.json'
        self.processed_videos = self._load_processed_videos()
        
        # Test mode settings (sem filtros)
        self.min_views_threshold = 0  # Removido threshold de views
        self.engagement_ratio_threshold = 0  # Removido threshold de engajamento
        self.max_results = 10  # Limite de 10 vídeos bons
        
        # Viral detection settings (ajustados para serem menos restritivos)
        self.viral_keywords = [
            'viral', 'trending', 'popular', 'hit', 'sensation', 'amazing',
            'incredible', 'awesome', 'insane', 'unbelievable', 'best',
            'top', 'most', 'epic', 'funny', 'cool', 'interesting'
        ]
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
    
    def _load_processed_videos(self) -> set:
        """Load set of processed video IDs."""
        try:
            if self.processed_videos_file.exists():
                with open(self.processed_videos_file, 'r') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            logger.error(f"Erro ao carregar vídeos processados: {str(e)}")
            return set()
            
    def _save_processed_videos(self):
        """Save set of processed video IDs."""
        try:
            with open(self.processed_videos_file, 'w') as f:
                json.dump(list(self.processed_videos), f)
        except Exception as e:
            logger.error(f"Erro ao salvar vídeos processados: {str(e)}")
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        try:
            if 'youtu.be' in url:
                return url.split('/')[-1]
            parsed = urlparse(url)
            if parsed.hostname in ['www.youtube.com', 'youtube.com']:
                if parsed.path == '/watch':
                    return parse_qs(parsed.query)['v'][0]
            return None
        except Exception:
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, session=None, method='GET', url=None, **kwargs):
        """Make a request to the YouTube API."""
        try:
            if session is None:
                session = requests.Session()
                session.headers.update(self.headers)
                
                # Add authentication cookies if available
                if self.cookies:
                    session.cookies.update(self.cookies)

            # If no URL is provided, get initial page
            if url is None:
                url = self.trending_url

            # Make the request
            if method.upper() == 'GET':
                response = session.get(url, **kwargs)
            else:
                response = session.post(url, **kwargs)
                
            response.raise_for_status()
            return response

        except Exception as e:
            logger.error(f"Error making request: {str(e)}")
            raise
    
    def get_trending_videos(self, region: str = 'US', max_results: int = 20, test_mode: bool = False) -> List[Dict]:
        """
        Get trending videos from YouTube search.
        """
        try:
            logger.info(f"Buscando vídeos populares para região: {region}")
            
            # Use apenas uma query em modo de teste
            if test_mode:
                search_queries = ['trending']
            else:
                search_queries = [
                    'trending',
                    'viral videos',
                    'popular uploads',
                    'most viewed',
                    'viral videos', 'trending now', 'most popular', 'best videos',
                    'amazing videos', 'viral moments', 'trending videos', 'must watch',
                    'top videos today', 'viral content', 'trending content',
                    'viral compilation', 'best moments', 'epic videos'
                ]
            
            all_videos = []
            session = requests.Session()
            session.headers.update(self.headers)
            
            # Add authentication cookies if available
            if self.cookies:
                session.cookies.update(self.cookies)
                
            for query in search_queries:
                try:
                    # Primeiro faz uma requisição para a página inicial
                    response = self._make_request(session=session, method='GET', url=self.base_url)
                    
                    # Extrai o INNERTUBE_API_KEY
                    api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', response.text)
                    if not api_key_match:
                        logger.warning("Não foi possível encontrar a API key")
                        continue
                    
                    api_key = api_key_match.group(1)
                    api_url = f"https://www.youtube.com/youtubei/v1/search?key={api_key}"
                    
                    payload = {
                        "context": {
                            "client": {
                                "clientName": "WEB",
                                "clientVersion": "2.20240101",
                                "hl": "en",
                                "gl": region,
                            }
                        },
                        "query": f"{query} this month",
                        "params": "CAMSAhAB"  # Filtro para vídeos mais relevantes
                    }
                    
                    logger.info(f"Buscando por: {query}")
                    
                    # Faz a requisição para a API
                    response = self._make_request(
                        session=session,
                        method='POST',
                        url=api_url,
                        json=payload,
                        headers={
                            **self.headers,
                            'Content-Type': 'application/json',
                            'X-Goog-Visitor-Id': '',
                        },
                        timeout=15
                    )
                    
                    data = response.json()
                    
                    # Extrai os vídeos da resposta
                    contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
                    
                    for content in contents:
                        if 'itemSectionRenderer' not in content:
                            continue
                        
                        items = content['itemSectionRenderer'].get('contents', [])
                        for item in items:
                            video_data = None
                            if 'videoRenderer' in item:
                                video = item['videoRenderer']
                                video_data = self._extract_video_data(item)
                            elif 'richItemRenderer' in item:
                                video = item['richItemRenderer'].get('content', {}).get('videoRenderer', {})
                                if video:
                                    video_data = self._extract_video_data(item)
                            
                            if video_data:
                                logger.debug(f"Vídeo encontrado: {json.dumps(video_data, ensure_ascii=False)}")
                                all_videos.append(video_data)
                
                    if not test_mode:
                        time.sleep(2)  # Delay entre buscas apenas fora do modo de teste
                
                except Exception as e:
                    logger.warning(f"Erro ao buscar query '{query}': {str(e)}", exc_info=True)
                    continue
            
            # Remove duplicados e ordena por views
            seen_urls = set()
            unique_videos = []
            for video in all_videos:
                if video['url'] not in seen_urls:
                    seen_urls.add(video['url'])
                    unique_videos.append(video)
            
            unique_videos.sort(key=lambda x: x['view_count'], reverse=True)
            return unique_videos[:max_results]
            
        except Exception as e:
            logger.error(f"Erro ao buscar vídeos populares: {str(e)}", exc_info=True)
            return []

    def get_trending_videos_from_multiple_regions(self, max_results: int = 20) -> List[Dict]:
        """
        Get trending videos from multiple regions.
        """
        try:
            logger.info("Buscando vídeos em tendência")
            videos = []
            regions = ['US', 'CA', 'GB', 'AU', 'BR', 'FR', 'DE', 'JP', 'KR', 'IN']
            
            for region in regions:
                try:
                    logger.debug(f"Buscando vídeos em tendência da região: {region}")
                    params = {
                        'gl': region,
                        'hl': 'en',
                    }
                    response = self._make_request(self.trending_url, params=params)
                    if not response:
                        continue
                    
                    page_videos = self._extract_videos_from_page(response)
                    if page_videos:
                        videos.extend(page_videos)
                        logger.info(f"Encontrados {len(page_videos)} vídeos em tendência na região {region}")
                except Exception as e:
                    logger.error(f"Erro ao buscar vídeos em tendência da região {region}: {str(e)}")
                    continue
            
            return self._filter_and_sort_videos(videos)
            
        except Exception as e:
            logger.error(f"Erro ao buscar vídeos em tendência: {str(e)}", exc_info=True)
            return []

    def _extract_video_data(self, item: Dict) -> Dict:
        """Extract video data from a YouTube API response item."""
        try:
            # Handle different item types
            if 'richItemRenderer' in item:
                video = item['richItemRenderer'].get('content', {}).get('videoRenderer', {})
            elif 'videoRenderer' in item:
                video = item['videoRenderer']
            else:
                logger.debug(f"Unsupported item type: {list(item.keys())}")
                return {}
            
            video_id = video.get('videoId', '')
            if not video_id:
                return {}
                
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Extract title
            title = video.get('title', {}).get('runs', [{}])[0].get('text', '')
            if not title:
                title = video.get('title', {}).get('simpleText', '')
            
            # Extract channel name
            channel_name = video.get('longBylineText', {}).get('runs', [{}])[0].get('text', '')
            if not channel_name:
                channel_name = video.get('ownerText', {}).get('runs', [{}])[0].get('text', '')
            
            # Extract view count
            view_count_text = video.get('viewCountText', {}).get('simpleText', '0')
            if not view_count_text:
                view_count_text = video.get('viewCountText', {}).get('runs', [{}])[0].get('text', '0')
            view_count = self._parse_view_count(view_count_text)
            
            # Extract duration
            duration_text = video.get('lengthText', {}).get('simpleText', '0:00')
            if not duration_text:
                duration_text = video.get('lengthText', {}).get('runs', [{}])[0].get('text', '0:00')
            duration = self._duration_to_seconds(duration_text)
            
            # Extract thumbnail URL
            thumbnail = video.get('thumbnail', {}).get('thumbnails', [{}])[0].get('url', '')
            
            # Extract other metadata
            is_age_restricted = bool(video.get('isRestrictedForAge', False))
            is_live = bool(video.get('isLive', False))
            is_upcoming = bool(video.get('isUpcoming', False))
            
            return {
                'url': url,
                'title': title,
                'channel_name': channel_name,
                'view_count': view_count,
                'duration': duration,
                'duration_text': duration_text,
                'thumbnail': thumbnail,
                'is_age_restricted': is_age_restricted,
                'is_live': is_live,
                'is_upcoming': is_upcoming
            }
            
        except Exception as e:
            logger.error(f"Error extracting video data: {str(e)}")
            return {}

    def get_viral_video(self):
        """Get viral videos from YouTube."""
        logger.info("Starting viral video search")
        videos_found = 0
        max_videos = 10  # Limit to 10 videos

        try:
            while videos_found < max_videos:
                logger.info("Making initial request to get API key")
                # Get initial page to get API key
                initial_response = self._make_request(method='GET', url=self.base_url)
                
                # Extract API key
                api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', initial_response.text)
                if not api_key_match:
                    logger.warning("Could not find API key")
                    break

                api_key = api_key_match.group(1)
                api_url = f"https://www.youtube.com/youtubei/v1/browse?key={api_key}"
                logger.info(f"Found API key, making request to {api_url}")
                
                # Make API request
                payload = {
                    "context": {
                        "client": {
                            "clientName": "WEB",
                            "clientVersion": "2.20240101",
                            "hl": "en",
                            "gl": "US",
                        }
                    },
                    "browseId": "FEtrending"
                }
                
                response = self._make_request(method='POST', url=api_url, json=payload)
                if not response:
                    logger.warning("No response from API")
                    break
                    
                data = response.json()
                logger.debug(f"Received API response: {json.dumps(data, indent=2)}")
                
                # Extract videos from response using the correct structure
                try:
                    contents = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
                    logger.info(f"Found {len(contents)} tabs in response")
                    for tab in contents:
                        tab_content = tab.get('tabRenderer', {}).get('content', {})
                        section_list = tab_content.get('sectionListRenderer', {}).get('contents', [])
                        logger.info(f"Found {len(section_list)} sections in tab")
                        for section in section_list:
                            item_section = section.get('itemSectionRenderer', {}).get('contents', [])
                            logger.info(f"Found {len(item_section)} items in section")
                            for item in item_section:
                                if 'videoRenderer' in item:
                                    logger.info("Found video renderer, extracting data")
                                    video_data = self._extract_video_data(item)
                                    if video_data:
                                        videos_found += 1
                                        logger.info(f"Found valid video: {json.dumps(video_data, indent=2)}")
                                        yield video_data
                                        
                                        if videos_found >= max_videos:
                                            logger.info("Reached max videos limit")
                                            return
                except Exception as e:
                    logger.error(f"Error parsing video data: {str(e)}")
                    continue
                
                # If we get here, we didn't find enough videos
                logger.info("No more videos found in current request")
                break

        except Exception as e:
            logger.error(f"Error in get_viral_video: {str(e)}")
            return

    def _duration_to_seconds(self, duration_text: str) -> int:
        """Convert duration text to seconds."""
        try:
            if not duration_text:
                return 0
                
            parts = duration_text.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return 0
        except Exception as e:
            logger.error(f"Error converting duration: {str(e)}")
            return 0

    def _parse_view_count(self, view_count_text: str) -> int:
        """Parse view count text to integer."""
        try:
            if not view_count_text:
                return 0
                
            # Remove 'views' and any commas, then convert to int
            count = view_count_text.lower().replace('views', '').replace(',', '').strip()
            
            # Handle K, M, B suffixes
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
            for suffix, multiplier in multipliers.items():
                if suffix in count.lower():
                    try:
                        number = float(count.lower().replace(suffix, '').strip())
                        return int(number * multiplier)
                    except (ValueError, TypeError):
                        return 0
            
            try:
                return int(count) if count.strip() else 0
            except (ValueError, TypeError):
                return 0
            
        except Exception as e:
            logger.error(f"Error parsing view count: {str(e)}")
            return 0

    def _extract_views_from_text(self, views_text: str) -> int:
        """Extract view count from text."""
        try:
            views_text = views_text.lower().replace(',', '').replace('.', '')
            views_str = views_text.split('views')[0].strip()
            
            multiplier = 1
            if 'k' in views_str:
                multiplier = 1000
                views_str = views_str.replace('k', '')
            elif 'm' in views_str:
                multiplier = 1000000
                views_str = views_str.replace('m', '')
            elif 'b' in views_str:
                multiplier = 1000000000
                views_str = views_str.replace('b', '')
            
            views_str = re.sub(r'[^\d]', '', views_str)
            if views_str:
                return int(float(views_str) * multiplier)
        except Exception as e:
            logger.error(f"Erro ao extrair visualizações do texto: {str(e)}")
        return 0

    def _is_valid_video(self, video: Dict) -> bool:
        """Check if a video meets our criteria."""
        try:
            # Skip if already processed
            if video['url'] in self.processed_videos:
                logger.debug(f"Video already processed: {video['title']}")
                return False

            # Skip age-restricted videos if no authentication
            if video.get('is_age_restricted', False) and not self.cookies:
                logger.debug(f"Skipping age-restricted video (no auth): {video['title']}")
                return False
                
            # Skip live or upcoming videos
            if video.get('is_live', False) or video.get('is_upcoming', False):
                logger.debug(f"Skipping live/upcoming video: {video['title']}")
                return False

            # Skip videos outside duration range (30s to 20min)
            min_duration = 30
            max_duration = 20 * 60  # Aumentado para 20 minutos
            duration = video.get('duration', 0)
            if not (min_duration <= duration <= max_duration):
                logger.debug(f"Video duration outside range: {duration}s")
                return False

            # Skip shorts
            if 'shorts' in video['url'].lower():
                logger.debug(f"Skipping short: {video['title']}")
                return False

            # Skip music videos and shows
            title_lower = video['title'].lower()
            music_keywords = [
                'music video', 'official video', 'lyric video', 'audio',
                'live', 'concert', 'show', 'performance', 'tour', 'clipe',
                'official music', 'official audio', 'visualizer', 'mv',
                'feat', 'ft.', 'ft ', 'featuring', 'cover', 'remix',
                'ao vivo', 'música', 'musical', 'cantando', 'song',
                'official clip', 'official mv', 'official m/v',
                'dvd', 'ep', 'album', 'álbum', 'clip', 'clipe',
                'part.', 'part ', 'part.', 'participação',
                'banda', 'singer', 'cantor', 'cantora',
                'trailer', 'teaser', 'announcement', 'reveal',
                'video oficial', 'videoclipe', 'videoclip',
                '@', 'ft', 'feat.', 'featuring',
                ' e ', ' & ', ' and '
            ]
            
            # Check title for music keywords
            if any(keyword in title_lower for keyword in music_keywords):
                logger.debug(f"Skipping music/show video: {video['title']}")
                return False

            # Skip videos from music channels
            channel_name = video.get('channel_name', '').lower()
            music_channels = [
                'vevo', 'music', 'records', 'entertainment', 'oficial',
                'official', 'studio', 'productions', 'record', 'sony',
                'universal', 'warner', 'hits', 'sound', 'audio',
                'groove', 'label', 'band', 'mc', 'dj', 'rap', 'hip hop',
                'músicas', 'musicas', 'musical', 'músic', 'music',
                'cantora', 'cantor', 'singer', 'artista', 'artist',
                'games', 'gaming', 'playstation', 'xbox', 'nintendo',
                'bahtidão', 'batidão', 'forró', 'sertanejo',
                'funk', 'pagode', 'axé', 'brega', 'piseiro'
            ]
            
            if any(keyword in channel_name for keyword in music_channels):
                logger.debug(f"Skipping music channel video: {video['title']}")
                return False

            # Add video to processed list and save
            self.processed_videos.add(video['url'])
            self._save_processed_videos()

            return True

        except Exception as e:
            logger.error(f"Error validating video: {str(e)}")
            return False

    def _search_videos(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Busca vídeos no YouTube com filtros específicos.
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            
        Returns:
            Lista de vídeos encontrados
        """
        try:
            # Codifica a query e adiciona filtros
            params = {
                'search_query': query,
                'sp': 'CAMSBggEEAEYAQ%253D%253D',  # Filtro: Esta semana + Mais visualizações
                'app': 'desktop'
            }
            
            url = f"{self.search_url}?{urlencode(params)}"
            logger.debug(f"URL de busca: {url}")
            
            # Faz a requisição
            response = self._make_request(url=url)
            if not response:
                return []
                
            # Extrai dados do JavaScript
            ytInitialData = self._extract_yt_initial_data(response.text)
            if not ytInitialData:
                return []
                
            videos = []
            contents = ytInitialData.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
            
            for content in contents:
                if 'itemSectionRenderer' not in content:
                    continue
                    
                items = content['itemSectionRenderer'].get('contents', [])
                for item in items:
                    if 'videoRenderer' not in item:
                        continue
                        
                    video = item['videoRenderer']
                    
                    # Extrai informações básicas
                    video_id = video.get('videoId')
                    title = video.get('title', {}).get('runs', [{}])[0].get('text', '')
                    
                    # Pula vídeos sem ID ou título
                    if not video_id or not title:
                        continue
                        
                    # Extrai e valida duração
                    duration_text = video.get('lengthText', {}).get('simpleText', '')
                    duration = self._parse_duration(duration_text)
                    
                    # Pula vídeos muito longos (>30min) ou muito curtos (<1min)
                    if not duration or duration > 1800 or duration < 60:
                        continue
                        
                    # Extrai visualizações
                    view_count_text = video.get('viewCountText', {}).get('simpleText', '0 views')
                    view_count = self._parse_view_count(view_count_text)
                    
                    # Pula vídeos com poucas visualizações
                    if view_count < 10000:  # Mínimo de 10k views
                        continue
                        
                    # Verifica data de publicação
                    published_time = video.get('publishedTimeText', {}).get('simpleText', '')
                    if not self._is_recent(published_time):
                        continue
                        
                    # Extrai mais metadados
                    channel_title = video.get('ownerText', {}).get('runs', [{}])[0].get('text', '')
                    thumbnail_url = video.get('thumbnail', {}).get('thumbnails', [{}])[-1].get('url', '')
                    
                    videos.append({
                        'id': video_id,
                        'title': title,
                        'duration': duration,
                        'view_count': view_count,
                        'channel': channel_title,
                        'thumbnail': thumbnail_url,
                        'published': published_time,
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })
                    
                    if len(videos) >= max_results:
                        break
                        
            logger.info(f"Encontrados {len(videos)} vídeos para a query '{query}'")
            return videos
            
        except Exception as e:
            logger.error(f"Erro na busca de vídeos: {str(e)}")
            return []
            
    def _extract_yt_initial_data(self, html_content: str) -> dict:
        """
        Extrai os dados iniciais do YouTube da página HTML.
        
        Args:
            html_content: Conteúdo HTML da página
            
        Returns:
            Dicionário com os dados iniciais do YouTube
        """
        try:
            # Procura pelo padrão ytInitialData
            pattern = r'var ytInitialData = ({.*?});'
            match = re.search(pattern, html_content)
            
            if not match:
                # Tenta outro padrão comum
                pattern = r'window\["ytInitialData"\] = ({.*?});'
                match = re.search(pattern, html_content)
                
            if not match:
                logger.error("Não foi possível encontrar ytInitialData")
                return {}
                
            # Extrai e parseia o JSON
            data = json.loads(match.group(1))
            return data
            
        except Exception as e:
            logger.error(f"Erro extraindo ytInitialData: {str(e)}")
            return {}
            
    def _parse_duration(self, duration_text: str) -> Optional[int]:
        """Converte texto de duração (HH:MM:SS) para segundos"""
        try:
            if not duration_text:
                return None
                
            parts = duration_text.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return None
            
        except Exception:
            return None
            
    def _parse_view_count(self, view_count_text: str) -> int:
        """Converte texto de visualizações para número"""
        try:
            number = ''.join(filter(str.isdigit, view_count_text))
            return int(number) if number else 0
        except Exception:
            return 0
            
    def _is_recent(self, published_time: str) -> bool:
        """Verifica se o vídeo é recente (últimos 6 meses)"""
        try:
            if not published_time:
                return False
                
            # Converte texto relativo para booleano
            recent_indicators = [
                'hour', 'hours',
                'day', 'days',
                'week', 'weeks',
                'month', 'months'
            ]
            
            is_recent = any(indicator in published_time.lower() for indicator in recent_indicators)
            
            # Se contém "months", verifica se é <= 6
            if 'month' in published_time.lower():
                number = int(''.join(filter(str.isdigit, published_time)))
                return number <= 6
                
            return is_recent
            
        except Exception:
            return False
            
    def fetch_new_videos(self) -> List[Dict]:
        """
        Busca novos vídeos virais do YouTube.
        
        Returns:
            Lista de dicionários com informações dos vídeos
        """
        try:
            logger.info("Buscando novos vídeos virais")
            videos = []
            
            # Queries específicas por categoria
            search_queries = {
                'gaming': [
                    'best gaming moments 2024',
                    'viral gaming clips',
                    'gaming highlights week',
                    'funny gaming moments'
                ],
                'sports': [
                    'amazing sports moments 2024',
                    'sports highlights week',
                    'incredible sports plays',
                    'best sports clips'
                ],
                'entertainment': [
                    'viral videos 2024',
                    'trending entertainment',
                    'funny moments compilation',
                    'best viral clips'
                ],
                'music': [
                    'viral music moments',
                    'music highlights 2024',
                    'best music clips',
                    'trending music videos'
                ]
            }
            
            for category, queries in search_queries.items():
                logger.info(f"Buscando vídeos da categoria: {category}")
                
                for query in queries:
                    try:
                        search_results = self._search_videos(query, max_results=5)
                        
                        for video in search_results:
                            video_id = video['id']
                            
                            # Pula vídeos já processados
                            if video_id in self.processed_videos:
                                continue
                                
                            # Adiciona categoria ao vídeo
                            video['category'] = category
                            videos.append(video)
                            
                            # Limita a 5 vídeos por categoria
                            if len([v for v in videos if v['category'] == category]) >= 5:
                                break
                                
                    except Exception as e:
                        logger.error(f"Erro buscando '{query}' em {category}: {str(e)}")
                        continue
                        
                    # Espera entre queries para evitar bloqueio
                    time.sleep(random.uniform(2, 4))
            
            # Ordena por visualizações
            videos.sort(key=lambda x: x.get('view_count', 0), reverse=True)
            
            logger.info(f"Encontrados {len(videos)} novos vídeos no total")
            return videos
            
        except Exception as e:
            logger.error(f"Erro buscando novos vídeos: {str(e)}")
            return []

    def download_video(self, url: str) -> Optional[str]:
        """
        Baixa um vídeo do YouTube usando yt-dlp.
        
        Args:
            url: URL do vídeo
            
        Returns:
            Caminho para o arquivo baixado ou None se falhar
        """
        try:
            # Cria diretório de downloads se não existir
            download_dir = Path('downloads')
            download_dir.mkdir(exist_ok=True)
            
            # Extrai ID do vídeo da URL
            video_id = self._extract_video_id(url)
            if not video_id:
                logger.error(f"ID do vídeo não encontrado na URL: {url}")
                return None
                
            # Define arquivo de saída
            output_path = str(download_dir / f"{video_id}.mp4")
            
            # Configura opções do yt-dlp
            ydl_opts = {
                'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            # Baixa o vídeo
            logger.info(f"Baixando vídeo {video_id}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if os.path.exists(output_path):
                logger.info(f"Vídeo baixado com sucesso: {output_path}")
                return output_path
            else:
                logger.error(f"Arquivo não encontrado após download: {output_path}")
                return None
                
        except Exception as e:
            logger.error(f"Erro baixando vídeo {url}: {str(e)}")
            return None

def get_random_viral_video() -> Optional[str]:
    """
    Helper function to get a random viral video URL.
    """
    try:
        scraper = YouTubeScraper()
        videos = list(scraper.get_viral_video())  # Convert generator to list
        if not videos:
            logger.warning("No viral videos found")
            return None
        video = random.choice(videos)
        return video['url']
    except Exception as e:
        logger.error(f"Error getting random viral video: {str(e)}")
        return None
