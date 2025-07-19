import pytest
import jwt
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import pytz

from open_webui.utils import auth
from open_webui.utils.auth import (
    verify_signature,
    verify_password,
    get_password_hash,
    create_token,
    decode_token,
    extract_token_from_auth_header,
    create_api_key,
    get_http_authorization_cred,
    get_current_user,
)


class TestAuthUtils:
    """Test suite for authentication utilities"""

    def test_verify_signature_valid(self):
        """Test signature verification with valid signature"""
        payload = "test_payload"
        # Mock the TRUSTED_SIGNATURE_KEY
        with patch('open_webui.utils.auth.TRUSTED_SIGNATURE_KEY', b'test_key'):
            import hmac
            import hashlib
            import base64
            
            expected_signature = base64.b64encode(
                hmac.new(b'test_key', payload.encode(), hashlib.sha256).digest()
            ).decode()
            
            assert verify_signature(payload, expected_signature) is True

    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature"""
        payload = "test_payload"
        invalid_signature = "invalid_signature"
        
        with patch('open_webui.utils.auth.TRUSTED_SIGNATURE_KEY', b'test_key'):
            assert verify_signature(payload, invalid_signature) is False

    def test_verify_signature_exception(self):
        """Test signature verification handles exceptions"""
        payload = "test_payload"
        signature = "test_signature"
        
        with patch('open_webui.utils.auth.TRUSTED_SIGNATURE_KEY', None):
            assert verify_signature(payload, signature) is False

    def test_verify_password_valid(self):
        """Test password verification with valid password"""
        password = "test_password"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_invalid(self):
        """Test password verification with invalid password"""
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_no_hash(self):
        """Test password verification with no hash"""
        password = "test_password"
        
        assert verify_password(password, None) is None

    def test_get_password_hash(self):
        """Test password hashing"""
        password = "test_password"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith('$2b$')

    def test_create_token_without_expiration(self):
        """Test token creation without expiration"""
        data = {"user_id": "123", "role": "user"}
        
        with patch('open_webui.utils.auth.SESSION_SECRET', 'test_secret'):
            token = create_token(data)
            
            assert token is not None
            assert isinstance(token, str)
            
            # Verify token can be decoded
            decoded = jwt.decode(token, 'test_secret', algorithms=['HS256'])
            assert decoded["user_id"] == "123"
            assert decoded["role"] == "user"

    def test_create_token_with_expiration(self):
        """Test token creation with expiration"""
        data = {"user_id": "123", "role": "user"}
        expires_delta = timedelta(hours=1)
        
        with patch('open_webui.utils.auth.SESSION_SECRET', 'test_secret'):
            token = create_token(data, expires_delta)
            
            assert token is not None
            decoded = jwt.decode(token, 'test_secret', algorithms=['HS256'])
            assert decoded["user_id"] == "123"
            assert "exp" in decoded

    def test_decode_token_valid(self):
        """Test token decoding with valid token"""
        data = {"user_id": "123", "role": "user"}
        
        with patch('open_webui.utils.auth.SESSION_SECRET', 'test_secret'):
            token = create_token(data)
            decoded = decode_token(token)
            
            assert decoded is not None
            assert decoded["user_id"] == "123"
            assert decoded["role"] == "user"

    def test_decode_token_invalid(self):
        """Test token decoding with invalid token"""
        invalid_token = "invalid.token.here"
        
        with patch('open_webui.utils.auth.SESSION_SECRET', 'test_secret'):
            decoded = decode_token(invalid_token)
            
            assert decoded is None

    def test_extract_token_from_auth_header(self):
        """Test token extraction from authorization header"""
        auth_header = "Bearer test_token_here"
        token = extract_token_from_auth_header(auth_header)
        
        assert token == "test_token_here"

    def test_create_api_key(self):
        """Test API key creation"""
        api_key = create_api_key()
        
        assert api_key is not None
        assert api_key.startswith("sk-")
        assert len(api_key) == 35  # sk- + 32 character UUID without dashes

    def test_get_http_authorization_cred_valid(self):
        """Test HTTP authorization credential parsing with valid header"""
        auth_header = "Bearer test_token"
        cred = get_http_authorization_cred(auth_header)
        
        assert cred is not None
        assert isinstance(cred, HTTPAuthorizationCredentials)
        assert cred.scheme == "Bearer"
        assert cred.credentials == "test_token"

    def test_get_http_authorization_cred_invalid(self):
        """Test HTTP authorization credential parsing with invalid header"""
        auth_header = "invalid_header"
        cred = get_http_authorization_cred(auth_header)
        
        assert cred is None

    def test_get_http_authorization_cred_none(self):
        """Test HTTP authorization credential parsing with None header"""
        cred = get_http_authorization_cred(None)
        
        assert cred is None

    def test_get_current_user_with_token(self):
        """Test getting current user with valid token"""
        # Create a mock request, response, and background tasks
        mock_request = Mock()
        mock_response = Mock()
        mock_background_tasks = Mock()
        mock_request.state.enable_api_key = True
        mock_request.app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS = False
        
        # Mock the Users.get_user_by_api_key method
        with patch('open_webui.utils.auth.Users') as mock_users:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.email = "test@example.com"
            mock_users.get_user_by_api_key.return_value = mock_user
            
            # Test with API key
            auth_token = HTTPAuthorizationCredentials(scheme="Bearer", credentials="sk-test_api_key")
            
            user = get_current_user(mock_request, mock_response, mock_background_tasks, auth_token)
            
            assert user is not None
            assert user.id == "123"

    def test_get_current_user_no_token(self):
        """Test getting current user without token raises exception"""
        mock_request = Mock()
        mock_request.cookies = {}
        mock_response = Mock()
        mock_background_tasks = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_request, mock_response, mock_background_tasks, None)
        
        assert exc_info.value.status_code == 403
        assert "Not authenticated" in str(exc_info.value.detail)

    def test_get_current_user_with_cookie_token(self):
        """Test getting current user with token from cookie"""
        mock_request = Mock()
        mock_request.cookies = {"token": "test_jwt_token"}
        mock_response = Mock()
        mock_background_tasks = Mock()
        
        # Mock decode_token to return valid user data
        with patch('open_webui.utils.auth.decode_token') as mock_decode:
            with patch('open_webui.utils.auth.Users') as mock_users:
                mock_decode.return_value = {"id": "123", "email": "test@example.com"}
                mock_user = Mock()
                mock_user.id = "123"
                mock_users.get_user_by_id.return_value = mock_user
                
                user = get_current_user(mock_request, mock_response, mock_background_tasks, None)
                
                assert user is not None
                assert user.id == "123"

    def test_get_current_user_api_key_disabled(self):
        """Test getting current user with API key when disabled"""
        mock_request = Mock()
        mock_request.state.enable_api_key = False
        mock_response = Mock()
        mock_background_tasks = Mock()
        
        auth_token = HTTPAuthorizationCredentials(scheme="Bearer", credentials="sk-test_api_key")
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_request, mock_response, mock_background_tasks, auth_token)
        
        assert exc_info.value.status_code == 403

    def test_get_current_user_api_key_restricted_path(self):
        """Test getting current user with API key on restricted path"""
        mock_request = Mock()
        mock_request.state.enable_api_key = True
        mock_request.app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS = True
        mock_request.app.state.config.API_KEY_ALLOWED_ENDPOINTS = "/api/v1/chat"
        mock_request.url.path = "/api/v1/restricted"
        mock_response = Mock()
        mock_background_tasks = Mock()
        
        auth_token = HTTPAuthorizationCredentials(scheme="Bearer", credentials="sk-test_api_key")
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_request, mock_response, mock_background_tasks, auth_token)
        
        assert exc_info.value.status_code == 403

    def test_override_static_safe_path(self):
        """Test override static with safe path"""
        with patch('open_webui.utils.auth.STATIC_DIR', '/tmp/static'):
            with patch('os.makedirs') as mock_makedirs:
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = Mock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    auth.override_static('test.txt', 'dGVzdCBjb250ZW50')  # 'test content' in base64
                    
                    mock_makedirs.assert_called_once()
                    mock_open.assert_called_once()

    def test_override_static_unsafe_path(self):
        """Test override static with unsafe path"""
        with patch('open_webui.utils.auth.log') as mock_log:
            auth.override_static('../test.txt', 'dGVzdCBjb250ZW50')
            
            mock_log.error.assert_called_once()

    def test_get_license_data_success(self):
        """Test successful license data retrieval"""
        mock_app = Mock()
        mock_app.state = Mock()
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {
                'count': 100,
                'name': 'Test License',
                'metadata': {'version': '1.0'}
            }
            mock_post.return_value = mock_response
            
            result = auth.get_license_data(mock_app, 'test_key')
            
            assert result is True
            assert mock_app.state.USER_COUNT == 100
            assert mock_app.state.WEBUI_NAME == 'Test License'

    def test_get_license_data_failure(self):
        """Test failed license data retrieval"""
        mock_app = Mock()
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.text = 'Error message'
            mock_post.return_value = mock_response
            
            result = auth.get_license_data(mock_app, 'test_key')
            
            assert result is False

    def test_get_license_data_no_key(self):
        """Test license data retrieval with no key"""
        mock_app = Mock()
        
        result = auth.get_license_data(mock_app, None)
        
        assert result is False

    def test_get_license_data_exception(self):
        """Test license data retrieval with exception"""
        mock_app = Mock()
        
        with patch('requests.post', side_effect=Exception("Network error")):
            result = auth.get_license_data(mock_app, 'test_key')
            
            assert result is False