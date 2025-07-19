import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from open_webui.test.util.abstract_integration_test import AbstractPostgresTest
from open_webui.test.util.mock_user import mock_webui_user


class TestConfigs(AbstractPostgresTest):
    BASE_PATH = "/api/v1/configs"

    def setup_class(cls):
        super().setup_class()

    def test_import_config_admin(self):
        """Test importing configuration as admin"""
        config_data = {
            "ENABLE_SIGNUP": True,
            "DEFAULT_USER_ROLE": "pending",
            "ENABLE_LOGIN_FORM": True,
            "ENABLE_COMMUNITY_SHARING": False
        }
        
        with mock_webui_user(role="admin"):
            with patch('open_webui.routers.configs.save_config') as mock_save:
                with patch('open_webui.routers.configs.get_config') as mock_get:
                    mock_get.return_value = config_data
                    
                    response = self.fast_api_client.post(
                        self.create_url("/import"),
                        json={"config": config_data}
                    )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_SIGNUP"] is True
        assert data["DEFAULT_USER_ROLE"] == "pending"
        mock_save.assert_called_once_with(config_data)

    def test_import_config_non_admin(self):
        """Test importing configuration as non-admin user"""
        config_data = {
            "ENABLE_SIGNUP": True,
            "DEFAULT_USER_ROLE": "pending"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/import"),
                json={"config": config_data}
            )
        
        assert response.status_code == 403

    def test_export_config_admin(self):
        """Test exporting configuration as admin"""
        config_data = {
            "ENABLE_SIGNUP": True,
            "DEFAULT_USER_ROLE": "pending",
            "ENABLE_LOGIN_FORM": True,
            "ENABLE_COMMUNITY_SHARING": False
        }
        
        with mock_webui_user(role="admin"):
            with patch('open_webui.routers.configs.get_config') as mock_get:
                mock_get.return_value = config_data
                
                response = self.fast_api_client.get(self.create_url("/export"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_SIGNUP"] is True
        assert data["DEFAULT_USER_ROLE"] == "pending"

    def test_export_config_non_admin(self):
        """Test exporting configuration as non-admin user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/export"))
        
        assert response.status_code == 403

    def test_get_direct_connections_config(self):
        """Test getting direct connections configuration"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/direct_connections"))
        
        assert response.status_code == 200
        data = response.json()
        assert "ENABLE_DIRECT_CONNECTIONS" in data
        assert isinstance(data["ENABLE_DIRECT_CONNECTIONS"], bool)

    def test_set_direct_connections_config(self):
        """Test setting direct connections configuration"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/direct_connections"),
                json={"ENABLE_DIRECT_CONNECTIONS": True}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_DIRECT_CONNECTIONS"] is True

    def test_set_direct_connections_config_non_admin(self):
        """Test setting direct connections configuration as non-admin"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/direct_connections"),
                json={"ENABLE_DIRECT_CONNECTIONS": True}
            )
        
        assert response.status_code == 403

    def test_get_tool_servers_config(self):
        """Test getting tool servers configuration"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/tool_servers"))
        
        assert response.status_code == 200
        data = response.json()
        assert "TOOL_SERVER_CONNECTIONS" in data
        assert isinstance(data["TOOL_SERVER_CONNECTIONS"], list)

    def test_set_tool_servers_config(self):
        """Test setting tool servers configuration"""
        tool_servers = [
            {
                "url": "http://localhost:8000",
                "path": "/tools",
                "auth_type": "bearer",
                "key": "test-key",
                "config": {"timeout": 30}
            }
        ]
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/tool_servers"),
                json={"TOOL_SERVER_CONNECTIONS": tool_servers}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["TOOL_SERVER_CONNECTIONS"]) == 1
        assert data["TOOL_SERVER_CONNECTIONS"][0]["url"] == "http://localhost:8000"

    def test_set_tool_servers_config_invalid_url(self):
        """Test setting tool servers configuration with invalid URL"""
        tool_servers = [
            {
                "url": "invalid-url",
                "path": "/tools",
                "auth_type": "bearer",
                "key": "test-key"
            }
        ]
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/tool_servers"),
                json={"TOOL_SERVER_CONNECTIONS": tool_servers}
            )
        
        assert response.status_code == 400

    def test_set_tool_servers_config_non_admin(self):
        """Test setting tool servers configuration as non-admin"""
        tool_servers = [
            {
                "url": "http://localhost:8000",
                "path": "/tools",
                "auth_type": "bearer",
                "key": "test-key"
            }
        ]
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/tool_servers"),
                json={"TOOL_SERVER_CONNECTIONS": tool_servers}
            )
        
        assert response.status_code == 403

    def test_get_banner_config(self):
        """Test getting banner configuration"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/banner"))
        
        assert response.status_code == 200
        data = response.json()
        assert "show" in data
        assert "content" in data
        assert "type" in data

    def test_set_banner_config(self):
        """Test setting banner configuration"""
        banner_config = {
            "show": True,
            "content": "Welcome to Open WebUI!",
            "type": "info"
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/banner"),
                json=banner_config
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["show"] is True
        assert data["content"] == "Welcome to Open WebUI!"
        assert data["type"] == "info"

    def test_set_banner_config_invalid_type(self):
        """Test setting banner configuration with invalid type"""
        banner_config = {
            "show": True,
            "content": "Test banner",
            "type": "invalid_type"
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/banner"),
                json=banner_config
            )
        
        assert response.status_code == 400

    def test_get_model_config(self):
        """Test getting model configuration"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/models"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_set_model_config(self):
        """Test setting model configuration"""
        model_config = {
            "DEFAULT_MODELS": ["llama3", "gpt-4"],
            "MODEL_FILTER_ENABLED": True,
            "MODEL_FILTER_LIST": ["gpt-4", "claude-3"]
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/models"),
                json=model_config
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["DEFAULT_MODELS"] == ["llama3", "gpt-4"]
        assert data["MODEL_FILTER_ENABLED"] is True

    def test_get_ui_config(self):
        """Test getting UI configuration"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/ui"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_set_ui_config(self):
        """Test setting UI configuration"""
        ui_config = {
            "ENABLE_COMMUNITY_SHARING": True,
            "ENABLE_MESSAGE_RATING": False,
            "ENABLE_AUTOCOMPLETE": True
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/ui"),
                json=ui_config
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_COMMUNITY_SHARING"] is True
        assert data["ENABLE_MESSAGE_RATING"] is False

    def test_config_validation(self):
        """Test configuration validation"""
        invalid_config = {
            "ENABLE_SIGNUP": "not_boolean",  # Should be boolean
            "DEFAULT_USER_ROLE": "invalid_role"  # Should be valid role
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/import"),
                json={"config": invalid_config}
            )
        
        assert response.status_code == 400

    def test_config_backup_restore(self):
        """Test configuration backup and restore"""
        # First export current config
        with mock_webui_user(role="admin"):
            export_response = self.fast_api_client.get(self.create_url("/export"))
            original_config = export_response.json()
            
            # Modify config
            modified_config = original_config.copy()
            modified_config["ENABLE_SIGNUP"] = not original_config.get("ENABLE_SIGNUP", True)
            
            # Import modified config
            import_response = self.fast_api_client.post(
                self.create_url("/import"),
                json={"config": modified_config}
            )
            
            assert import_response.status_code == 200
            
            # Verify modification
            verify_response = self.fast_api_client.get(self.create_url("/export"))
            assert verify_response.json()["ENABLE_SIGNUP"] != original_config.get("ENABLE_SIGNUP", True)

    def test_config_partial_update(self):
        """Test partial configuration update"""
        partial_config = {
            "ENABLE_SIGNUP": False
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/import"),
                json={"config": partial_config}
            )
        
        assert response.status_code == 200
        # Should only update specified fields, not replace entire config

    def test_config_security_settings(self):
        """Test security-related configuration settings"""
        security_config = {
            "ENABLE_API_KEY": True,
            "ENABLE_OAUTH": False,
            "JWT_EXPIRES_IN": 3600,
            "ENABLE_RATE_LIMITING": True
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/security"),
                json=security_config
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_API_KEY"] is True
        assert data["ENABLE_RATE_LIMITING"] is True

    def test_config_feature_flags(self):
        """Test feature flag configuration"""
        feature_flags = {
            "ENABLE_EXPERIMENTAL_FEATURES": True,
            "ENABLE_BETA_FEATURES": False,
            "FEATURE_WEB_SEARCH": True,
            "FEATURE_IMAGE_GENERATION": False
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/features"),
                json=feature_flags
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_EXPERIMENTAL_FEATURES"] is True
        assert data["FEATURE_WEB_SEARCH"] is True

    def test_config_environment_specific(self):
        """Test environment-specific configuration"""
        env_config = {
            "ENVIRONMENT": "production",
            "DEBUG_MODE": False,
            "LOG_LEVEL": "INFO",
            "ENABLE_TELEMETRY": True
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/environment"),
                json=env_config
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENVIRONMENT"] == "production"
        assert data["DEBUG_MODE"] is False