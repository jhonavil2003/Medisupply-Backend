import pytest
from unittest.mock import Mock, patch
import cv2

from src.services.video_processor_service import VideoProcessorService


class TestVideoProcessorAdditional:
    
    @patch('os.path.exists', return_value=True)
    @patch('os.path.isfile', return_value=True)
    def test_cleanup_frames_with_existing_files(self, mock_isfile, mock_exists):
        """Test cleanup con archivos existentes"""
        service = VideoProcessorService()
        
        frame_paths = ["/tmp/frame1.jpg", "/tmp/frame2.jpg"]
        
        with patch('os.remove') as mock_remove:
            service.cleanup_frames(frame_paths)
            assert mock_remove.call_count == 2
    
    @patch('os.path.exists', return_value=False)
    def test_cleanup_frames_skips_missing_files(self, mock_exists):
        """Test cleanup skip archivos no existentes"""
        service = VideoProcessorService()
        
        frame_paths = ["/tmp/nonexistent.jpg"]
        
        with patch('os.remove') as mock_remove:
            service.cleanup_frames(frame_paths)
            mock_remove.assert_not_called()
    
    @patch('cv2.VideoCapture')
    def test_get_video_info_returns_all_fields(self, mock_cv2):
        """Test que get_video_info retorna todos los campos"""
        service = VideoProcessorService()
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 300,
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_WIDTH: 1920,
            cv2.CAP_PROP_FRAME_HEIGHT: 1080
        }.get(prop, 0)
        mock_cap.release = Mock()
        mock_cv2.return_value = mock_cap
        
        info = service.get_video_info("http://example.com/video.mp4")
        
        assert 'frames' in info
        assert 'fps' in info
        assert 'duration_seconds' in info
        assert 'width' in info
        assert 'height' in info
        assert info['frames'] == 300
        assert info['fps'] == 30.0
    
    def test_init_sets_upload_folder(self):
        """Test que __init__ establece upload_folder"""
        service = VideoProcessorService()
        assert service.upload_folder is not None
        assert 'uploads' in str(service.upload_folder)
    
    @patch('cv2.VideoCapture')
    def test_get_video_info_calculates_duration(self, mock_cv2):
        """Test que calcula duración correctamente"""
        service = VideoProcessorService()
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 90,
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_WIDTH: 1280,
            cv2.CAP_PROP_FRAME_HEIGHT: 720
        }.get(prop, 0)
        mock_cap.release = Mock()
        mock_cv2.return_value = mock_cap
        
        info = service.get_video_info("http://example.com/video.mp4")
        
        assert info['duration_seconds'] == 3.0  # 90 frames / 30 fps
    
    @patch('cv2.VideoCapture')
    def test_get_video_info_handles_closed_capture(self, mock_cv2):
        """Test manejo de video que no se puede abrir"""
        service = VideoProcessorService()
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cv2.return_value = mock_cap
        
        info = service.get_video_info("http://example.com/invalid.mp4")
        
        assert 'error' in info
        assert info['error'] == 'Cannot open video'
    
    @pytest.mark.asyncio
    @patch('cv2.VideoCapture')
    @patch('os.path.exists', return_value=True)
    async def test_extract_frames_with_local_file(self, mock_exists, mock_cv2):
        """Test extracción de frames de archivo local"""
        service = VideoProcessorService()
        
        # Crear mock de frame con size attribute
        mock_frame1 = Mock()
        mock_frame1.size = 100
        mock_frame2 = Mock()
        mock_frame2.size = 100
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 10,
            cv2.CAP_PROP_FPS: 30.0
        }.get(prop, 0)
        # Simular lectura de 10 frames (interval será 10/2=5, entonces lee frame 0 y frame 5)
        mock_cap.read.side_effect = [
            (True, mock_frame1),  # frame 0
            (True, Mock(size=100)),  # frame 1
            (True, Mock(size=100)),  # frame 2
            (True, Mock(size=100)),  # frame 3
            (True, Mock(size=100)),  # frame 4
            (True, mock_frame2),  # frame 5
            (False, None)  # end
        ]
        mock_cap.release = Mock()
        mock_cv2.return_value = mock_cap
        
        with patch('cv2.imwrite') as mock_imwrite:
            frames = await service.extract_frames("/local/video.mp4", max_frames=2)
            assert len(frames) == 2
            assert mock_imwrite.call_count == 2
