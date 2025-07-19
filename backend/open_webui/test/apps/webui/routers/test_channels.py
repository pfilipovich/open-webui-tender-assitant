import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from open_webui.test.util.abstract_integration_test import AbstractPostgresTest
from open_webui.test.util.mock_user import mock_webui_user


class TestChannels(AbstractPostgresTest):
    BASE_PATH = "/api/v1/channels"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.channels import Channels
        from open_webui.models.messages import Messages

        cls.channels = Channels
        cls.messages = Messages

    def setup_method(self):
        super().setup_method()
        # Create test channel
        self.test_channel = self.channels.insert_new_channel(
            None,
            {
                "name": "Test Channel",
                "description": "A test channel for unit testing",
                "access_control": {"read": {"user_ids": ["1"]}, "write": {"user_ids": ["1"]}}
            },
            "1"
        )

    def test_get_channels_admin(self):
        """Test getting channels as admin user"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        # Find our test channel
        test_channel = next((ch for ch in data if ch["name"] == "Test Channel"), None)
        assert test_channel is not None
        assert test_channel["description"] == "A test channel for unit testing"

    def test_get_channels_user_with_access(self):
        """Test getting channels as user with access"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_channels_user_without_access(self):
        """Test getting channels as user without access"""
        with mock_webui_user(id="2"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        # Should only get channels user has access to
        assert isinstance(data, list)

    def test_create_new_channel_admin(self):
        """Test creating new channel as admin"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "name": "New Channel",
                    "description": "A new test channel",
                    "access_control": {
                        "read": {"user_ids": ["1", "2"]},
                        "write": {"user_ids": ["1"]}
                    }
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Channel"
        assert data["description"] == "A new test channel"
        assert data["user_id"] == "1"

    def test_create_new_channel_non_admin(self):
        """Test creating new channel as non-admin user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "name": "Unauthorized Channel",
                    "description": "Should not be created",
                    "access_control": {"read": {"user_ids": ["1"]}}
                }
            )
        
        assert response.status_code == 403

    def test_create_channel_duplicate_name(self):
        """Test creating channel with duplicate name"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "name": "Test Channel",  # Same name as existing
                    "description": "Duplicate channel",
                    "access_control": {"read": {"user_ids": ["1"]}}
                }
            )
        
        assert response.status_code == 400

    def test_get_channel_by_id_success(self):
        """Test getting channel by ID with proper access"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url(f"/{channel_id}"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == channel_id
        assert data["name"] == "Test Channel"

    def test_get_channel_by_id_not_found(self):
        """Test getting non-existent channel"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/nonexistent-id"))
        
        assert response.status_code == 404

    def test_get_channel_by_id_no_access(self):
        """Test getting channel without access"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="2"):  # User without access
            response = self.fast_api_client.get(self.create_url(f"/{channel_id}"))
        
        assert response.status_code == 403

    def test_get_channel_by_id_admin_access(self):
        """Test admin can access any channel"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url(f"/{channel_id}"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == channel_id

    def test_update_channel_by_id_success(self):
        """Test updating channel by ID"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url(f"/{channel_id}/update"),
                json={
                    "name": "Updated Channel",
                    "description": "Updated description",
                    "access_control": {"read": {"user_ids": ["1", "2"]}}
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Channel"
        assert data["description"] == "Updated description"

    def test_update_channel_by_id_not_found(self):
        """Test updating non-existent channel"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/nonexistent-id/update"),
                json={
                    "name": "Updated Channel",
                    "description": "Updated description",
                    "access_control": {"read": {"user_ids": ["1"]}}
                }
            )
        
        assert response.status_code == 404

    def test_update_channel_non_admin(self):
        """Test updating channel as non-admin user"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{channel_id}/update"),
                json={
                    "name": "Unauthorized Update",
                    "description": "Should not work",
                    "access_control": {"read": {"user_ids": ["1"]}}
                }
            )
        
        assert response.status_code == 403

    def test_delete_channel_by_id_success(self):
        """Test deleting channel by ID"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.delete(self.create_url(f"/{channel_id}"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_channel_by_id_not_found(self):
        """Test deleting non-existent channel"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.delete(self.create_url("/nonexistent-id"))
        
        assert response.status_code == 404

    def test_delete_channel_non_admin(self):
        """Test deleting channel as non-admin user"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url(f"/{channel_id}"))
        
        assert response.status_code == 403

    def test_get_channel_messages(self):
        """Test getting messages from a channel"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url(f"/{channel_id}/messages"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_post_message_to_channel(self):
        """Test posting message to channel"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{channel_id}/messages"),
                json={
                    "content": "Hello, this is a test message",
                    "type": "text"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello, this is a test message"
        assert data["user_id"] == "1"

    def test_post_message_without_write_access(self):
        """Test posting message without write access"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="2"):  # User without write access
            response = self.fast_api_client.post(
                self.create_url(f"/{channel_id}/messages"),
                json={
                    "content": "Unauthorized message",
                    "type": "text"
                }
            )
        
        assert response.status_code == 403

    def test_get_channel_users(self):
        """Test getting users with access to channel"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url(f"/{channel_id}/users"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_add_user_to_channel(self):
        """Test adding user to channel"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url(f"/{channel_id}/users"),
                json={
                    "user_id": "2",
                    "access_type": "read"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_remove_user_from_channel(self):
        """Test removing user from channel"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.delete(
                self.create_url(f"/{channel_id}/users/1")
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_channel_access_control_validation(self):
        """Test channel access control validation"""
        with mock_webui_user(role="admin"):
            # Test invalid access control structure
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "name": "Invalid Access Channel",
                    "description": "Invalid access control",
                    "access_control": {"invalid": "structure"}
                }
            )
        
        assert response.status_code == 400

    def test_channel_search(self):
        """Test searching channels"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(
                self.create_url("/search"),
                params={"q": "Test"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_channel_export_admin(self):
        """Test exporting channel data as admin"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url(f"/{channel_id}/export"))
        
        assert response.status_code == 200
        data = response.json()
        assert "channel" in data
        assert "messages" in data

    def test_channel_export_non_admin(self):
        """Test exporting channel data as non-admin"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url(f"/{channel_id}/export"))
        
        assert response.status_code == 403

    def test_channel_archive(self):
        """Test archiving channel"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(self.create_url(f"/{channel_id}/archive"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["archived"] is True

    def test_channel_unarchive(self):
        """Test unarchiving channel"""
        channel_id = self.test_channel.id
        
        # First archive the channel
        with mock_webui_user(role="admin"):
            self.fast_api_client.post(self.create_url(f"/{channel_id}/archive"))
            
            # Then unarchive
            response = self.fast_api_client.post(self.create_url(f"/{channel_id}/unarchive"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["archived"] is False

    def test_channel_webhook_integration(self):
        """Test channel webhook integration"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(role="admin"):
            with patch('open_webui.utils.webhook.post_webhook') as mock_webhook:
                mock_webhook.return_value = True
                
                response = self.fast_api_client.post(
                    self.create_url(f"/{channel_id}/webhook"),
                    json={
                        "url": "https://example.com/webhook",
                        "events": ["message_posted", "user_joined"]
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["webhook_configured"] is True

    def test_channel_socket_integration(self):
        """Test channel socket integration"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            with patch('open_webui.socket.main.sio') as mock_sio:
                mock_sio.emit = Mock()
                
                response = self.fast_api_client.post(
                    self.create_url(f"/{channel_id}/messages"),
                    json={
                        "content": "Socket test message",
                        "type": "text"
                    }
                )
        
        assert response.status_code == 200
        # Verify socket emission was called
        # mock_sio.emit.assert_called_once()

    def test_channel_pagination(self):
        """Test channel message pagination"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(
                self.create_url(f"/{channel_id}/messages"),
                params={"page": 1, "limit": 10}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    def test_channel_message_formatting(self):
        """Test channel message formatting"""
        channel_id = self.test_channel.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/{channel_id}/messages"),
                json={
                    "content": "**Bold text** and *italic text*",
                    "type": "markdown"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "**Bold text** and *italic text*"
        assert data["type"] == "markdown"