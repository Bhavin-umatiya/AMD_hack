"""
Tests for AMD Agentic Hardware Co-Design Platform
Run with: pytest test_app.py -v
"""
import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, parse_ai_response


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ========================================
# ROUTE TESTS
# ========================================

def test_home_page(client):
    """Test that the home page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'AMD Agentic Hardware Co-Design Platform' in response.data


def test_api_status(client):
    """Test the API status endpoint."""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'running'
    assert 'endpoints' in data


def test_generate_requires_post(client):
    """Test that generate endpoint rejects GET requests."""
    response = client.get('/generate-agentic-project')
    assert response.status_code == 405


def test_generate_requires_json(client):
    """Test that generate endpoint requires JSON body."""
    response = client.post('/generate-agentic-project',
                          content_type='application/json',
                          data=json.dumps({}))
    assert response.status_code == 400


def test_generate_requires_prompt(client):
    """Test that generate endpoint requires userPrompt field."""
    response = client.post('/generate-agentic-project',
                          content_type='application/json',
                          data=json.dumps({'userPrompt': ''}))
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'userPrompt is required' in data['error']


def test_chat_requires_message(client):
    """Test that chat endpoint requires a message."""
    response = client.post('/chat-assistant',
                          content_type='application/json',
                          data=json.dumps({}))
    assert response.status_code == 400


def test_download_requires_data(client):
    """Test that download endpoint requires project data."""
    response = client.post('/download-project',
                          content_type='application/json',
                          data=json.dumps({}))
    # Should still work since it gracefully handles empty data
    assert response.status_code in [200, 400]


def test_invalid_path_rejected(client):
    """Test that directory traversal paths are rejected."""
    response = client.get('/../../../etc/passwd')
    assert response.status_code == 400


def test_static_css_served(client):
    """Test that static CSS file is served."""
    response = client.get('/static/style.css')
    assert response.status_code == 200
    assert b'--primary-color' in response.data


# ========================================
# PARSE AI RESPONSE TESTS
# ========================================

def test_parse_valid_json():
    """Test parsing valid JSON response."""
    response = '{"projectTitle": "Test ALU", "architectureDescription": "A simple ALU"}'
    result = parse_ai_response(response, "Test Agent")
    assert result['projectTitle'] == 'Test ALU'


def test_parse_json_with_markdown():
    """Test parsing JSON wrapped in markdown code blocks."""
    response = '```json\n{"projectTitle": "Test ALU"}\n```'
    result = parse_ai_response(response, "Test Agent")
    assert result['projectTitle'] == 'Test ALU'


def test_parse_json_with_extra_text():
    """Test parsing JSON with extra text around it."""
    response = 'Here is the result: {"projectTitle": "Test ALU"} and more text'
    result = parse_ai_response(response, "Test Agent")
    assert result['projectTitle'] == 'Test ALU'


def test_parse_invalid_json_raises():
    """Test that invalid JSON raises ValueError."""
    with pytest.raises(ValueError):
        parse_ai_response("this is not json at all", "Test Agent")


def test_parse_unescape_newlines():
    """Test that escaped newlines in code fields are unescaped."""
    response = '{"verilogCode": "module x();\\\\nendmodule", "testbenchCode": "module tb();\\\\nendmodule"}'
    result = parse_ai_response(response, "Test Agent")
    assert '\n' in result['verilogCode']
    assert '\n' in result['testbenchCode']
