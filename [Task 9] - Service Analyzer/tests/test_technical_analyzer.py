import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
from typing import Dict, Any

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyzers.technical_analyzer import TechnicalAnalyzer
from analyzers.base_analyzer import AnalysisType, ServiceMetadata

@pytest.fixture
def test_api_key():
    return "test-api-key-12345"

@pytest.fixture
def technical_analyzer(test_api_key):
    return TechnicalAnalyzer("Test Technical Service", "https://test-technical.com", api_key=test_api_key)

@pytest.mark.asyncio
async def test_technical_analyzer_init(test_api_key):
    """Test TechnicalAnalyzer initialization."""
    analyzer = TechnicalAnalyzer("Test Service", api_key=test_api_key)
    assert analyzer.service_metadata.name == "Test Service"
    assert analyzer.api_key == test_api_key

@pytest.mark.asyncio
async def test_get_service_description(technical_analyzer):
    """Test getting service description for technical analysis."""
    description = technical_analyzer._get_service_description()
    assert "Technical analysis of service" in description
    assert "Test Technical Service" in description
    assert "test-technical.com" in description

@pytest.mark.asyncio
async def test_get_service_description_with_description(technical_analyzer):
    """Test getting service description with custom description."""
    technical_analyzer.service_metadata.description = "Custom technical description"
    description = technical_analyzer._get_service_description()
    assert "Custom technical description" in description

@pytest.mark.asyncio
async def test_format_dict(technical_analyzer):
    """Test formatting dictionary for markdown."""
    data = {"key1": "value1", "key2": "value2"}
    formatted = technical_analyzer._format_dict(data)
    assert "**key1**: value1" in formatted
    assert "**key2**: value2" in formatted

@pytest.mark.asyncio
async def test_format_dict_empty(technical_analyzer):
    """Test formatting empty dictionary."""
    formatted = technical_analyzer._format_dict({})
    assert formatted == "Не указано"

@pytest.mark.asyncio
async def test_prepare_analysis_prompt(technical_analyzer):
    """Test preparing analysis prompt."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description",
        "additional_data": {"key": "value"}
    }
    
    prompt = technical_analyzer._prepare_analysis_prompt(service_info)
    assert "Test Service" in prompt
    assert "https://test.com" in prompt
    assert "Test description" in prompt
    assert "architecture" in prompt.lower()
    assert "technical requirements" in prompt.lower()
    assert "scalability" in prompt.lower()

@pytest.mark.asyncio
async def test_perform_specific_analysis_success(technical_analyzer):
    """Test successful technical analysis."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(technical_analyzer, 'analyze_description') as mock_analyze:
        mock_analyze.return_value = {
            "architecture": "Microservices",
            "technical_requirements": ["High availability", "Scalability"],
            "technical_risks": ["Security risks", "Performance issues"],
            "integrations": ["API", "Database"],
            "scalability": "Horizontal scaling"
        }
        
        result = await technical_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "architecture" in result
        assert "technical_requirements" in result
        assert result["service_info"].name == "Test Technical Service"

@pytest.mark.asyncio
async def test_perform_specific_analysis_error(technical_analyzer):
    """Test technical analysis with error."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(technical_analyzer, 'analyze_description') as mock_analyze:
        mock_analyze.return_value = {"error": "Analysis failed"}
        
        result = await technical_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "error" in result
        assert result["error"] == "Analysis failed"

@pytest.mark.asyncio
async def test_check_availability_success(technical_analyzer):
    """Test successful availability check."""
    with patch.object(technical_analyzer, '_check_availability') as mock_check:
        mock_check.return_value = {
            "is_available": True,
            "status_code": 200,
            "response_time": 0.1,
            "headers": {"Server": "nginx", "Content-Type": "text/html"}
        }
        
        availability = await technical_analyzer._check_availability()
        
        assert availability["is_available"] is True
        assert availability["status_code"] == 200
        assert "nginx" in str(availability["headers"])

@pytest.mark.asyncio
async def test_check_availability_error(technical_analyzer):
    """Test availability check with error."""
    with patch.object(technical_analyzer, '_check_availability') as mock_check:
        mock_check.return_value = {"error": "Connection failed"}
        
        availability = await technical_analyzer._check_availability()
        
        assert "error" in availability
        assert "Connection failed" in availability["error"]

@pytest.mark.asyncio
async def test_generate_markdown(technical_analyzer):
    """Test markdown generation."""
    # Создаем правильную структуру данных для TechnicalAnalysisResult
    analysis_results = {
        "service_info": technical_analyzer.service_metadata,
        "analysis_type": AnalysisType.TECHNICAL,
        "architecture": "Microservices",
        "technical_requirements": ["High availability", "Scalability"],
        "technical_risks": ["Security risks", "Performance issues"],
        "integrations": ["API", "Database"],
        "scalability": {"approach": "Horizontal scaling"},
        "availability": {
            "is_available": True,
            "status_code": 200,
            "response_time": 0.1,
            "headers": {"Server": "nginx"}
        },
        "error": None
    }
    
    markdown = technical_analyzer.generate_markdown(analysis_results)
    
    assert "## Технический анализ" in markdown
    assert "Test Technical Service" in markdown
    assert "Microservices" in markdown
    assert "High availability" in markdown
    assert "Security risks" in markdown
    assert "API" in markdown
    assert "Horizontal scaling" in markdown

@pytest.mark.asyncio
async def test_generate_markdown_with_error(technical_analyzer):
    """Test markdown generation with error."""
    # Создаем правильную структуру данных для TechnicalAnalysisResult
    analysis_results = {
        "service_info": technical_analyzer.service_metadata,
        "analysis_type": AnalysisType.TECHNICAL,
        "architecture": None,
        "technical_requirements": [],
        "technical_risks": [],
        "integrations": [],
        "scalability": {},
        "error": "Analysis failed"
    }
    
    markdown = technical_analyzer.generate_markdown(analysis_results)
    
    assert "## Технический анализ" in markdown
    assert "Analysis failed" in markdown

@pytest.mark.asyncio
async def test_create_error_result(technical_analyzer):
    """Test creating error result."""
    error_result = technical_analyzer._create_error_result("Test error")
    
    assert "error" in error_result
    assert error_result["error"] == "Test error"

@pytest.mark.asyncio
async def test_analyze_success(technical_analyzer):
    """Test successful technical analysis."""
    with patch.object(technical_analyzer, '_get_service_description', return_value="Test description"):
        with patch.object(technical_analyzer, '_enrich_service_info') as mock_enrich:
            mock_enrich.return_value = {
                "service_name": "Test Technical Service",
                "service_url": "https://test-technical.com",
                "description": "Test description"
            }
            
            with patch.object(technical_analyzer, '_perform_specific_analysis') as mock_perform:
                mock_perform.return_value = {
                    "service_info": {"service_name": "Test Technical Service"},
                    "architecture": "Microservices",
                    "markdown": "## Технический анализ\n\nTest"
                }
                
                result = await technical_analyzer.analyze()
                
                assert "architecture" in result
                assert "technical_requirements" in result
                assert "technical_risks" in result
                assert "integrations" in result
                assert "scalability" in result

@pytest.mark.asyncio
async def test_perform_specific_analysis_with_web_metadata(technical_analyzer):
    """Test technical analysis with web metadata."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description",
        "additional_data": {
            "web_metadata": {
                "technologies": {
                    "frontend": ["React"],
                    "backend": ["Node.js"]
                }
            }
        }
    }
    
    with patch.object(technical_analyzer, 'analyze_description') as mock_analyze:
        mock_analyze.return_value = {
            "architecture": "Microservices",
            "technical_requirements": ["High availability"],
            "technical_risks": ["Security risks"],
            "integrations": ["API"],
            "scalability": "Horizontal scaling"
        }
        
        result = await technical_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "architecture" in result
        assert "raw_data" in result

@pytest.mark.asyncio
async def test_perform_specific_analysis_exception(technical_analyzer):
    """Test technical analysis with exception."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(technical_analyzer, 'analyze_description', side_effect=Exception("Test error")):
        result = await technical_analyzer._perform_specific_analysis(service_info)
        
        assert "error" in result
        assert "Test error" in result["error"] 