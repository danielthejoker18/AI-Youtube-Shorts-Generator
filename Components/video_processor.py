import os
from typing import List, Dict, Any, Tuple
import numpy as np
import cv2
import torch
import mediapipe as mp
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from .logger import get_logger
import moviepy_conf
import json

logger = get_logger(__name__)

class VideoProcessor:
    def __init__(
        self,
        video_path: str,
        output_dir: str,
        target_fps: int = 30,
        face_detection_confidence: float = 0.5,
        max_faces: int = 3
    ):
        """
        Inicializa o processador de vídeo.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            output_dir: Diretório de saída
            target_fps: FPS alvo para o vídeo processado
            face_detection_confidence: Confiança mínima para detecção de faces
            max_faces: Número máximo de faces a serem detectadas
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.target_fps = target_fps
        self.face_detection_confidence = face_detection_confidence
        self.max_faces = max_faces
        
        # Histórico de posições para suavização
        self.position_history = []
        self.history_size = 30  # Mantém histórico de 1 segundo (30 frames)
        self.current_crop_x = None
        
        # Configura logging
        self.logger = get_logger(__name__)
        self.logger.info(f"Inicializando processador de vídeo para: {video_path}")
        
        # Verifica se o arquivo de vídeo existe
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")
            
        # Verifica se o diretório de saída existe, se não, cria
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Configura device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.logger.info(f"Usando device: {self.device}")
        
        # Inicializa MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=face_detection_confidence
        )
        
        self.logger.info("Processador de vídeo inicializado com sucesso")

    def _detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta faces em um frame.
        
        Args:
            frame: Frame do vídeo
            
        Returns:
            Lista de tuplas (x, y, w, h) representando as faces detectadas
        """
        try:
            # Converte para RGB se necessário
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            
            # Detecta faces usando mediapipe
            results = self.face_detector.process(frame)
            faces = []
            
            if results.detections:
                img_height, img_width = frame.shape[:2]
                
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    
                    # Converte coordenadas relativas para absolutas
                    x = int(bbox.xmin * img_width)
                    y = int(bbox.ymin * img_height)
                    w = int(bbox.width * img_width)
                    h = int(bbox.height * img_height)
                    
                    # Adiciona margem para incluir mais do rosto
                    margin = 0.2  # 20% de margem
                    x = max(0, int(x - w * margin))
                    y = max(0, int(y - h * margin))
                    w = min(img_width - x, int(w * (1 + 2 * margin)))
                    h = min(img_height - y, int(h * (1 + 2 * margin)))
                    
                    faces.append((x, y, w, h))
                    
                self.logger.debug(f"Detectadas {len(faces)} faces no frame")
            
            return faces
            
        except Exception as e:
            self.logger.error(f"Erro detectando faces: {e}")
            return []

    def _get_smart_crop(self, frame: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Determina a melhor região para crop baseado no movimento da cena.
        O crop será sempre vertical (9:16) para TikTok e YouTube Shorts.
        Usa suavização temporal para evitar movimentos bruscos.
        
        Args:
            frame: Frame do vídeo
            
        Returns:
            Tupla (x, y, w, h) da região de crop
        """
        frame_height, frame_width = frame.shape[:2]
        target_ratio = 9/16  # Proporção vertical para shorts
        
        # Calcula a largura do crop mantendo a altura original
        crop_width = int(frame_height * target_ratio)
        
        if crop_width >= frame_width:
            # Se o frame já é mais estreito que 9:16, usa o frame inteiro
            return 0, 0, frame_width, frame_height
            
        # Define a região central como área principal
        center_x = frame_width // 2
        
        # Detecta faces como referência secundária
        faces = self._detect_faces(frame)
        
        if faces:
            # Se houver faces, usa a mediana das posições para evitar outliers
            face_positions = [x + w//2 for x, _, w, _ in faces]
            face_positions.sort()
            face_center_x = face_positions[len(face_positions)//2]  # Mediana
            # Aplica peso: 80% centro do frame, 20% centro das faces
            target_x = int(0.8 * center_x + 0.2 * face_center_x)
        else:
            # Se não houver faces, mantém o foco no centro
            target_x = center_x
        
        # Calcula a posição inicial do crop
        initial_x = max(0, min(target_x - crop_width // 2, frame_width - crop_width))
        
        # Aplica suavização temporal
        if self.current_crop_x is None:
            self.current_crop_x = initial_x
        
        # Atualiza histórico
        self.position_history.append(initial_x)
        if len(self.position_history) > self.history_size:
            self.position_history.pop(0)
        
        # Calcula média móvel com mais peso para posições recentes
        weights = [i/len(self.position_history) for i in range(1, len(self.position_history) + 1)]
        total_weight = sum(weights)
        smooth_x = sum(x * w for x, w in zip(self.position_history, weights)) / total_weight
        
        # Limita a velocidade máxima de movimento
        max_movement = 5  # pixels por frame
        target_movement = smooth_x - self.current_crop_x
        actual_movement = max(min(target_movement, max_movement), -max_movement)
        
        # Atualiza posição atual
        self.current_crop_x += actual_movement
        
        # Garante que o crop está dentro dos limites
        final_x = max(0, min(int(self.current_crop_x), frame_width - crop_width))
        
        return final_x, 0, crop_width, frame_height

    def _process_frame_gpu(self, frame: np.ndarray) -> np.ndarray:
        """
        Processa frame usando GPU via PyTorch.
        
        Args:
            frame: Frame do vídeo em formato NumPy
            
        Returns:
            Frame processado em formato NumPy
        """
        # Converte NumPy para tensor PyTorch
        frame_tensor = torch.from_numpy(frame).to(self.device)
        
        # Normaliza valores para [0, 1]
        if frame_tensor.dtype == torch.uint8:
            frame_tensor = frame_tensor.float() / 255.0
        
        # Aqui você pode adicionar processamento GPU como:
        # - Redimensionamento
        # - Filtros de imagem
        # - Transformações de cor
        # - etc
        
        # Volta para [0, 255] e converte para uint8
        frame_tensor = (frame_tensor * 255).clamp(0, 255).byte()
        
        # Converte tensor PyTorch de volta para NumPy
        return frame_tensor.cpu().numpy()

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Processa um frame do vídeo.
        
        Args:
            frame: Frame do vídeo
            
        Returns:
            Frame processado
        """
        try:
            # Log das dimensões do frame original
            h, w = frame.shape[:2]
            self.logger.debug(f"Frame original: {w}x{h}")
            
            # Converte para GPU se disponível
            if self.device.type == 'cuda':
                frame = self._process_frame_gpu(frame)
            
            # Aplica crop inteligente
            x, y, w, h = self._get_smart_crop(frame)
            
            # Verifica se as dimensões do crop são válidas
            if w <= 0 or h <= 0:
                self.logger.error(f"Dimensões de crop inválidas: w={w}, h={h}")
                return frame
                
            if x < 0 or y < 0:
                self.logger.error(f"Posição de crop inválida: x={x}, y={y}")
                return frame
                
            if x + w > frame.shape[1] or y + h > frame.shape[0]:
                self.logger.error(f"Crop ultrapassa limites do frame: x+w={x+w}, y+h={y+h}")
                return frame
            
            # Aplica o crop
            cropped = frame[y:y+h, x:x+w]
            
            # Log das dimensões após crop
            ch, cw = cropped.shape[:2]
            self.logger.debug(f"Frame após crop: {cw}x{ch}")
            
            # Verifica se o resultado está na proporção correta
            ratio = ch / cw
            target_ratio = 16 / 9  # Queremos altura/largura = 16/9
            if abs(ratio - target_ratio) > 0.1:  # 10% de tolerância
                self.logger.warning(f"Proporção do frame ({ratio:.2f}) difere do alvo (1.78)")
            
            return cropped
            
        except Exception as e:
            self.logger.error(f"Erro processando frame: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return frame

    def _add_subtitles(self, clip: VideoFileClip, text: str, start_time: float, end_time: float) -> CompositeVideoClip:
        """
        Adiciona legendas a um clipe de vídeo.
        
        Args:
            clip: Clipe de vídeo
            text: Texto da legenda
            start_time: Tempo inicial da legenda
            end_time: Tempo final da legenda
            
        Returns:
            Clipe com legendas
        """
        # Cria o clipe de texto
        txt_clip = TextClip(
            text,
            font='Arial',
            fontsize=24,
            color='white',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(clip.w * 0.8, None),  # Largura máxima de 80% do vídeo
            align='center'
        )
        
        # Posiciona o texto na parte inferior
        txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(end_time - start_time)
        
        # Compõe o vídeo com o texto
        return CompositeVideoClip([clip, txt_clip])

    def process_video_segments(self, segments: List[dict], output_path: str) -> None:
        """
        Processa os segmentos de vídeo e gera o vídeo final.
        """
        try:
            processed_clips = []
            
            # Obtém o título do vídeo do caminho do arquivo
            video_id = os.path.splitext(os.path.basename(self.video_path))[0]
            
            # Carrega os metadados do vídeo
            with open('videos.json', 'r', encoding='utf-8') as f:
                videos_data = json.load(f)
                video_title = videos_data[video_id]['title']
            
            # Sanitiza o título para usar como nome de arquivo
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # Limita o tamanho do título
            
            # Atualiza o caminho de saída com o título
            output_dir = os.path.dirname(output_path)
            output_filename = f"{safe_title}_short.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            self.logger.info("Iniciando processamento dos segmentos de vídeo")
            
            # Carrega o vídeo original para obter informações
            with VideoFileClip(self.video_path) as video:
                original_width = video.w
                original_height = video.h
                original_duration = video.duration
                self.logger.info(f"Vídeo original: {original_width}x{original_height}, {original_duration:.2f}s")
            
            for i, segment in enumerate(segments):
                self.logger.info(f"Processando segmento {i+1}/{len(segments)}")
                
                start_time = segment['start']
                end_time = segment['end']
                text = segment.get('text', '')
                
                # Carrega o clip
                clip = VideoFileClip(self.video_path).subclip(start_time, end_time)
                
                # Calcula as dimensões para formato 9:16
                if clip.w > clip.h:
                    # Vídeo horizontal - precisa de crop
                    target_width = int(clip.h * 9/16)
                    target_height = clip.h
                else:
                    # Vídeo vertical - mantém altura e ajusta largura
                    target_width = clip.w
                    target_height = int(clip.w * 16/9)
                
                # Função para processar cada frame
                def process_frame_func(frame):
                    # Detecta faces
                    faces = self._detect_faces(frame)
                    
                    # Calcula o centro das faces ou usa o centro do frame
                    if faces:
                        center_x = int(np.mean([face[0] + face[2]/2 for face in faces]))
                    else:
                        center_x = frame.shape[1] // 2
                    
                    # Calcula as coordenadas do crop
                    x = max(0, min(center_x - target_width//2, frame.shape[1] - target_width))
                    y = 0
                    w = target_width
                    h = target_height
                    
                    # Aplica o crop
                    cropped = frame[y:y+h, x:x+w]
                    
                    # Redimensiona para as dimensões finais
                    return cv2.resize(cropped, (1080, 1920))
                
                # Aplica o processamento em cada frame
                self.logger.info(f"Aplicando processamento ao segmento {i+1}")
                processed_clip = clip.fl_image(process_frame_func)
                
                # Adiciona legendas se houver texto
                if text:
                    self.logger.info(f"Adicionando legendas ao segmento {i+1}")
                    processed_clip = self._add_subtitles(processed_clip, text, 0, end_time - start_time)
                
                processed_clips.append(processed_clip)
                clip.close()
            
            if not processed_clips:
                raise ValueError("Nenhum segmento foi processado com sucesso")
            
            # Concatena todos os clips
            self.logger.info("Concatenando clips...")
            final_clip = concatenate_videoclips(processed_clips)
            
            # Salva o vídeo final
            self.logger.info(f"Salvando vídeo final em: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=30,
                threads=1,
                preset='medium',
                ffmpeg_params=["-crf", "23"],
                logger=None
            )
            
            # Fecha todos os clips para liberar memória
            for clip in processed_clips:
                clip.close()
            final_clip.close()
            
            self.logger.info("Processamento de vídeo concluído com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro no processamento do vídeo: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
