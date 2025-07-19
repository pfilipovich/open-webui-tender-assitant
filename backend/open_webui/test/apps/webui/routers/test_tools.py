import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user


class TestTools(AbstractPostgresTest):
    BASE_PATH = "/api/v1/tools"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.tools import Tools

        cls.tools = Tools

    def setup_method(self):
        super().setup_method()
        # Create test tool
        self.test_tool = self.tools.insert_new_tool(
            user_id="1",
            form={
                "id": "test_tool",
                "name": "Test Tool",
                "content": "def test_function():\n    return 'Hello World'",
                "meta": {"description": "A test tool"},
                "access_control": {"read": {"group_ids": [], "user_ids": []}},
                "valves": {},
                "is_active": True,
                "is_global": False
            }
        )

    @patch('open_webui.utils.tools.get_tool_servers_data')
    def test_get_tools_admin(self, mock_get_servers):
        """Test getting tools as admin user"""
        mock_get_servers.return_value = []
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        # Find our test tool
        test_tool = next((tool for tool in data if tool["name"] == "Test Tool"), None)
        assert test_tool is not None
        assert test_tool["id"] == "test_tool"

    @patch('open_webui.utils.tools.get_tool_servers_data')
    def test_get_tools_user_with_access(self, mock_get_servers):
        """Test getting tools as user with access"""
        mock_get_servers.return_value = []
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @patch('open_webui.utils.tools.get_tool_servers_data')
    def test_get_tools_user_without_access(self, mock_get_servers):
        """Test getting tools as user without access"""
        mock_get_servers.return_value = []
        
        with mock_webui_user(id="2"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        # Should only get tools user has access to
        assert isinstance(data, list)

    @patch('open_webui.utils.tools.get_tool_servers_data')
    def test_get_tools_with_tool_servers(self, mock_get_servers):
        """Test getting tools with tool servers"""
        mock_get_servers.return_value = [
            {
                "idx": 0,
                "openapi": {
                    "info": {
                        "title": "Test Tool Server",
                        "description": "A test tool server"
                    }
                }
            }
        ]
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/"))
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include tool server
        server_tool = next((tool for tool in data if tool["id"] == "server:0"), None)
        assert server_tool is not None
        assert server_tool["name"] == "Test Tool Server"

    def test_get_tool_list_admin(self):
        """Test getting tool list as admin"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/list"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_tool_list_user_with_write_access(self):
        """Test getting tool list as user with write access"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/list"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_new_tool(self):
        """Test creating a new tool"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "id": "new_tool",
                    "name": "New Tool",
                    "content": "def new_function():\n    return 'New Tool'",
                    "meta": {"description": "A new test tool"},
                    "access_control": {"read": {"group_ids": [], "user_ids": []}},
                    "valves": {},
                    "is_active": True,
                    "is_global": False
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Tool"
        assert data["id"] == "new_tool"

    def test_create_tool_duplicate_id(self):
        """Test creating tool with duplicate ID"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "id": "test_tool",  # Same ID as existing tool
                    "name": "Duplicate Tool",
                    "content": "def duplicate_function():\n    return 'Duplicate'",
                    "meta": {"description": "A duplicate test tool"},
                    "access_control": {"read": {"group_ids": [], "user_ids": []}},
                    "valves": {},
                    "is_active": True,
                    "is_global": False
                }
            )
        
        assert response.status_code == 400

    def test_get_tool_by_id(self):
        """Test getting specific tool by ID"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/id/test_tool"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_tool"
        assert data["name"] == "Test Tool"

    def test_get_tool_by_id_not_found(self):
        """Test getting non-existent tool"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/id/nonexistent"))
        
        assert response.status_code == 404

    def test_update_tool_by_id(self):
        """Test updating tool by ID"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/id/test_tool/update"),
                json={
                    "id": "test_tool",
                    "name": "Updated Test Tool",
                    "content": "def updated_function():\n    return 'Updated'",
                    "meta": {"description": "An updated test tool"},
                    "access_control": {"read": {"group_ids": [], "user_ids": []}},
                    "valves": {},
                    "is_active": True,
                    "is_global": False
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Test Tool"

    def test_update_tool_not_found(self):
        """Test updating non-existent tool"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/id/nonexistent/update"),
                json={
                    "id": "nonexistent",
                    "name": "Updated Tool",
                    "content": "def updated_function():\n    return 'Updated'",
                    "meta": {"description": "Updated tool"},
                    "access_control": {"read": {"group_ids": [], "user_ids": []}},
                    "valves": {},
                    "is_active": True,
                    "is_global": False
                }
            )
        
        assert response.status_code == 404

    def test_delete_tool_by_id(self):
        """Test deleting tool by ID"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url("/id/test_tool"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_tool_not_found(self):
        """Test deleting non-existent tool"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url("/id/nonexistent"))
        
        assert response.status_code == 404

    def test_export_tools(self):
        """Test exporting tools"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/export"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_export_tools_non_admin(self):
        """Test exporting tools as non-admin user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/export"))
        
        assert response.status_code == 403

    @patch('aiohttp.ClientSession.get')
    def test_load_tool_from_url_success(self, mock_get):
        """Test loading tool from URL successfully"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="def test_function():\n    return 'Hello'")
        mock_get.return_value.__aenter__.return_value = mock_response
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/load/url"),
                json={"url": "https://example.com/tool.py"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "tool"
        assert "test_function" in data["content"]

    @patch('aiohttp.ClientSession.get')
    def test_load_tool_from_url_failure(self, mock_get):
        """Test loading tool from URL with failure"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/load/url"),
                json={"url": "https://example.com/nonexistent.py"}
            )
        
        assert response.status_code == 404

    def test_load_tool_from_url_non_admin(self):
        """Test loading tool from URL as non-admin user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/load/url"),
                json={"url": "https://example.com/tool.py"}
            )
        
        assert response.status_code == 403

    def test_github_url_conversion(self):
        """Test GitHub URL to raw URL conversion"""
        from open_webui.routers.tools import github_url_to_raw_url
        
        # Test tree URL
        tree_url = "https://github.com/user/repo/tree/main/path/to/tool"
        expected = "https://raw.githubusercontent.com/user/repo/refs/heads/main/path/to/tool/main.py"
        assert github_url_to_raw_url(tree_url) == expected
        
        # Test blob URL
        blob_url = "https://github.com/user/repo/blob/main/path/to/tool.py"
        expected = "https://raw.githubusercontent.com/user/repo/refs/heads/main/path/to/tool.py"
        assert github_url_to_raw_url(blob_url) == expected
        
        # Test regular URL (no conversion)
        regular_url = "https://raw.githubusercontent.com/user/repo/main/tool.py"
        assert github_url_to_raw_url(regular_url) == regular_url

    def test_get_tool_specs(self):
        """Test getting tool specifications"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/id/test_tool/specs"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_tool_specs_not_found(self):
        """Test getting specs for non-existent tool"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/id/nonexistent/specs"))
        
        assert response.status_code == 404

    def test_tool_access_control(self):
        """Test tool access control"""
        # Create tool with restricted access
        restricted_tool = self.tools.insert_new_tool(
            user_id="1",
            form={
                "id": "restricted_tool",
                "name": "Restricted Tool",
                "content": "def restricted_function():\n    return 'Restricted'",
                "meta": {"description": "A restricted tool"},
                "access_control": {"read": {"group_ids": [], "user_ids": ["1"]}},
                "valves": {},
                "is_active": True,
                "is_global": False
            }
        )
        
        # User without access should not see the tool
        with mock_webui_user(id="2"):
            response = self.fast_api_client.get(self.create_url("/id/restricted_tool"))
        
        assert response.status_code == 403

    def test_tool_validation_error(self):
        """Test tool creation with validation errors"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/create"),
                json={
                    "id": "",  # Empty ID should fail validation
                    "name": "Invalid Tool",
                    "content": "def invalid_function():\n    return 'Invalid'",
                    "meta": {"description": "Invalid tool"},
                    "access_control": {"read": {"group_ids": [], "user_ids": []}},
                    "valves": {},
                    "is_active": True,
                    "is_global": False
                }
            )
        
        assert response.status_code == 400