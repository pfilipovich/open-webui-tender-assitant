import io
import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from open_webui.test.util.abstract_integration_test import AbstractPostgresTest
from open_webui.test.util.mock_user import mock_webui_user


class TestAudio(AbstractPostgresTest):
    BASE_PATH = "/api/v1/audio"

    def setup_class(cls):
        super().setup_class()

    def test_speech_to_text_upload(self):
        """Test speech to text conversion with file upload"""
        with mock_webui_user():
            # Create a mock audio file
            audio_content = b"fake audio content"
            audio_file = io.BytesIO(audio_content)
            
            with patch('open_webui.routers.audio.speech_to_text') as mock_stt:
                mock_stt.return_value = "Transcribed text"
                
                response = self.fast_api_client.post(
                    self.create_url("/speech-to-text"),
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )
                
        assert response.status_code == 200
        assert response.json() == "Transcribed text"

    def test_speech_to_text_large_file(self):
        """Test speech to text with file size validation"""
        with mock_webui_user():
            # Create a mock large audio file
            large_content = b"x" * (25 * 1024 * 1024)  # 25MB
            audio_file = io.BytesIO(large_content)
            
            response = self.fast_api_client.post(
                self.create_url("/speech-to-text"),
                files={"file": ("large.wav", audio_file, "audio/wav")}
            )
                
        assert response.status_code == 413  # Payload too large

    def test_speech_to_text_invalid_format(self):
        """Test speech to text with invalid audio format"""
        with mock_webui_user():
            # Create a mock non-audio file
            text_content = b"This is not audio"
            text_file = io.BytesIO(text_content)
            
            response = self.fast_api_client.post(
                self.create_url("/speech-to-text"),
                files={"file": ("test.txt", text_file, "text/plain")}
            )
                
        assert response.status_code == 400

    def test_text_to_speech_synthesis(self):
        """Test text to speech synthesis"""
        with mock_webui_user():
            with patch('open_webui.routers.audio.text_to_speech') as mock_tts:
                mock_tts.return_value = b"fake audio data"
                
                response = self.fast_api_client.post(
                    self.create_url("/text-to-speech"),
                    json={
                        "text": "Hello world",
                        "voice": "default",
                        "speed": 1.0
                    }
                )
                
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_text_to_speech_empty_text(self):
        """Test text to speech with empty text"""
        with mock_webui_user():
            response = self.fast_api_client.post(
                self.create_url("/text-to-speech"),
                json={
                    "text": "",
                    "voice": "default"
                }
            )
                
        assert response.status_code == 400

    def test_text_to_speech_invalid_voice(self):
        """Test text to speech with invalid voice"""
        with mock_webui_user():
            response = self.fast_api_client.post(
                self.create_url("/text-to-speech"),
                json={
                    "text": "Hello world",
                    "voice": "nonexistent_voice"
                }
            )
                
        assert response.status_code == 400

    def test_get_available_voices(self):
        """Test getting available TTS voices"""
        with mock_webui_user():
            with patch('open_webui.routers.audio.get_available_voices') as mock_voices:
                mock_voices.return_value = ["voice1", "voice2", "voice3"]
                
                response = self.fast_api_client.get(self.create_url("/voices"))
                
        assert response.status_code == 200
        assert response.json() == ["voice1", "voice2", "voice3"]

    def test_audio_conversion_required(self):
        """Test audio conversion requirement check"""
        with mock_webui_user():
            with patch('open_webui.routers.audio.is_audio_conversion_required') as mock_check:
                mock_check.return_value = True
                
                response = self.fast_api_client.post(
                    self.create_url("/check-conversion"),
                    json={"file_path": "/path/to/audio.m4a"}
                )
                
        assert response.status_code == 200
        assert response.json()["conversion_required"] is True

    def test_audio_conversion(self):
        """Test audio format conversion"""
        with mock_webui_user():
            audio_content = b"fake audio content"
            audio_file = io.BytesIO(audio_content)
            
            with patch('open_webui.routers.audio.convert_audio') as mock_convert:
                mock_convert.return_value = b"converted audio"
                
                response = self.fast_api_client.post(
                    self.create_url("/convert"),
                    files={"file": ("test.m4a", audio_file, "audio/m4a")},
                    data={"target_format": "mp3"}
                )
                
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mp3"

    def test_audio_split_on_silence(self):
        """Test audio splitting on silence detection"""
        with mock_webui_user():
            audio_content = b"fake audio content"
            audio_file = io.BytesIO(audio_content)
            
            with patch('open_webui.routers.audio.split_audio_on_silence') as mock_split:
                mock_split.return_value = [b"chunk1", b"chunk2", b"chunk3"]
                
                response = self.fast_api_client.post(
                    self.create_url("/split"),
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={
                        "silence_threshold": "-40",
                        "min_silence_duration": "500"
                    }
                )
                
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_count"] == 3

    def test_audio_transcription_with_language(self):
        """Test audio transcription with specific language"""
        with mock_webui_user():
            audio_content = b"fake audio content"
            audio_file = io.BytesIO(audio_content)
            
            with patch('open_webui.routers.audio.speech_to_text') as mock_stt:
                mock_stt.return_value = "Transcribed text in Spanish"
                
                response = self.fast_api_client.post(
                    self.create_url("/speech-to-text"),
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"language": "es"}
                )
                
        assert response.status_code == 200
        assert response.json() == "Transcribed text in Spanish"

    def test_audio_transcription_with_timestamp(self):
        """Test audio transcription with timestamp information"""
        with mock_webui_user():
            audio_content = b"fake audio content"
            audio_file = io.BytesIO(audio_content)
            
            with patch('open_webui.routers.audio.speech_to_text_with_timestamps') as mock_stt:
                mock_stt.return_value = {
                    "text": "Hello world",
                    "segments": [
                        {"start": 0.0, "end": 1.0, "text": "Hello"},
                        {"start": 1.0, "end": 2.0, "text": "world"}
                    ]
                }
                
                response = self.fast_api_client.post(
                    self.create_url("/speech-to-text/timestamps"),
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )
                
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Hello world"
        assert len(data["segments"]) == 2

    def test_audio_processing_admin_only(self):
        """Test admin-only audio processing endpoints"""
        with mock_webui_user(role="user"):
            response = self.fast_api_client.post(
                self.create_url("/admin/process-batch"),
                json={"files": ["file1.wav", "file2.wav"]}
            )
                
        assert response.status_code == 403

        with mock_webui_user(role="admin"):
            with patch('open_webui.routers.audio.process_audio_batch') as mock_batch:
                mock_batch.return_value = {"processed": 2, "failed": 0}
                
                response = self.fast_api_client.post(
                    self.create_url("/admin/process-batch"),
                    json={"files": ["file1.wav", "file2.wav"]}
                )
                
        assert response.status_code == 200
        assert response.json()["processed"] == 2

    def test_audio_cache_management(self):
        """Test audio cache management"""
        with mock_webui_user(role="admin"):
            with patch('open_webui.routers.audio.clear_audio_cache') as mock_clear:
                mock_clear.return_value = {"cleared_files": 5, "size_freed": "1.2MB"}
                
                response = self.fast_api_client.delete(self.create_url("/cache"))
                
        assert response.status_code == 200
        data = response.json()
        assert data["cleared_files"] == 5
        assert data["size_freed"] == "1.2MB"

    def test_audio_quality_validation(self):
        """Test audio quality validation"""
        with mock_webui_user():
            audio_content = b"fake audio content"
            audio_file = io.BytesIO(audio_content)
            
            with patch('open_webui.routers.audio.validate_audio_quality') as mock_validate:
                mock_validate.return_value = {
                    "quality_score": 8.5,
                    "recommendations": ["increase_bitrate"],
                    "is_acceptable": True
                }
                
                response = self.fast_api_client.post(
                    self.create_url("/validate-quality"),
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )
                
        assert response.status_code == 200
        data = response.json()
        assert data["quality_score"] == 8.5
        assert data["is_acceptable"] is True

    def test_audio_metadata_extraction(self):
        """Test audio metadata extraction"""
        with mock_webui_user():
            audio_content = b"fake audio content"
            audio_file = io.BytesIO(audio_content)
            
            with patch('open_webui.routers.audio.extract_audio_metadata') as mock_extract:
                mock_extract.return_value = {
                    "duration": 120.5,
                    "bitrate": 128000,
                    "sample_rate": 44100,
                    "channels": 2,
                    "format": "wav"
                }
                
                response = self.fast_api_client.post(
                    self.create_url("/metadata"),
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )
                
        assert response.status_code == 200
        data = response.json()
        assert data["duration"] == 120.5
        assert data["channels"] == 2

    def test_audio_noise_reduction(self):
        """Test audio noise reduction"""
        with mock_webui_user():
            audio_content = b"fake audio content"
            audio_file = io.BytesIO(audio_content)
            
            with patch('open_webui.routers.audio.reduce_noise') as mock_reduce:
                mock_reduce.return_value = b"cleaned audio"
                
                response = self.fast_api_client.post(
                    self.create_url("/reduce-noise"),
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"reduction_strength": "medium"}
                )
                
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_audio_error_handling(self):
        """Test audio processing error handling"""
        with mock_webui_user():
            # Test with corrupted file
            corrupted_content = b"corrupted audio data"
            corrupted_file = io.BytesIO(corrupted_content)
            
            response = self.fast_api_client.post(
                self.create_url("/speech-to-text"),
                files={"file": ("corrupted.wav", corrupted_file, "audio/wav")}
            )
                
        assert response.status_code == 400
        assert "error" in response.json()

    def test_audio_concurrent_processing(self):
        """Test concurrent audio processing"""
        with mock_webui_user():
            with patch('open_webui.routers.audio.process_audio_concurrent') as mock_concurrent:
                mock_concurrent.return_value = {
                    "job_id": "job-123",
                    "status": "processing",
                    "estimated_completion": "2 minutes"
                }
                
                response = self.fast_api_client.post(
                    self.create_url("/process-async"),
                    json={
                        "files": ["file1.wav", "file2.wav"],
                        "operation": "transcribe"
                    }
                )
                
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == "processing"