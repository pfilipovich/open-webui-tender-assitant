import io
import json
from unittest.mock import Mock, patch

from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user


class TestFiles(AbstractPostgresTest):
    BASE_PATH = "/api/v1/files"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.files import Files
        from open_webui.models.knowledge import Knowledges

        cls.files = Files
        cls.knowledges = Knowledges

    def test_upload_file_success(self):
        """Test successful file upload"""
        with mock_webui_user():
            with patch('open_webui.storage.provider.Storage.upload_file') as mock_upload:
                mock_upload.return_value = (b"test content", "/path/to/file.txt")
                
                response = self.fast_api_client.post(
                    self.create_url("/"),
                    files={
                        "file": ("test.txt", io.BytesIO(b"test content"), "text/plain")
                    },
                    data={"metadata": json.dumps({"description": "test file"})}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["meta"]["content_type"] == "text/plain"
        assert data["meta"]["size"] == 12

    def test_upload_file_invalid_metadata(self):
        """Test file upload with invalid metadata"""
        with mock_webui_user():
            response = self.fast_api_client.post(
                self.create_url("/"),
                files={
                    "file": ("test.txt", io.BytesIO(b"test content"), "text/plain")
                },
                data={"metadata": "invalid json"}
            )
        
        assert response.status_code == 400

    def test_upload_file_forbidden_extension(self):
        """Test file upload with forbidden file extension"""
        with mock_webui_user():
            with patch('fastapi.Request') as mock_request:
                mock_request.app.state.config.ALLOWED_FILE_EXTENSIONS = ["txt", "pdf"]
                
                response = self.fast_api_client.post(
                    self.create_url("/"),
                    files={
                        "file": ("test.exe", io.BytesIO(b"test content"), "application/octet-stream")
                    }
                )
        
        assert response.status_code == 400

    def test_get_files_list(self):
        """Test getting list of files"""
        with mock_webui_user():
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_file_by_id_success(self):
        """Test getting a specific file by ID"""
        # First create a file
        with mock_webui_user() as user:
            with patch('open_webui.storage.provider.Storage.upload_file') as mock_upload:
                mock_upload.return_value = (b"test content", "/path/to/file.txt")
                
                upload_response = self.fast_api_client.post(
                    self.create_url("/"),
                    files={
                        "file": ("test.txt", io.BytesIO(b"test content"), "text/plain")
                    }
                )
                
                file_id = upload_response.json()["id"]
                
                # Now get the file
                response = self.fast_api_client.get(self.create_url(f"/{file_id}"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == file_id
        assert data["filename"] == "test.txt"

    def test_get_file_by_id_not_found(self):
        """Test getting a non-existent file"""
        with mock_webui_user():
            response = self.fast_api_client.get(self.create_url("/nonexistent-id"))
        
        assert response.status_code == 404

    def test_delete_file_success(self):
        """Test successful file deletion"""
        with mock_webui_user():
            with patch('open_webui.storage.provider.Storage.upload_file') as mock_upload:
                with patch('open_webui.storage.provider.Storage.delete_file') as mock_delete:
                    mock_upload.return_value = (b"test content", "/path/to/file.txt")
                    
                    # Create file
                    upload_response = self.fast_api_client.post(
                        self.create_url("/"),
                        files={
                            "file": ("test.txt", io.BytesIO(b"test content"), "text/plain")
                        }
                    )
                    
                    file_id = upload_response.json()["id"]
                    
                    # Delete file
                    response = self.fast_api_client.delete(self.create_url(f"/{file_id}"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_file_not_found(self):
        """Test deleting a non-existent file"""
        with mock_webui_user():
            response = self.fast_api_client.delete(self.create_url("/nonexistent-id"))
        
        assert response.status_code == 404

    def test_has_access_to_file_with_knowledge_base(self):
        """Test file access control through knowledge base"""
        with mock_webui_user() as user:
            with patch('open_webui.storage.provider.Storage.upload_file') as mock_upload:
                mock_upload.return_value = (b"test content", "/path/to/file.txt")
                
                # Create file with knowledge base metadata
                response = self.fast_api_client.post(
                    self.create_url("/"),
                    files={
                        "file": ("test.txt", io.BytesIO(b"test content"), "text/plain")
                    },
                    data={"metadata": json.dumps({"collection_name": "test-kb"})}
                )
                
                file_id = response.json()["id"]
                
                # Test access check
                response = self.fast_api_client.get(self.create_url(f"/{file_id}"))
        
        assert response.status_code == 200

    def test_file_content_download(self):
        """Test downloading file content"""
        with mock_webui_user():
            with patch('open_webui.storage.provider.Storage.upload_file') as mock_upload:
                with patch('open_webui.storage.provider.Storage.get_file') as mock_get:
                    mock_upload.return_value = (b"test content", "/path/to/file.txt")
                    mock_get.return_value = "/path/to/file.txt"
                    
                    # Create file
                    upload_response = self.fast_api_client.post(
                        self.create_url("/"),
                        files={
                            "file": ("test.txt", io.BytesIO(b"test content"), "text/plain")
                        }
                    )
                    
                    file_id = upload_response.json()["id"]
                    
                    # Download file content
                    with patch('pathlib.Path.exists', return_value=True):
                        with patch('pathlib.Path.open', return_value=io.BytesIO(b"test content")):
                            response = self.fast_api_client.get(self.create_url(f"/{file_id}/content"))
        
        assert response.status_code == 200