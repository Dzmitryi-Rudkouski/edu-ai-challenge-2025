import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
from typing import Dict, Any

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyzers.business_analyzer import BusinessAnalyzer
from analyzers.base_analyzer import AnalysisType, ServiceMetadata

@pytest.fixture
def test_api_key():
    return "test-api-key-12345"

@pytest.fixture
def business_analyzer(test_api_key):
    return BusinessAnalyzer("Test Business Service", "https://test-business.com", api_key=test_api_key)

@pytest.mark.asyncio
async def test_business_analyzer_init(test_api_key):
    """Test BusinessAnalyzer initialization."""
    analyzer = BusinessAnalyzer("Test Service", api_key=test_api_key)
    assert analyzer.service_metadata.name == "Test Service"
    assert analyzer.api_key == test_api_key

@pytest.mark.asyncio
async def test_get_service_description(business_analyzer):
    """Test getting service description for business analysis."""
    description = business_analyzer._get_service_description()
    assert "Business analysis of service" in description
    assert "Test Business Service" in description
    assert "test-business.com" in description

@pytest.mark.asyncio
async def test_get_service_description_with_description(business_analyzer):
    """Test getting service description with custom description."""
    business_analyzer.service_metadata.description = "Custom business description"
    description = business_analyzer._get_service_description()
    assert "Custom business description" in description

@pytest.mark.asyncio
async def test_format_list(business_analyzer):
    """Test formatting list for markdown."""
    items = ["Item 1", "Item 2", "Item 3"]
    formatted = business_analyzer._format_list(items)
    assert "- Item 1" in formatted
    assert "- Item 2" in formatted
    assert "- Item 3" in formatted

@pytest.mark.asyncio
async def test_format_list_empty(business_analyzer):
    """Test formatting empty list."""
    formatted = business_analyzer._format_list([])
    assert formatted == "Not specified"

@pytest.mark.asyncio
async def test_format_dict(business_analyzer):
    """Test formatting dictionary for markdown."""
    data = {"key1": "value1", "key2": "value2"}
    formatted = business_analyzer._format_dict(data)
    assert "**key1**: value1" in formatted
    assert "**key2**: value2" in formatted

@pytest.mark.asyncio
async def test_format_dict_empty(business_analyzer):
    """Test formatting empty dictionary."""
    formatted = business_analyzer._format_dict({})
    assert formatted == "Not specified"

@pytest.mark.asyncio
async def test_format_list_of_dicts(business_analyzer):
    """Test formatting list of dictionaries."""
    items = [
        {"name": "Competitor 1", "strength": "High"},
        {"name": "Competitor 2", "strength": "Medium"}
    ]
    formatted = business_analyzer._format_list_of_dicts(items)
    assert "#### Competitor 1" in formatted
    assert "#### Competitor 2" in formatted
    assert "**name**: Competitor 1" in formatted
    assert "**strength**: High" in formatted

@pytest.mark.asyncio
async def test_format_list_of_dicts_empty(business_analyzer):
    """Test formatting empty list of dictionaries."""
    formatted = business_analyzer._format_list_of_dicts([])
    assert formatted == "Not specified"

@pytest.mark.asyncio
async def test_prepare_analysis_prompt(business_analyzer):
    """Test preparing analysis prompt."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    prompt = business_analyzer._prepare_analysis_prompt(service_info)
    assert "Test Service" in prompt
    assert "https://test.com" in prompt
    assert "Test description" in prompt
    assert "бизнес-модели" in prompt.lower()
    assert "целевой аудитории" in prompt.lower()
    assert "зарабатывает деньги" in prompt.lower()

@pytest.mark.asyncio
async def test_prepare_market_analysis_prompt(business_analyzer):
    """Test preparing market analysis prompt."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    prompt = business_analyzer._prepare_market_analysis_prompt(service_info)
    assert "Test Business Service" in prompt
    assert "https://test-business.com" in prompt
    assert "market size" in prompt.lower()
    assert "competitive landscape" in prompt.lower()

@pytest.mark.asyncio
async def test_perform_specific_analysis_success(business_analyzer):
    """Test successful business analysis."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(business_analyzer, 'analyze_description') as mock_analyze:
        mock_analyze.return_value = {
            "business_model": "SaaS model",
            "target_audience": ["Developers", "Startups"],
            "market_analysis": "Growing market",
            "competitors": ["Competitor 1", "Competitor 2"],
            "monetization_strategies": ["Subscription", "Freemium"],
            "growth_potential": "High potential"
        }
        
        result = await business_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "business_model" in result
        assert "target_audience" in result
        assert result["service_info"].name == "Test Business Service"

@pytest.mark.asyncio
async def test_perform_specific_analysis_error(business_analyzer):
    """Test business analysis with error."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(business_analyzer, 'analyze_description') as mock_analyze:
        mock_analyze.return_value = {"error": "Analysis failed"}
        
        result = await business_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "error" in result
        assert result["error"] == "Analysis failed"

@pytest.mark.asyncio
async def test_analyze_market_aspects_success(business_analyzer):
    """Test successful market analysis."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(business_analyzer, '_analyze_with_ai') as mock_analyze:
        mock_analyze.return_value = {
            "market_size": {"total": "1B USD"},
            "market_trends": ["Growing", "Digital transformation"],
            "competitive_landscape": {"competitors": 10},
            "growth_opportunities": ["International expansion"],
            "risks": ["Market saturation"]
        }
        
        result = await business_analyzer._analyze_market_aspects(service_info)
        
        assert "market_size" in result
        assert "market_trends" in result
        assert "competitive_landscape" in result
        assert "growth_opportunities" in result
        assert "risks" in result

@pytest.mark.asyncio
async def test_analyze_market_aspects_error(business_analyzer):
    """Test market analysis with error."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(business_analyzer, '_analyze_with_ai') as mock_analyze:
        mock_analyze.return_value = {"error": "Market analysis failed"}
        
        result = await business_analyzer._analyze_market_aspects(service_info)
        
        assert "error" in result
        assert result["error"] == "Market analysis failed"

@pytest.mark.asyncio
async def test_analyze_market_aspects_exception(business_analyzer):
    """Test market analysis with exception."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(business_analyzer, '_analyze_with_ai', side_effect=Exception("Test error")):
        result = await business_analyzer._analyze_market_aspects(service_info)
        
        assert "error" in result
        assert "Test error" in result["error"]

@pytest.mark.asyncio
async def test_generate_markdown(business_analyzer):
    """Test markdown generation."""
    # Создаем правильную структуру данных для BusinessAnalysisResult
    analysis_results = {
        "service_info": business_analyzer.service_metadata,
        "analysis_type": AnalysisType.BUSINESS,
        "business_model": {"type": "SaaS model"},
        "target_audience": {"primary": "Developers", "secondary": "Startups"},
        "core_functions": ["Function 1", "Function 2"],
        "unique_advantages": ["Advantage 1", "Advantage 2"],
        "market_analysis": "Growing market",
        "competitors": ["Competitor 1", "Competitor 2"],
        "monetization_strategies": ["Strategy 1", "Strategy 2"],
        "growth_potential": "High potential",
        "error": None
    }
    
    markdown = business_analyzer.generate_markdown(analysis_results)
    
    assert "## Бизнес-анализ сервиса" in markdown
    assert "Test Business Service" in markdown
    assert "SaaS model" in markdown
    assert "Developers" in markdown
    assert "Startups" in markdown

@pytest.mark.asyncio
async def test_generate_markdown_with_error(business_analyzer):
    """Test markdown generation with error."""
    # Создаем правильную структуру данных для BusinessAnalysisResult
    analysis_results = {
        "service_info": business_analyzer.service_metadata,
        "analysis_type": AnalysisType.BUSINESS,
        "business_model": {},
        "target_audience": {},
        "market_analysis": {},
        "competitors": [],
        "monetization_strategies": [],
        "growth_potential": {},
        "error": "Analysis failed"
    }
    
    markdown = business_analyzer.generate_markdown(analysis_results)
    
    assert "## Бизнес-анализ" in markdown
    assert "Analysis failed" in markdown

@pytest.mark.asyncio
async def test_create_error_result(business_analyzer):
    """Test creating error result."""
    error_result = business_analyzer._create_error_result("Test error")
    
    assert "error" in error_result
    assert error_result["error"] == "Test error"

@pytest.mark.asyncio
async def test_analyze_success(business_analyzer):
    """Test successful business analysis."""
    with patch.object(business_analyzer, '_get_service_description', return_value="Test description"):
        with patch.object(business_analyzer, '_enrich_service_info') as mock_enrich:
            mock_enrich.return_value = {
                "service_name": "Test Business Service",
                "service_url": "https://test-business.com",
                "description": "Test description"
            }
            
            with patch.object(business_analyzer, '_perform_specific_analysis') as mock_perform:
                mock_perform.return_value = {
                    "service_info": {"service_name": "Test Business Service"},
                    "business_model": "SaaS",
                    "markdown": "## Бизнес-анализ\n\nTest"
                }
                
                result = await business_analyzer.analyze()
                
                assert "business_model" in result
                assert "target_audience" in result
                assert "market_analysis" in result
                assert "competitors" in result
                assert "monetization" in result
                assert "growth_potential" in result 