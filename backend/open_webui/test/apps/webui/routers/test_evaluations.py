import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from open_webui.test.util.abstract_integration_test import AbstractPostgresTest
from open_webui.test.util.mock_user import mock_webui_user


class TestEvaluations(AbstractPostgresTest):
    BASE_PATH = "/api/v1/evaluations"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.feedbacks import Feedbacks
        cls.feedbacks = Feedbacks

    def setup_method(self):
        super().setup_method()
        # Create test feedback
        self.test_feedback = self.feedbacks.insert_new_feedback(
            user_id="1",
            form_data={
                "type": "rating",
                "content": "Test feedback content",
                "data": {"rating": 5, "comment": "Great response!"},
                "meta": {"model": "gpt-4", "session_id": "test-session"}
            }
        )

    def test_get_config_admin(self):
        """Test getting evaluation configuration as admin"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/config"))
        
        assert response.status_code == 200
        data = response.json()
        assert "ENABLE_EVALUATION_ARENA_MODELS" in data
        assert "EVALUATION_ARENA_MODELS" in data
        assert isinstance(data["ENABLE_EVALUATION_ARENA_MODELS"], bool)
        assert isinstance(data["EVALUATION_ARENA_MODELS"], list)

    def test_get_config_non_admin(self):
        """Test getting evaluation configuration as non-admin user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/config"))
        
        assert response.status_code == 403

    def test_update_config_admin(self):
        """Test updating evaluation configuration as admin"""
        config_data = {
            "ENABLE_EVALUATION_ARENA_MODELS": True,
            "EVALUATION_ARENA_MODELS": [
                {"name": "gpt-4", "id": "gpt-4", "provider": "openai"},
                {"name": "claude-3", "id": "claude-3", "provider": "anthropic"}
            ]
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/config"),
                json=config_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_EVALUATION_ARENA_MODELS"] is True
        assert len(data["EVALUATION_ARENA_MODELS"]) == 2

    def test_update_config_partial(self):
        """Test partial update of evaluation configuration"""
        config_data = {
            "ENABLE_EVALUATION_ARENA_MODELS": False
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/config"),
                json=config_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_EVALUATION_ARENA_MODELS"] is False

    def test_update_config_non_admin(self):
        """Test updating evaluation configuration as non-admin user"""
        config_data = {
            "ENABLE_EVALUATION_ARENA_MODELS": True
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/config"),
                json=config_data
            )
        
        assert response.status_code == 403

    def test_get_all_feedbacks_admin(self):
        """Test getting all feedbacks as admin"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/feedbacks/all"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check feedback structure
        feedback = data[0]
        assert "id" in feedback
        assert "type" in feedback
        assert "content" in feedback
        assert "user" in feedback

    def test_get_all_feedbacks_non_admin(self):
        """Test getting all feedbacks as non-admin user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/feedbacks/all"))
        
        assert response.status_code == 403

    def test_delete_all_feedbacks_admin(self):
        """Test deleting all feedbacks as admin"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.delete(self.create_url("/feedbacks/all"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_all_feedbacks_non_admin(self):
        """Test deleting all feedbacks as non-admin user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url("/feedbacks/all"))
        
        assert response.status_code == 403

    def test_export_all_feedbacks_admin(self):
        """Test exporting all feedbacks as admin"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/feedbacks/all/export"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_export_all_feedbacks_non_admin(self):
        """Test exporting all feedbacks as non-admin user"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/feedbacks/all/export"))
        
        assert response.status_code == 403

    def test_get_user_feedbacks(self):
        """Test getting user's own feedbacks"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/feedbacks/user"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_delete_user_feedbacks(self):
        """Test deleting user's own feedbacks"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url("/feedbacks"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_create_feedback_success(self):
        """Test creating new feedback"""
        feedback_data = {
            "type": "rating",
            "content": "New feedback content",
            "data": {"rating": 4, "comment": "Good response"},
            "meta": {"model": "gpt-3.5-turbo", "session_id": "new-session"}
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/feedback"),
                json=feedback_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "rating"
        assert data["content"] == "New feedback content"
        assert data["user_id"] == "1"

    def test_create_feedback_invalid_data(self):
        """Test creating feedback with invalid data"""
        feedback_data = {
            "type": "",  # Invalid empty type
            "content": "Test content"
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/feedback"),
                json=feedback_data
            )
        
        assert response.status_code == 400

    def test_get_feedback_by_id_success(self):
        """Test getting feedback by ID"""
        feedback_id = self.test_feedback.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url(f"/feedback/{feedback_id}"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == feedback_id
        assert data["user_id"] == "1"

    def test_get_feedback_by_id_not_found(self):
        """Test getting non-existent feedback"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(self.create_url("/feedback/nonexistent-id"))
        
        assert response.status_code == 404

    def test_get_feedback_by_id_unauthorized(self):
        """Test getting feedback by different user"""
        feedback_id = self.test_feedback.id
        
        with mock_webui_user(id="2"):  # Different user
            response = self.fast_api_client.get(self.create_url(f"/feedback/{feedback_id}"))
        
        assert response.status_code == 404

    def test_update_feedback_by_id_success(self):
        """Test updating feedback by ID"""
        feedback_id = self.test_feedback.id
        update_data = {
            "type": "rating",
            "content": "Updated feedback content",
            "data": {"rating": 3, "comment": "Updated comment"},
            "meta": {"model": "gpt-4", "session_id": "updated-session"}
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url(f"/feedback/{feedback_id}"),
                json=update_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated feedback content"
        assert data["data"]["rating"] == 3

    def test_update_feedback_by_id_not_found(self):
        """Test updating non-existent feedback"""
        update_data = {
            "type": "rating",
            "content": "Updated content",
            "data": {"rating": 5}
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/feedback/nonexistent-id"),
                json=update_data
            )
        
        assert response.status_code == 404

    def test_update_feedback_by_id_unauthorized(self):
        """Test updating feedback by different user"""
        feedback_id = self.test_feedback.id
        update_data = {
            "type": "rating",
            "content": "Unauthorized update",
            "data": {"rating": 1}
        }
        
        with mock_webui_user(id="2"):  # Different user
            response = self.fast_api_client.post(
                self.create_url(f"/feedback/{feedback_id}"),
                json=update_data
            )
        
        assert response.status_code == 404

    def test_delete_feedback_by_id_success(self):
        """Test deleting feedback by ID as owner"""
        feedback_id = self.test_feedback.id
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url(f"/feedback/{feedback_id}"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_feedback_by_id_admin(self):
        """Test deleting feedback by ID as admin"""
        feedback_id = self.test_feedback.id
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.delete(self.create_url(f"/feedback/{feedback_id}"))
        
        assert response.status_code == 200
        assert response.json() is True

    def test_delete_feedback_by_id_not_found(self):
        """Test deleting non-existent feedback"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url("/feedback/nonexistent-id"))
        
        assert response.status_code == 404

    def test_delete_feedback_by_id_unauthorized(self):
        """Test deleting feedback by different user"""
        feedback_id = self.test_feedback.id
        
        with mock_webui_user(id="2"):  # Different user
            response = self.fast_api_client.delete(self.create_url(f"/feedback/{feedback_id}"))
        
        assert response.status_code == 404

    def test_feedback_validation(self):
        """Test feedback data validation"""
        invalid_feedback_data = {
            "type": "invalid_type",
            "content": "",  # Empty content
            "data": "invalid_data_format"  # Should be dict
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/feedback"),
                json=invalid_feedback_data
            )
        
        assert response.status_code == 400

    def test_feedback_rating_validation(self):
        """Test feedback rating validation"""
        feedback_data = {
            "type": "rating",
            "content": "Test rating",
            "data": {"rating": 11, "comment": "Invalid rating"}  # Rating > 10
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/feedback"),
                json=feedback_data
            )
        
        assert response.status_code == 400

    def test_feedback_comparison_data(self):
        """Test creating comparison feedback"""
        feedback_data = {
            "type": "comparison",
            "content": "Model A vs Model B",
            "data": {
                "winner": "model_a",
                "models": ["model_a", "model_b"],
                "responses": ["Response A", "Response B"]
            },
            "meta": {"session_id": "comparison-session"}
        }
        
        with mock_webui_user(id="1"):
            response = self.fast_api_client.post(
                self.create_url("/feedback"),
                json=feedback_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "comparison"
        assert data["data"]["winner"] == "model_a"

    def test_feedback_arena_models_config(self):
        """Test arena models configuration"""
        arena_models = [
            {"name": "GPT-4", "id": "gpt-4", "provider": "openai"},
            {"name": "Claude-3", "id": "claude-3", "provider": "anthropic"},
            {"name": "Llama-2", "id": "llama-2", "provider": "meta"}
        ]
        
        config_data = {
            "ENABLE_EVALUATION_ARENA_MODELS": True,
            "EVALUATION_ARENA_MODELS": arena_models
        }
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.post(
                self.create_url("/config"),
                json=config_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ENABLE_EVALUATION_ARENA_MODELS"] is True
        assert len(data["EVALUATION_ARENA_MODELS"]) == 3

    def test_feedback_aggregation_stats(self):
        """Test feedback aggregation and statistics"""
        # Create multiple feedbacks
        for i in range(3):
            self.feedbacks.insert_new_feedback(
                user_id="1",
                form_data={
                    "type": "rating",
                    "content": f"Test feedback {i}",
                    "data": {"rating": i + 3, "comment": f"Comment {i}"},
                    "meta": {"model": "gpt-4", "session_id": f"session-{i}"}
                }
            )
        
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/feedbacks/all"))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4  # Original + 3 new feedbacks

    def test_feedback_export_format(self):
        """Test feedback export format"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/feedbacks/all/export"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            feedback = data[0]
            assert "id" in feedback
            assert "type" in feedback
            assert "content" in feedback
            assert "data" in feedback
            assert "user_id" in feedback
            assert "created_at" in feedback

    def test_feedback_user_response_format(self):
        """Test feedback user response format"""
        with mock_webui_user(role="admin"):
            response = self.fast_api_client.get(self.create_url("/feedbacks/all"))
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            feedback = data[0]
            assert "user" in feedback
            if feedback["user"]:
                user = feedback["user"]
                assert "id" in user
                assert "name" in user
                assert "email" in user
                assert "role" in user

    def test_feedback_pagination(self):
        """Test feedback pagination (if implemented)"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(
                self.create_url("/feedbacks/user"),
                params={"page": 1, "limit": 10}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_feedback_filtering(self):
        """Test feedback filtering by type"""
        with mock_webui_user(id="1"):
            response = self.fast_api_client.get(
                self.create_url("/feedbacks/user"),
                params={"type": "rating"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_feedback_bulk_operations(self):
        """Test bulk feedback operations"""
        # Create multiple feedbacks first
        feedback_ids = []
        for i in range(3):
            feedback = self.feedbacks.insert_new_feedback(
                user_id="1",
                form_data={
                    "type": "rating",
                    "content": f"Bulk test {i}",
                    "data": {"rating": 5},
                    "meta": {"session_id": f"bulk-{i}"}
                }
            )
            feedback_ids.append(feedback.id)
        
        # Test bulk delete
        with mock_webui_user(id="1"):
            response = self.fast_api_client.delete(self.create_url("/feedbacks"))
        
        assert response.status_code == 200
        assert response.json() is True