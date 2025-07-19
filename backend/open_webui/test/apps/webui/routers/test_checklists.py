import pytest
from open_webui.models.checklists import ChecklistForm

class TestChecklists:
    def test_create_checklist(self, client, user_token):
        checklist_data = {
            "command": "test-checklist",
            "title": "Test Checklist",
            "description": "A test checklist",
            "items": [
                {"prompt_command": "/test-prompt", "order_index": 1}
            ]
        }
        
        response = client.post(
            "/api/v1/checklists/create",
            json=checklist_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Checklist"
    
    def test_get_checklists(self, client, user_token):
        response = client.get(
            "/api/v1/checklists/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)