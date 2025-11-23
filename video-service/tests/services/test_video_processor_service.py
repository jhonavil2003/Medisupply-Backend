import pytest
from unittest.mock import Mock, patch, mock_open
from src.services.video_processor_service import VideoProcessorService


class TestVideoProcessorService:
    
    def test_init_creates_upload_folder(self, tmp_path):
        """Test que el servicio crea el directorio de uploads"""
        # Arrange
        upload_folder = str(tmp_path / "test_frames")
        
        # Act
        service = VideoProcessorService(upload_folder)
        
        # Assert
        assert service.upload_folder == upload_folder
    
    @pytest.mark.asyncio
    @patch('src.services.video_processor_service.cv2.VideoCapture')
    @patch('src.services.video_processor_service.os.path.exists')
    async def test_extract_frames_from_local_video(self, mock_exists, mock_cv2_capture, tmp_path):
        """Test extracción de frames de video local"""
        # Arrange
        service = VideoProcessorService(str(tmp_path))
        mock_exists.return_value = True
        
        # Mock OpenCV VideoCapture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        # Usar los valores reales de las constantes de OpenCV
        mock_cap.get.side_effect = lambda prop: {
            7: 100,  # cv2.CAP_PROP_FRAME_COUNT
            5: 30.0,  # cv2.CAP_PROP_FPS
        }.get(prop, 0)
        
        # Mock frame reading
        mock_frame = Mock()
        mock_frame.size = 1000
        mock_cap.read.side_effect = [
            (True, mock_frame),
            (True, mock_frame),
            (True, mock_frame),
            (False, None)  # End of video
        ]
        
        mock_cv2_capture.return_value = mock_cap
        
        # Mock cv2.imwrite
        with patch('src.services.video_processor_service.cv2.imwrite'):
            # Act
            frames = await service.extract_frames("test_video.mp4", max_frames=3)
            
            # Assert
            assert len(frames) > 0
            mock_cap.release.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.video_processor_service.VideoProcessorService._download_video')
    @patch('src.services.video_processor_service.os.path.exists')
    async def test_extract_frames_downloads_url_first(self, mock_exists, mock_download):
        """Test que extrae frames descarga primero si es URL"""
        # Arrange
        service = VideoProcessorService()
        mock_download.return_value = "/tmp/downloaded.mp4"
        mock_exists.return_value = False
        
        # Act & Assert
        with pytest.raises(ValueError):
            await service.extract_frames("https://example.com/video.mp4")
        
        mock_download.assert_called_once()
    
    def test_cleanup_frames_deletes_files(self, sample_frame_paths):
        """Test que cleanup elimina frames correctamente"""
        # Arrange
        service = VideoProcessorService()
        
        # Act
        service.cleanup_frames(sample_frame_paths)
        
        # Assert - verificar que los archivos no existen más
        import os
        for path in sample_frame_paths:
            assert not os.path.exists(path)
    
    @patch('src.services.video_processor_service.cv2.VideoCapture')
    def test_get_video_info_returns_metadata(self, mock_cv2_capture):
        """Test que get_video_info retorna información correcta"""
        # Arrange
        service = VideoProcessorService()
        
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            7: 300,    # FRAME_COUNT
            5: 30.0,   # FPS
            3: 1920,   # WIDTH
            4: 1080,   # HEIGHT
            6: 1234,   # FOURCC
        }.get(prop, 0)
        mock_cv2_capture.return_value = mock_cap
        
        # Act
        info = service.get_video_info("test.mp4")
        
        # Assert
        assert info['frames'] == 300
        assert info['fps'] == 30.0
        assert info['width'] == 1920
        assert info['height'] == 1080
        assert info['duration_seconds'] == 10.0  # 300/30
        mock_cap.release.assert_called_once()
