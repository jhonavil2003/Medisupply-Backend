import pytest
from unittest.mock import Mock, patch, AsyncMock
import cv2
import os

from src.services.video_processor_service import VideoProcessorService


class TestVideoProcessorCoverage:
    @pytest.mark.asyncio
    @patch('os.path.exists', return_value=False)
    async def test_extract_frames_local_file_not_found(self, mock_exists):
        """Test que extract_frames falla con archivo local no existente"""
        service = VideoProcessorService()
        
        with pytest.raises(ValueError, match="Video file not found"):
            await service.extract_frames("/nonexistent/video.mp4")
    
    @pytest.mark.asyncio
    @patch('cv2.VideoCapture')
    @patch('os.path.exists', return_value=True)
    async def test_extract_frames_cannot_open_video(self, mock_exists, mock_cv2):
        """Test que extract_frames falla cuando no se puede abrir el video"""
        service = VideoProcessorService()
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cv2.return_value = mock_cap
        
        with pytest.raises(ValueError, match="Cannot open video file"):
            await service.extract_frames("/local/video.mp4")
    
    @pytest.mark.asyncio
    @patch('cv2.VideoCapture')
    @patch('os.path.exists', return_value=True)
    async def test_extract_frames_zero_frames_video(self, mock_exists, mock_cv2):
        """Test que extract_frames falla con video sin frames"""
        service = VideoProcessorService()
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 0,
            cv2.CAP_PROP_FPS: 30.0
        }.get(prop, 0)
        mock_cap.release = Mock()
        mock_cv2.return_value = mock_cap
        
        with pytest.raises(ValueError, match="Video has no frames"):
            await service.extract_frames("/local/video.mp4")
    
    @pytest.mark.asyncio
    @patch('cv2.VideoCapture')
    @patch('os.path.exists', return_value=True)
    async def test_extract_frames_with_corrupted_frames(self, mock_exists, mock_cv2):
        """Test extracción skipeando frames corruptos (None)"""
        service = VideoProcessorService()
        
        mock_frame = Mock()
        mock_frame.size = 100
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 5,
            cv2.CAP_PROP_FPS: 30.0
        }.get(prop, 0)
        # Frame 0: None (corrupto), Frame 2: válido, Frame 4: válido
        mock_cap.read.side_effect = [
            (True, None),  # frame 0 corrupto
            (True, Mock(size=100)),  # frame 1
            (True, mock_frame),  # frame 2 válido
            (True, Mock(size=100)),  # frame 3
            (True, mock_frame),  # frame 4 válido
            (False, None)
        ]
        mock_cap.release = Mock()
        mock_cv2.return_value = mock_cap
        
        with patch('cv2.imwrite'):
            frames = await service.extract_frames("/local/video.mp4", max_frames=3)
            # Solo extrae frames no corruptos (frame None se skipea)
            assert len(frames) >= 1
    
    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_download_video_http_success(self, mock_get):
        """Test descarga HTTP exitosa"""
        service = VideoProcessorService()
        
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b'video', b'data'])
        mock_response.raise_for_status = Mock()
        mock_response.headers = {}  # Agregar headers vacío para el check
        mock_get.return_value = mock_response
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = await service._download_from_http("http://example.com/video.mp4", "/tmp/video.mp4")
            
            assert result == "/tmp/video.mp4"
            mock_file.write.assert_called()
    
    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_download_video_http_fails(self, mock_get):
        """Test fallo en descarga HTTP"""
        import requests
        service = VideoProcessorService()
        
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        with pytest.raises(ValueError, match="Cannot download video from URL"):
            await service._download_from_http("http://example.com/video.mp4", "/tmp/video.mp4")
    
    def test_generate_session_id(self):
        """Test generación de session ID único"""
        service = VideoProcessorService()
        
        session_id1 = service._generate_session_id("/path/to/video1.mp4")
        session_id2 = service._generate_session_id("/path/to/video2.mp4")
        
        assert isinstance(session_id1, str)
        assert len(session_id1) > 0
        assert session_id1 != session_id2  # Diferentes videos = diferentes IDs
    
    def test_cleanup_old_files(self):
        """Test cleanup de archivos antiguos"""
        service = VideoProcessorService()
        
        with patch('os.listdir', return_value=['old_file.jpg']):
            with patch('os.path.getmtime', return_value=0):  # Archivo muy antiguo
                with patch('os.remove') as mock_remove:
                    service.cleanup_old_files(max_age_hours=1)
                    mock_remove.assert_called_once()
    
    def test_cleanup_old_files_handles_errors(self):
        """Test que cleanup maneja errores gracefully"""
        service = VideoProcessorService()
        
        with patch('os.listdir', return_value=['file1.jpg', 'file2.jpg']):
            with patch('os.path.getmtime', return_value=0):
                with patch('os.remove', side_effect=Exception("Permission denied")):
                    # No debe lanzar excepción
                    service.cleanup_old_files(max_age_hours=1)
    
    @patch('cv2.VideoCapture')
    def test_get_video_info_calculates_codec(self, mock_cv2):
        """Test que get_video_info incluye información de codec"""
        service = VideoProcessorService()
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 100,
            cv2.CAP_PROP_FPS: 25.0,
            cv2.CAP_PROP_FRAME_WIDTH: 1280,
            cv2.CAP_PROP_FRAME_HEIGHT: 720,
            cv2.CAP_PROP_FOURCC: 1234
        }.get(prop, 0)
        mock_cap.release = Mock()
        mock_cv2.return_value = mock_cap
        
        info = service.get_video_info("/path/to/video.mp4")
        
        assert 'codec' in info
        assert info['codec'] == 1234
        assert info['duration_seconds'] == 4.0  # 100 frames / 25 fps
