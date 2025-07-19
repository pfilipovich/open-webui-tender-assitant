from unittest.mock import Mock, patch

from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user


class TestKnowledge(AbstractPostgresTest):
    BASE_PATH = "/api/v1/knowledge"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.knowledge import Knowledges
        from open_webui.models.files import Files

        cls.knowledges = Knowledges
        cls.files = Files

    def setup_method(self):
        super().setup_method()
        # Create test knowledge base
        self.knowledge_base = self.knowledges.insert_new_knowledge(
            user_id="1",
            form={
                "name": "Test Knowledge Base",
                "description": "A test knowledge base",
                "data": {"file_ids": []}
            }
        )

    def test_get_knowledge_bases_admin(self):
        """Test getting knowledge bases as admin"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        # Find our test knowledge base
        test_kb = next((kb for kb in data if kb["name"] == "Test Knowledge Base"), None)
        assert test_kb is not None
        assert test_kb["description"] == "A test knowledge base"
        assert test_kb["files"] == []

    def test_get_knowledge_bases_user_with_access(self):
        """Test getting knowledge bases as user with read access"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_knowledge_bases_user_without_access(self):
        """Test getting knowledge bases as user without access"""
        with mock_webui_user(id="2"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        # Should only get knowledge bases user has access to
        assert isinstance(data, list)

    def test_get_knowledge_list_admin(self):
        """Test getting knowledge list as admin"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/list"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_knowledge_list_user_with_write_access(self):
        """Test getting knowledge list as user with write access"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/list"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_knowledge_base(self):
        """Test creating a new knowledge base"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "name": "New Knowledge Base",
                    "description": "A new test knowledge base",
                    "data": {"file_ids": []}
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Knowledge Base"
        assert data["description"] == "A new test knowledge base"
        assert data["user_id"] == "1"

    def test_create_knowledge_base_duplicate_name(self):
        """Test creating knowledge base with duplicate name"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "name": "Test Knowledge Base",  # Same name as existing
                    "description": "Duplicate name test",
                    "data": {"file_ids": []}
                }
            )
        
        assert response.status_code == 400

    def test_get_knowledge_base_by_id(self):
        """Test getting specific knowledge base by ID"""
        kb_id = self.knowledge_base.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url(f"/{kb_id}"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == kb_id
        assert data["name"] == "Test Knowledge Base"

    def test_get_knowledge_base_not_found(self):
        """Test getting non-existent knowledge base"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/nonexistent-id"))
        
        assert response.status_code == 404

    def test_update_knowledge_base(self):
        """Test updating knowledge base"""
        kb_id = self.knowledge_base.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{kb_id}/update"),
                json={
                    "name": "Updated Knowledge Base",
                    "description": "Updated description",
                    "data": {"file_ids": []}
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Knowledge Base"
        assert data["description"] == "Updated description"

    def test_update_knowledge_base_not_found(self):
        """Test updating non-existent knowledge base"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/nonexistent-id/update"),
                json={
                    "name": "Updated Knowledge Base",
                    "description": "Updated description",
                    "data": {"file_ids": []}
                }
            )
        
        assert response.status_code == 404

    def test_delete_knowledge_base(self):
        """Test deleting knowledge base"""
        kb_id = self.knowledge_base.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url(f"/{kb_id}"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_knowledge_base_not_found(self):
        """Test deleting non-existent knowledge base"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url("/nonexistent-id"))
        
        assert response.status_code == 404

    def test_knowledge_base_with_files(self):
        """Test knowledge base with associated files"""
        # Create a mock file
        with patch('open_webui.models.files.Files.get_file_metadatas_by_ids') as mock_get_files:
            mock_file = Mock()
            mock_file.id = "test-file-id"
            mock_file.filename = "test.txt"
            mock_get_files.return_value = [mock_file]
            
            # Update knowledge base with file
            kb_id = self.knowledge_base.id
            with mock_webui_user(id="1"):
                response = self.fast_api_client.post(
                    self.create_url(f"/{kb_id}/update"),
                    json={
                        "name": "KB with Files",
                        "description": "Knowledge base with files",
                        "data": {"file_ids": ["test-file-id"]}
                    }
                )
                
                assert response.status_code == 200
                
                # Get knowledge base to verify files are included
                response = self.fast_api_client.get(self.create_url("/"))
                assert response.status_code == 200
                
                kb_data = response.json()
                test_kb = next((kb for kb in kb_data if kb["name"] == "KB with Files"), None)
                assert test_kb is not None
                assert len(test_kb["files"]) == 1
                assert test_kb["files"][0]["id"] == "test-file-id"

    def test_knowledge_base_with_missing_files(self):
        """Test knowledge base with missing files gets cleaned up"""
        # Create knowledge base with non-existent file
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "name": "KB with Missing Files",
                    "description": "Knowledge base with missing files",
                    "data": {"file_ids": ["nonexistent-file-id"]}
                }
            )
            
            assert response.status_code == 200
            
            # Get knowledge bases - should clean up missing files
            response = self.fast_api_client.get(self.create_url("/"))
            assert response.status_code == 200
            
            kb_data = response.json()
            test_kb = next((kb for kb in kb_data if kb["name"] == "KB with Missing Files"), None)
            assert test_kb is not None
            # Files should be empty after cleanup
            assert test_kb["files"] == []

    def test_access_control_unauthorized(self):
        """Test access control for unauthorized user"""
        with mock_webui_user(id="999"):  # User without access
            response = self.fast_api_client.get(self.create_url(f"/{self.knowledge_base.id}"))
        
        # Should return 403 or 404 depending on implementation
        assert response.status_code in [403, 404]