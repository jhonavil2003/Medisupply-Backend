"""Servicio para procesamiento de videos con OpenCV."""

import cv2
import os
import requests
import hashlib
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from urllib.parse import urlparse

from src.utils.config import Config

logger = logging.getLogger(__name__)


class VideoProcessorService:
    """Servicio para procesamiento de videos con OpenCV."""
    
    def __init__(self, upload_folder: Optional[str] = None):
        """
        Inicializa el servicio de procesamiento de video.
        
        Args:
            upload_folder: Directorio para guardar frames temporales
        """
        self.upload_folder = upload_folder or str(Config.UPLOAD_DIR / 'frames')
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VideoProcessorService initialized (folder: {self.upload_folder})")
    
    async def extract_frames(
        self,
        video_path: str,
        max_frames: Optional[int] = None
    ) -> List[str]:
        """
        Extrae frames clave del video.
        
        Estrategia de extracción:
        - Calcula FPS y duración del video
        - Distribuye frames uniformemente en el tiempo
        - Evita frames consecutivos muy similares
        - Prioriza frames con más información visual
        
        Args:
            video_path: Ruta local o URL del video
            max_frames: Máximo de frames a extraer (default: Config.MAX_FRAMES_PER_VIDEO)
        
        Returns:
            Lista de rutas absolutas a frames extraídos
        
        Raises:
            ValueError: Si el video no se puede abrir o es inválido
            Exception: Si hay errores durante la extracción
        
        Example:
            >>> processor = VideoProcessorService()
            >>> frames = await processor.extract_frames("video.mp4", max_frames=5)
            >>> print(frames)
            ['/app/uploads/frames/frame_0000.jpg', ...]
        """
        max_frames = max_frames or Config.MAX_FRAMES_PER_VIDEO
        
        logger.info(f"🎬 Starting frame extraction from: {video_path}")
        logger.info(f"   Max frames: {max_frames}")
        
        try:
            # ===== PASO 1: Descargar video si es URL =====
            if video_path.startswith(('http://', 'https://')):
                logger.info("   Video is URL, downloading...")
                video_path = await self._download_video(video_path)
                logger.info(f"   ✓ Video downloaded to: {video_path}")
            
            # ===== PASO 2: Validar que el archivo existe =====
            if not os.path.exists(video_path):
                raise ValueError(f"Video file not found: {video_path}")
            
            # ===== PASO 3: Abrir video con OpenCV =====
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            # ===== PASO 4: Obtener información del video =====
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration_seconds = total_frames / fps if fps > 0 else 0
            
            logger.info(f"   Video info: {total_frames} frames, {fps:.2f} fps, {duration_seconds:.1f}s")
            
            # Validar que el video tenga frames
            if total_frames == 0:
                raise ValueError("Video has no frames")
            
            # ===== PASO 5: Calcular intervalo de extracción =====
            # Distribuir frames uniformemente en el video
            interval = max(1, total_frames // max_frames)
            logger.info(f"   Extraction interval: every {interval} frames")
            
            # ===== PASO 6: Extraer frames =====
            frame_paths = []
            frame_count = 0
            extracted = 0
            
            # Generar ID único para esta sesión
            session_id = self._generate_session_id(video_path)
            
            while cap.isOpened() and extracted < max_frames:
                ret, frame = cap.read()
                
                if not ret:
                    logger.info(f"   End of video reached at frame {frame_count}")
                    break
                
                # Extraer frame si está en el intervalo
                if frame_count % interval == 0:
                    # Validar que el frame no esté corrupto o vacío
                    if frame is not None and frame.size > 0:
                        frame_path = self._save_frame(
                            frame,
                            session_id,
                            extracted
                        )
                        frame_paths.append(frame_path)
                        extracted += 1
                        logger.debug(f"   ✓ Frame {extracted}/{max_frames} extracted")
                
                frame_count += 1
            
            # ===== PASO 7: Liberar recursos =====
            cap.release()
            
            logger.info(f"✅ Frame extraction completed: {len(frame_paths)} frames")
            
            # ===== PASO 8: Validar que se extrajeron frames =====
            if not frame_paths:
                raise ValueError("No frames could be extracted from video")
            
            return frame_paths
            
        except Exception as e:
            logger.error(f"❌ Error extracting frames: {str(e)}")
            raise
    
    async def _download_video(self, url: str) -> str:
        """
        Descarga video desde URL (HTTP/HTTPS/S3).
        
        Args:
            url: URL del video (soporta HTTP, HTTPS y S3)
        
        Returns:
            Path local al video descargado
        
        Raises:
            requests.exceptions.RequestException: Si hay errores de descarga
        """
        logger.info(f"📥 Downloading video from: {url}")
        
        # Generar nombre único basado en URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"video_{timestamp}_{url_hash}.mp4"
        video_path = os.path.join(self.upload_folder, video_filename)
        
        # Detectar si es una URL de S3
        parsed_url = urlparse(url)
        # Detectar diferentes formatos de URLs de S3:
        # - bucket.s3.region.amazonaws.com/key
        # - bucket.s3.amazonaws.com/key
        # - s3.region.amazonaws.com/bucket/key
        is_s3_url = (
            '.s3.' in parsed_url.netloc and 'amazonaws.com' in parsed_url.netloc
        ) or (
            parsed_url.netloc.startswith('s3.') and 'amazonaws.com' in parsed_url.netloc
        )
        
        if is_s3_url:
            # Descargar desde S3
            logger.info(f"   Detected S3 URL: {parsed_url.netloc}")
            return await self._download_from_s3(url, video_path)
        else:
            # Descargar desde HTTP/HTTPS
            logger.info(f"   Detected HTTP/HTTPS URL: {parsed_url.netloc}")
            return await self._download_from_http(url, video_path)
    
    async def _download_from_s3(self, url: str, video_path: str) -> str:
        """
        Descarga video desde S3 usando boto3.
        
        Args:
            url: URL de S3 (formato: https://bucket-name.s3.region.amazonaws.com/key)
            video_path: Path donde guardar el video
        
        Returns:
            Path al archivo descargado
        """
        try:
            # Parsear URL de S3
            parsed_url = urlparse(url)
            
            # Extraer bucket y key
            # Formato: https://bucket-name.s3.region.amazonaws.com/path/to/file.mp4
            if parsed_url.netloc.endswith('.s3.amazonaws.com'):
                # Formato: bucket-name.s3.region.amazonaws.com
                bucket_name = parsed_url.netloc.split('.')[0]
            else:
                bucket_name = Config.AWS_BUCKET_NAME
            
            # Key es el path sin el leading slash
            key = parsed_url.path.strip('/')
            
            logger.info(f"   S3 Bucket: {bucket_name}")
            logger.info(f"   S3 Key: {key}")
            
            # Crear cliente S3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_REGION
            )
            
            # Descargar archivo
            logger.info(f"   Downloading from S3...")
            s3_client.download_file(bucket_name, key, video_path)
            
            logger.info(f"✅ Video downloaded from S3: {video_path}")
            return video_path
            
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found")
            raise ValueError(
                "AWS credentials not configured. Please set AWS_ACCESS_KEY_ID "
                "and AWS_SECRET_ACCESS_KEY in .env file"
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"❌ S3 download error: {error_code} - {str(e)}")
            raise ValueError(f"Cannot download video from S3: {error_code}. {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected S3 error: {str(e)}")
            raise ValueError(f"Cannot download video from S3: {str(e)}")
    
    async def _download_from_http(self, url: str, video_path: str) -> str:
        """
        Descarga video desde HTTP/HTTPS.
        
        Args:
            url: URL HTTP/HTTPS del video
            video_path: Path donde guardar el video
        
        Returns:
            Path al archivo descargado
        """
        try:
            # Descargar con streaming para videos grandes
            response = requests.get(
                url,
                stream=True,
                timeout=Config.VIDEO_DOWNLOAD_TIMEOUT,
                headers={'User-Agent': 'MediSupply-VideoService/1.0'}
            )
            response.raise_for_status()
            
            # Verificar Content-Type
            content_type = response.headers.get('Content-Type', '')
            if 'video' not in content_type.lower():
                logger.warning(f"⚠️ Unexpected Content-Type: {content_type}")
            
            # Verificar tamaño del video
            content_length = response.headers.get('Content-Length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                logger.info(f"   Video size: {size_mb:.2f} MB")
                
                if size_mb > Config.MAX_VIDEO_SIZE_MB:
                    raise ValueError(
                        f"Video too large: {size_mb:.2f}MB "
                        f"(max: {Config.MAX_VIDEO_SIZE_MB}MB)"
                    )
            
            # Escribir video a disco
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"✅ Video downloaded successfully: {video_path}")
            return video_path
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Download timeout after {Config.VIDEO_DOWNLOAD_TIMEOUT}s")
            raise ValueError(
                f"Video download timeout. URL may be slow or unreachable: {url}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Download error: {str(e)}")
            raise ValueError(f"Cannot download video from URL: {url}. Error: {str(e)}")
    
    def _save_frame(
        self,
        frame,
        session_id: str,
        frame_index: int
    ) -> str:
        """
        Guarda un frame como imagen JPEG.
        
        Args:
            frame: Frame de OpenCV (numpy array)
            session_id: ID único de la sesión
            frame_index: Índice del frame
        
        Returns:
            Path absoluto al frame guardado
        """
        # Generar nombre de archivo
        frame_filename = f"frame_{session_id}_{frame_index:04d}.jpg"
        frame_path = os.path.join(self.upload_folder, frame_filename)
        
        # Guardar con compresión JPEG (calidad 85%)
        cv2.imwrite(
            frame_path,
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 85]
        )
        
        return frame_path
    
    def _generate_session_id(self, video_path: str) -> str:
        """
        Genera ID único para la sesión de procesamiento.
        
        Args:
            video_path: Path o URL del video
        
        Returns:
            ID de sesión (8 caracteres)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path_hash = hashlib.md5(video_path.encode()).hexdigest()[:4]
        return f"{timestamp}_{path_hash}"
    
    def cleanup_frames(self, frame_paths: List[str]):
        """
        Elimina frames temporales del disco.
        
        Args:
            frame_paths: Lista de paths a frames a eliminar
        """
        logger.info(f"🧹 Cleaning up {len(frame_paths)} frames...")
        
        deleted = 0
        for path in frame_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    deleted += 1
            except Exception as e:
                logger.warning(f"   ⚠️ Could not delete {path}: {e}")
        
        logger.info(f"✅ Cleanup complete: {deleted}/{len(frame_paths)} frames deleted")
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Limpia archivos antiguos del directorio de uploads.
        
        Args:
            max_age_hours: Edad máxima en horas
        """
        logger.info(f"🧹 Cleaning up files older than {max_age_hours}h...")
        
        now = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        deleted = 0
        
        for filename in os.listdir(self.upload_folder):
            filepath = os.path.join(self.upload_folder, filename)
            
            try:
                file_age = now - os.path.getmtime(filepath)
                
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    deleted += 1
                    logger.debug(f"   ✓ Deleted old file: {filename}")
            except Exception as e:
                logger.warning(f"   ⚠️ Could not process {filename}: {e}")
        
        logger.info(f"✅ Cleanup complete: {deleted} old files deleted")
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Obtiene información técnica del video.
        
        Args:
            video_path: Path al video
        
        Returns:
            Diccionario con información del video
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return {'error': 'Cannot open video'}
        
        info = {
            'frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration_seconds': 0,
            'codec': int(cap.get(cv2.CAP_PROP_FOURCC)),
        }
        
        if info['fps'] > 0:
            info['duration_seconds'] = info['frames'] / info['fps']
        
        cap.release()
        
        return info
