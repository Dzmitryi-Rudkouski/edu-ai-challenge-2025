import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
from typing import Dict, Any, Optional
import json
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyzers.base_analyzer import (
    BaseAnalyzer, 
    AnalysisType, 
    ServiceMetadata,
    AnalysisResponse,
    APIError,
    APIKeyError,
    APIRequestError,
    APIRateLimitError
)

class MockResponse:
    """Mock class for aiohttp response."""
    def __init__(self, status: int, text: str, headers: Dict[str, str] = None):
        self.status = status
        self._text = text
        self.headers = headers or {}

    async def text(self) -> str:
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class MockSession:
    """Mock class for aiohttp session."""
    def __init__(self, raise_exc=None):
        self.raise_exc = raise_exc

    async def get(self, url, timeout=None):
        if self.raise_exc:
            raise self.raise_exc
        return MockResponse(200, "<html><body>Test</body></html>", {"Server": "nginx"})

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class TestAnalyzer(BaseAnalyzer):
    """Test implementation of BaseAnalyzer."""
    
    def _prepare_analysis_prompt(self, service_info: Dict[str, Any]) -> str:
        return f"Analyze {service_info['service_name']}"
    
    async def _perform_specific_analysis(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "service_info": service_info,
            "analysis": {"test": "analysis"},
            "markdown": "# Test Analysis\n\nTest content"
        }
    
    def generate_markdown(self, analysis_results: Dict[str, Any]) -> str:
        return "# Test Analysis\n\nTest content"

@pytest.fixture
def test_api_key():
    return "test-api-key-12345"

@pytest.fixture
def analyzer(test_api_key):
    return TestAnalyzer("Test Service", "https://test-service.com", api_key=test_api_key)

@pytest.mark.asyncio
async def test_get_service_description(analyzer):
    """Test getting service description."""
    with patch.object(analyzer, '_get_session') as mock_get_session:
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        
        description = await analyzer._get_service_description()
        assert "Test Service" in description
        assert "test-service.com" in description

@pytest.mark.asyncio
async def test_get_service_description_no_url(analyzer):
    """Test getting service description without URL."""
    analyzer.service_metadata.url = None
    analyzer.service_metadata.description = "Test description"
    
    description = await analyzer._get_service_description()
    assert description == "Service Test Service"

@pytest.mark.asyncio
async def test_enrich_service_info(analyzer):
    """Test enriching service information."""
    with patch.object(analyzer, '_get_session') as mock_get_session:
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        
        service_info = await analyzer._enrich_service_info()
        
        assert service_info["service_name"] == "Test Service"
        assert service_info["service_url"] == "https://test-service.com"
        assert "additional_data" in service_info

@pytest.mark.asyncio
async def test_analyze_with_ai(analyzer):
    """Test AI analysis."""
    with patch.object(analyzer, '_call_ai_api') as mock_call_api:
        mock_call_api.return_value = '{"test": "result"}'
        
        result = await analyzer._analyze_with_ai({"service_name": "test"})
        assert "test" in result
        assert result["test"] == "result"

@pytest.mark.asyncio
async def test_analyze_with_ai_error(analyzer):
    """Test AI analysis with error."""
    # Отключаем retry для теста
    with patch.object(analyzer, '_call_ai_api', side_effect=APIRateLimitError("Rate limit exceeded")):
        result = await analyzer._analyze_with_ai({"service_name": "test"})
        assert "error" in result
        assert "Rate limit exceeded" in result["error"]

@pytest.mark.asyncio
async def test_analyze_success(analyzer):
    """Test successful analysis."""
    with patch.object(analyzer, '_get_service_description', return_value="Test description"):
        result = await analyzer.analyze()
        
        assert "service_info" in result
        assert "analysis" in result
        assert "markdown" in result
        assert result["service_info"]["service_name"] == "Test Service"

@pytest.mark.asyncio
async def test_analyze_api_error(test_api_key, caplog):
    """Test analysis with API error."""
    caplog.set_level(logging.WARNING)
    # Создаем анализатор с моком сессии, который будет вызывать ошибку
    analyzer = TestAnalyzer("Test Service", "https://test-service.com", api_key=test_api_key)
    error_session = MockSession(raise_exc=APIRequestError("API request failed"))
    analyzer._session = error_session
    
    # Патчим метод _get_service_description, чтобы он не пытался делать реальный запрос
    with patch.object(analyzer, '_get_service_description', return_value="Test Description"):
        result = await analyzer.analyze()
        # Проверяем, что результат содержит всю необходимую информацию
        assert "service_info" in result
        assert result["service_info"]["service_name"] == "Test Service"
        assert result["service_info"]["service_url"] == "https://test-service.com"
        assert "analysis" in result
        assert "markdown" in result
        # Проверяем, что в логах есть сообщение об ошибке
        assert any("Error enriching service info" in record.message for record in caplog.records)

@pytest.mark.asyncio
async def test_unimplemented_methods(test_api_key):
    """Test that abstract methods are properly implemented."""
    analyzer = TestAnalyzer("Test Service", api_key=test_api_key)
    assert callable(analyzer._prepare_analysis_prompt)
    assert callable(analyzer.generate_markdown)
    assert callable(analyzer._perform_specific_analysis)

@pytest.mark.asyncio
async def test_detect_technologies(analyzer):
    """Test technology detection."""
    html = """
    <html>
        <head>
            <script src="https://code.jquery.com/jquery.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0/dist/js/bootstrap.min.js"></script>
        </head>
        <body>
            <div data-reactroot>
                <p>React app</p>
            </div>
            <script>
                // Google Analytics
                gtag('config', 'GA_MEASUREMENT_ID');
            </script>
        </body>
    </html>
    """
    headers = {"Server": "nginx/1.18.0"}
    
    technologies = await analyzer._detect_technologies(html, headers)
    
    assert "React" in technologies["frontend"]
    assert "Nginx" in technologies["backend"]
    assert "jQuery" in technologies["libraries"]
    assert "Bootstrap" in technologies["libraries"]

@pytest.mark.asyncio
async def test_detect_technologies_error(analyzer):
    """Test technology detection with error."""
    with patch('bs4.BeautifulSoup', side_effect=Exception("Parse error")):
        technologies = await analyzer._detect_technologies("<html></html>", {})
        assert technologies["frontend"] == []
        assert technologies["backend"] == []

@pytest.mark.asyncio
async def test_call_ai_api_success(analyzer):
    """Test successful AI API call."""
    with patch.object(analyzer._client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"test": "result"}'
        mock_create.return_value = mock_response
        
        result = await analyzer._call_ai_api("Test prompt")
        assert result == '{"test": "result"}'

@pytest.mark.asyncio
async def test_call_ai_api_rate_limit(analyzer):
    """Test AI API call with rate limit error."""
    with patch.object(analyzer._client.chat.completions, 'create') as mock_create:
        mock_create.side_effect = Exception("Rate limit exceeded")
        
        with pytest.raises(Exception):
            await analyzer._call_ai_api("Test prompt")

@pytest.mark.asyncio
async def test_context_manager(analyzer):
    """Test async context manager."""
    async with analyzer as a:
        assert a == analyzer
        assert a._session is not None
    
    assert analyzer._session is None

@pytest.mark.asyncio
async def test_get_session(analyzer):
    """Test getting session."""
    session = await analyzer._get_session()
    assert session is not None
    assert isinstance(session, aiohttp.ClientSession)

@pytest.mark.asyncio
async def test_validate_analysis_result(analyzer):
    """Test analysis result validation."""
    valid_result = {
        "service_info": {"name": "test"},
        "analysis": {"data": "test"},
        "markdown": "# Test"
    }
    assert analyzer._validate_analysis_result(valid_result) is True
    
    invalid_result = {"service_info": {"name": "test"}}
    assert analyzer._validate_analysis_result(invalid_result) is False

@pytest.mark.asyncio
async def test_create_error_result(analyzer):
    """Test creating error result."""
    error_result = analyzer._create_error_result("Test error")
    
    assert "error" in error_result
    assert error_result["error"] == "Test error"
    assert "service_info" in error_result
    assert "analysis" in error_result
    assert "markdown" in error_result
    assert "Test error" in error_result["markdown"]

@pytest.mark.asyncio
async def test_get_system_prompt(analyzer):
    """Test getting system prompt."""
    prompt = analyzer._get_system_prompt(AnalysisType.BUSINESS)
    assert "эксперт по анализу сервисов" in prompt
    assert "бизнес-анализа" in prompt

@pytest.mark.asyncio
async def test_get_user_prompt(analyzer):
    """Test getting user prompt."""
    prompt = analyzer._get_user_prompt("Test description", AnalysisType.TECHNICAL)
    assert "Test Service" in prompt
    assert "Test description" in prompt
    assert "technical" in prompt 