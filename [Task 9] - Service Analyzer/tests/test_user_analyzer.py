import pytest
from unittest.mock import patch, AsyncMock
from analyzers.user_analyzer import UserAnalyzer
from analyzers.base_analyzer import AnalysisType

@pytest.fixture
def test_api_key():
    return "test-api-key"

@pytest.fixture
def user_analyzer(test_api_key):
    return UserAnalyzer("Test User Service", "https://test-user.com", api_key=test_api_key)

@pytest.mark.asyncio
async def test_user_analyzer_init(test_api_key):
    """Test user analyzer initialization."""
    analyzer = UserAnalyzer("Test Service", "https://test.com", api_key=test_api_key)
    assert analyzer.service_metadata.name == "Test Service"
    assert analyzer.service_metadata.url == "https://test.com"

@pytest.mark.asyncio
async def test_get_service_description(user_analyzer):
    """Test getting service description."""
    description = user_analyzer._get_service_description()
    assert "Test User Service" in description
    assert "test-user.com" in description

@pytest.mark.asyncio
async def test_get_service_description_with_description(user_analyzer):
    """Test getting service description with provided description."""
    user_analyzer.service_metadata.description = "Custom description"
    description = user_analyzer._get_service_description()
    assert "Custom description" in description

@pytest.mark.asyncio
async def test_format_list(user_analyzer):
    """Test formatting list."""
    test_list = ["item1", "item2", "item3"]
    formatted = user_analyzer._format_list(test_list)
    assert "item1" in formatted
    assert "item2" in formatted
    assert "item3" in formatted

@pytest.mark.asyncio
async def test_format_list_empty(user_analyzer):
    """Test formatting empty list."""
    formatted = user_analyzer._format_list([])
    assert "Not specified" in formatted

@pytest.mark.asyncio
async def test_format_dict(user_analyzer):
    """Test formatting dictionary."""
    test_dict = {"key1": "value1", "key2": "value2"}
    formatted = user_analyzer._format_dict(test_dict)
    assert "key1" in formatted
    assert "value1" in formatted
    assert "key2" in formatted
    assert "value2" in formatted

@pytest.mark.asyncio
async def test_format_dict_empty(user_analyzer):
    """Test formatting empty dictionary."""
    formatted = user_analyzer._format_dict({})
    assert "Not specified" in formatted

@pytest.mark.asyncio
async def test_prepare_analysis_prompt(user_analyzer):
    """Test preparing analysis prompt."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    prompt = user_analyzer._prepare_analysis_prompt(service_info)
    assert "Test Service" in prompt
    assert "https://test.com" in prompt
    assert "Test description" in prompt
    assert "user experience" in prompt.lower()
    assert "user scenarios" in prompt.lower()

@pytest.mark.asyncio
async def test_perform_specific_analysis_success(user_analyzer):
    """Test successful user analysis."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(user_analyzer, 'analyze_description') as mock_analyze:
        mock_analyze.return_value = {
            "user_scenarios": ["Scenario 1", "Scenario 2"],
            "ux_issues": ["Issue 1", "Issue 2"],
            "interface_requirements": ["Requirement 1", "Requirement 2"],
            "success_metrics": ["Metric 1", "Metric 2"],
            "improvement_recommendations": ["Recommendation 1", "Recommendation 2"]
        }
        
        result = await user_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "user_scenarios" in result
        assert "ux_issues" in result
        assert result["service_info"].name == "Test User Service"

@pytest.mark.asyncio
async def test_perform_specific_analysis_error(user_analyzer):
    """Test user analysis with error."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(user_analyzer, 'analyze_description') as mock_analyze:
        mock_analyze.return_value = {"error": "Analysis failed"}
        
        result = await user_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "error" in result
        assert result["error"] == "Analysis failed"

@pytest.mark.asyncio
async def test_generate_markdown(user_analyzer):
    """Test markdown generation."""
    # Создаем правильную структуру данных для UserAnalysisResult
    analysis_results = {
        "service_info": user_analyzer.service_metadata,
        "analysis_type": AnalysisType.USER,
        "user_scenarios": ["Scenario 1", "Scenario 2"],
        "ux_issues": ["Issue 1", "Issue 2"],
        "interface_requirements": ["Requirement 1", "Requirement 2"],
        "success_metrics": ["Metric 1", "Metric 2"],
        "improvement_recommendations": ["Recommendation 1", "Recommendation 2"],
        "error": None
    }
    
    markdown = user_analyzer.generate_markdown(analysis_results)
    
    assert "## User Experience Analysis" in markdown
    assert "Test User Service" in markdown
    assert "Scenario 1" in markdown
    assert "Issue 1" in markdown
    assert "Requirement 1" in markdown
    assert "Metric 1" in markdown
    assert "Recommendation 1" in markdown

@pytest.mark.asyncio
async def test_generate_markdown_with_error(user_analyzer):
    """Test markdown generation with error."""
    # Создаем правильную структуру данных для UserAnalysisResult
    analysis_results = {
        "service_info": user_analyzer.service_metadata,
        "analysis_type": AnalysisType.USER,
        "user_scenarios": [],
        "ux_issues": [],
        "interface_requirements": [],
        "success_metrics": [],
        "improvement_recommendations": [],
        "error": "Analysis failed"
    }
    
    markdown = user_analyzer.generate_markdown(analysis_results)
    
    assert "## User Experience Analysis" in markdown
    assert "Analysis failed" in markdown

@pytest.mark.asyncio
async def test_create_error_result(user_analyzer):
    """Test creating error result."""
    error_result = user_analyzer._create_error_result("Test error")
    
    assert "service_info" in error_result
    assert "analysis" in error_result
    assert "markdown" in error_result
    assert "Test error" in error_result["markdown"]

@pytest.mark.asyncio
async def test_analyze_success(user_analyzer):
    """Test successful user analysis."""
    with patch.object(user_analyzer, '_get_service_description', return_value="Test description"):
        with patch.object(user_analyzer, '_enrich_service_info') as mock_enrich:
            mock_enrich.return_value = {
                "service_name": "Test User Service",
                "service_url": "https://test-user.com",
                "description": "Test description"
            }
            
            with patch.object(user_analyzer, '_perform_specific_analysis') as mock_perform:
                mock_perform.return_value = {
                    "service_info": {"service_name": "Test User Service"},
                    "user_scenarios": ["Test scenario"],
                    "markdown": "## User Experience Analysis\n\nTest"
                }
                
                result = await user_analyzer.analyze()
                
                assert "user_scenarios" in result
                assert "ux_issues" in result
                assert "interface_requirements" in result
                assert "success_metrics" in result
                assert "improvement_recommendations" in result

@pytest.mark.asyncio
async def test_perform_specific_analysis_with_web_metadata(user_analyzer):
    """Test user analysis with web metadata."""
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
    
    with patch.object(user_analyzer, 'analyze_description') as mock_analyze:
        mock_analyze.return_value = {
            "user_scenarios": ["Scenario 1"],
            "ux_issues": ["Issue 1"],
            "interface_requirements": ["Requirement 1"],
            "success_metrics": ["Metric 1"],
            "improvement_recommendations": ["Recommendation 1"]
        }
        
        result = await user_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "user_scenarios" in result
        assert "raw_data" in result

@pytest.mark.asyncio
async def test_perform_specific_analysis_exception(user_analyzer):
    """Test user analysis with exception."""
    service_info = {
        "service_name": "Test Service",
        "service_url": "https://test.com",
        "description": "Test description"
    }
    
    with patch.object(user_analyzer, 'analyze_description', side_effect=Exception("Test error")):
        result = await user_analyzer._perform_specific_analysis(service_info)
        
        assert "service_info" in result
        assert "analysis" in result
        assert "markdown" in result
        assert "Test error" in result["markdown"] 