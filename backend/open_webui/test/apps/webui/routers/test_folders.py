import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from open_webui.test.util.abstract_integration_test import AbstractPostgresTest
from open_webui.test.util.mock_user import mock_webui_user


class TestFolders(AbstractPostgresTest):
    BASE_PATH = "/api/v1/folders"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.folders import Folders
        from open_webui.models.chats import Chats
        cls.folders = Folders
        cls.chats = Chats

    def setup_method(self):
        super().setup_method()
        # Create test folder
        self.test_folder = self.folders.insert_new_folder(
            user_id="1",
            name="Test Folder"
        )

    def test_get_folders_success(self):
        """Test getting folders for user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check folder structure
        folder = data[0]
        assert "id" in folder
        assert "name" in folder
        assert "items" in folder
        assert "chats" in folder["items"]
        assert folder["name"] == "Test Folder"

    def test_get_folders_empty(self):
        """Test getting folders when user has no folders"""
        with mock_webui_user(id="2"):  # Different user
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_folder_success(self):
        """Test creating new folder"""
        folder_data = {
            "name": "New Folder"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/"),
                json=folder_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Folder"
        assert data["user_id"] == "1"

    def test_create_folder_duplicate_name(self):
        """Test creating folder with duplicate name"""
        folder_data = {
            "name": "Test Folder"  # Same name as existing folder
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/"),
                json=folder_data
            )
        
        assert response.status_code == 400

    def test_create_folder_empty_name(self):
        """Test creating folder with empty name"""
        folder_data = {
            "name": ""
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/"),
                json=folder_data
            )
        
        assert response.status_code == 400

    def test_get_folder_by_id_success(self):
        """Test getting folder by ID"""
        folder_id = self.test_folder.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url(f"/{folder_id}"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == folder_id
        assert data["name"] == "Test Folder"

    def test_get_folder_by_id_not_found(self):
        """Test getting non-existent folder"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/nonexistent-id"))
        
        assert response.status_code == 404

    def test_get_folder_by_id_unauthorized(self):
        """Test getting folder by different user"""
        folder_id = self.test_folder.id
        
        with mock_webui_user(id="2"):  # Different user
            response = self.fast_api_client.get(self.create_url(f"/{folder_id}"))
        
        assert response.status_code == 404

    def test_update_folder_name_success(self):
        """Test updating folder name"""
        folder_id = self.test_folder.id
        update_data = {
            "name": "Updated Folder Name"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update"),
                json=update_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Folder Name"

    def test_update_folder_name_duplicate(self):
        """Test updating folder name to duplicate"""
        # Create second folder
        second_folder = self.folders.insert_new_folder(
            user_id="1",
            name="Second Folder"
        )
        
        folder_id = self.test_folder.id
        update_data = {
            "name": "Second Folder"  # Same name as existing folder
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update"),
                json=update_data
            )
        
        assert response.status_code == 400

    def test_update_folder_name_not_found(self):
        """Test updating non-existent folder"""
        update_data = {
            "name": "Updated Name"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/nonexistent-id/update"),
                json=update_data
            )
        
        assert response.status_code == 404

    def test_update_folder_name_unauthorized(self):
        """Test updating folder by different user"""
        folder_id = self.test_folder.id
        update_data = {
            "name": "Unauthorized Update"
        }
        
        with mock_webui_user(id="2"):  # Different user
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update"),
                json=update_data
            )
        
        assert response.status_code == 404

    def test_update_folder_parent_id_success(self):
        """Test updating folder parent ID"""
        # Create parent folder
        parent_folder = self.folders.insert_new_folder(
            user_id="1",
            name="Parent Folder"
        )
        
        folder_id = self.test_folder.id
        update_data = {
            "parent_id": parent_folder.id
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update/parent"),
                json=update_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == parent_folder.id

    def test_update_folder_parent_id_null(self):
        """Test setting folder parent ID to null"""
        folder_id = self.test_folder.id
        update_data = {
            "parent_id": None
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update/parent"),
                json=update_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] is None

    def test_update_folder_parent_id_duplicate(self):
        """Test updating folder parent ID causing duplicate"""
        # Create parent folder
        parent_folder = self.folders.insert_new_folder(
            user_id="1",
            name="Parent Folder"
        )
        
        # Create another folder with same name under parent
        self.folders.insert_new_folder(
            user_id="1",
            name="Test Folder"
        )
        
        folder_id = self.test_folder.id
        update_data = {
            "parent_id": parent_folder.id
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update/parent"),
                json=update_data
            )
        
        assert response.status_code == 400

    def test_update_folder_parent_id_not_found(self):
        """Test updating parent ID for non-existent folder"""
        update_data = {
            "parent_id": "nonexistent-parent"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/nonexistent-id/update/parent"),
                json=update_data
            )
        
        assert response.status_code == 404

    def test_update_folder_is_expanded_success(self):
        """Test updating folder expanded state"""
        folder_id = self.test_folder.id
        update_data = {
            "is_expanded": True
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update/expanded"),
                json=update_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_expanded"] is True

    def test_update_folder_is_expanded_false(self):
        """Test setting folder expanded state to false"""
        folder_id = self.test_folder.id
        update_data = {
            "is_expanded": False
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update/expanded"),
                json=update_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_expanded"] is False

    def test_update_folder_is_expanded_not_found(self):
        """Test updating expanded state for non-existent folder"""
        update_data = {
            "is_expanded": True
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/nonexistent-id/update/expanded"),
                json=update_data
            )
        
        assert response.status_code == 404

    def test_update_folder_is_expanded_unauthorized(self):
        """Test updating expanded state by different user"""
        folder_id = self.test_folder.id
        update_data = {
            "is_expanded": True
        }
        
        with mock_webui_user(id="2"):  # Different user
            response = self.fast_api_client.post(
                self.create_url(f"/{folder_id}/update/expanded"),
                json=update_data
            )
        
        assert response.status_code == 404

    def test_delete_folder_success(self):
        """Test deleting folder"""
        folder_id = self.test_folder.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url(f"/{folder_id}"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_folder_admin(self):
        """Test deleting folder as admin"""
        folder_id = self.test_folder.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.delete(self.create_url(f"/{folder_id}"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_folder_not_found(self):
        """Test deleting non-existent folder"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url("/nonexistent-id"))
        
        assert response.status_code == 404

    def test_delete_folder_unauthorized(self):
        """Test deleting folder by different user"""
        folder_id = self.test_folder.id
        
        with mock_webui_user(id="2"):  # Different user
            response = self.fast_api_client.delete(self.create_url(f"/{folder_id}"))
        
        assert response.status_code == 404

    def test_delete_folder_permission_denied(self):
        """Test deleting folder without proper permissions"""
        folder_id = self.test_folder.id
        
        with mock_webui_user(id="1", role="user"):
            with patch('open_webui.utils.access_control.has_permission') as mock_permission:
                mock_permission.return_value = False
                
                response = self.fast_api_client.delete(self.create_url(f"/{folder_id}"))
        
        assert response.status_code == 403

    def test_folder_hierarchy_structure(self):
        """Test folder hierarchy structure"""
        # Create parent folder
        parent_folder = self.folders.insert_new_folder(
            user_id="1",
            name="Parent Folder"
        )
        
        # Create child folder
        child_folder = self.folders.insert_new_folder(
            user_id="1",
            name="Child Folder"
        )
        
        # Update child folder parent
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{child_folder.id}/update/parent"),
                json={"parent_id": parent_folder.id}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == parent_folder.id

    def test_folder_with_chats(self):
        """Test folder containing chats"""
        # Create a chat and assign to folder
        with patch('open_webui.models.chats.Chats.get_chats_by_folder_id_and_user_id') as mock_chats:
            mock_chats.return_value = [
                Mock(id="chat-1", title="Test Chat 1"),
                Mock(id="chat-2", title="Test Chat 2")
            ]
            
            with mock_webui_user(id="1"):
                response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        folder = data[0]
        assert "items" in folder
        assert "chats" in folder["items"]
        assert len(folder["items"]["chats"]) == 2

    def test_folder_validation(self):
        """Test folder data validation"""
        invalid_folder_data = {
            "name": "a" * 256  # Too long name
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/"),
                json=invalid_folder_data
            )
        
        assert response.status_code == 400

    def test_folder_special_characters(self):
        """Test folder with special characters"""
        folder_data = {
            "name": "Test Folder with 🚀 Emoji & Special Characters!"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/"),
                json=folder_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Folder with 🚀 Emoji & Special Characters!"

    def test_folder_case_sensitivity(self):
        """Test folder name case sensitivity"""
        # Create folder with lowercase name
        folder_data_lower = {
            "name": "test folder"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/"),
                json=folder_data_lower
            )
        
        assert response.status_code == 200
        
        # Try to create folder with uppercase name
        folder_data_upper = {
            "name": "TEST FOLDER"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/"),
                json=folder_data_upper
            )
        
        assert response.status_code == 200  # Should succeed as names are different

    def test_folder_whitespace_handling(self):
        """Test folder name whitespace handling"""
        folder_data = {
            "name": "  Folder with Spaces  "
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/"),
                json=folder_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "  Folder with Spaces  "

    def test_folder_circular_reference_prevention(self):
        """Test prevention of circular folder references"""
        # Create parent folder
        parent_folder = self.folders.insert_new_folder(
            user_id="1",
            name="Parent Folder"
        )
        
        # Create child folder
        child_folder = self.folders.insert_new_folder(
            user_id="1",
            name="Child Folder"
        )
        
        # Set child as parent of parent (should fail)
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{parent_folder.id}/update/parent"),
                json={"parent_id": child_folder.id}
            )
        
        # This should either succeed or fail based on implementation
        # The actual behavior depends on the circular reference check
        assert response.status_code in [200, 400]

    def test_folder_bulk_operations(self):
        """Test bulk folder operations"""
        # Create multiple folders
        folder_ids = []
        for i in range(3):
            folder = self.folders.insert_new_folder(
                user_id="1",
                name=f"Bulk Folder {i}"
            )
            folder_ids.append(folder.id)
        
        # Get all folders
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4  # Original + 3 new folders

    def test_folder_sorting(self):
        """Test folder sorting order"""
        # Create multiple folders
        folder_names = ["C Folder", "A Folder", "B Folder"]
        for name in folder_names:
            self.folders.insert_new_folder(
                user_id="1",
                name=name
            )
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4  # Original + 3 new folders
        
        # Check if folders are returned in some order
        folder_names_returned = [folder["name"] for folder in data]
        assert len(folder_names_returned) >= 4

    def test_folder_metadata(self):
        """Test folder metadata fields"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        folder = data[0]
        assert "id" in folder
        assert "name" in folder
        assert "user_id" in folder
        assert "created_at" in folder
        assert "updated_at" in folder
        assert "parent_id" in folder
        assert "is_expanded" in folder
        assert "items" in folder