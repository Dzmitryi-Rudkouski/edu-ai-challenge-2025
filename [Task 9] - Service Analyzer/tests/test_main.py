import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from typer.testing import CliRunner
import json
import aiohttp
from main import app, run_analysis, save_report, main

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_analyzers():
    business = MagicMock()
    business.__class__.__name__ = "BusinessAnalyzer"
    business.analyze = AsyncMock(return_value={"markdown": "## Бизнес-анализ\n\nTest"})
    
    technical = MagicMock()
    technical.__class__.__name__ = "TechnicalAnalyzer"
    technical.analyze = AsyncMock(return_value={"markdown": "## Технический анализ\n\nTest"})
    
    user = MagicMock()
    user.__class__.__name__ = "UserAnalyzer"
    user.analyze = AsyncMock(return_value={"markdown": "## Пользовательский анализ\n\nTest"})
    
    return business, technical, user

@pytest.mark.asyncio
async def test_run_analysis_success(mock_analyzers):
    """Test successful analysis run."""
    business, technical, user = mock_analyzers
    
    with patch("main.BusinessAnalyzer", return_value=business), \
         patch("main.TechnicalAnalyzer", return_value=technical), \
         patch("main.UserAnalyzer", return_value=user):
        
        results = await run_analysis(
            service_name="test-service",
            api_key="test-key",
            url="http://test.com",
            description="Test description"
        )
        
        assert len(results) == 3
        assert all("markdown" in result for result in results)
        assert business.analyze.call_count == 1
        assert technical.analyze.call_count == 1
        assert user.analyze.call_count == 1

@pytest.mark.asyncio
async def test_run_analysis_analyzer_error(mock_analyzers):
    """Test analysis with analyzer error."""
    business, technical, user = mock_analyzers
    technical.analyze.side_effect = Exception("Test error")
    
    with patch("main.BusinessAnalyzer", return_value=business), \
         patch("main.TechnicalAnalyzer", return_value=technical), \
         patch("main.UserAnalyzer", return_value=user):
        
        results = await run_analysis(
            service_name="test-service",
            api_key="test-key",
            url="http://test.com"
        )
        
        assert len(results) == 3
        assert "error" in results[1]
        assert "Test error" in results[1]["error"]

def test_save_report(tmp_path):
    """Test saving report to file."""
    content = "# Test Report\n\nTest content"
    output_file = tmp_path / "test.md"
    
    save_report(content, output_file)
    
    assert output_file.exists()
    saved_content = output_file.read_text(encoding='utf-8')
    assert "title: Service Analysis" in saved_content
    assert "Test Report" in saved_content
    assert "Test content" in saved_content

def test_main_help(runner):
    """Test help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Arguments" in result.output
    assert "Options" in result.output
    assert "NAME" in result.output
    assert "--api-key" in result.output
    assert "--output" in result.output
    assert "--no-preview" in result.output

def test_main_missing_required_argument(runner):
    """Test command with missing required argument."""
    result = runner.invoke(app, [])
    assert result.exit_code != 0
    assert "Missing argument" in result.output

def test_main_success(runner, mock_analyzers, tmp_path):
    """Test successful command execution."""
    business, technical, user = mock_analyzers
    output_file = tmp_path / "analysis.md"
    
    with patch("main.run_analysis", new_callable=AsyncMock) as mock_run_analysis, \
         patch("main.save_report") as mock_save_report:
        
        mock_run_analysis.return_value = [
            {"markdown": "## Бизнес-анализ\n\nTest"},
            {"markdown": "## Технический анализ\n\nTest"},
            {"markdown": "## Пользовательский анализ\n\nTest"}
        ]
        
        result = runner.invoke(app, [
            "test-service",
            "--api-key", "test-key",
            "--url", "http://test.com",
            "--output", str(output_file)
        ])
        
        assert result.exit_code == 0
        mock_run_analysis.assert_called_once()
        mock_save_report.assert_called_once()
        assert "Предварительный просмотр отчета:" in result.output

def test_main_no_preview(runner, mock_analyzers, tmp_path):
    """Test command with no preview option."""
    business, technical, user = mock_analyzers
    output_file = tmp_path / "analysis.md"
    
    with patch("main.run_analysis", new_callable=AsyncMock) as mock_run_analysis, \
         patch("main.save_report") as mock_save_report:
        
        mock_run_analysis.return_value = [
            {"markdown": "## Бизнес-анализ\n\nTest"},
            {"markdown": "## Технический анализ\n\nTest"},
            {"markdown": "## Пользовательский анализ\n\nTest"}
        ]
        
        result = runner.invoke(app, [
            "test-service",
            "--api-key", "test-key",
            "--url", "http://test.com",
            "--output", str(output_file),
            "--no-preview"
        ])
        
        assert result.exit_code == 0
        mock_run_analysis.assert_called_once()
        mock_save_report.assert_called_once()
        assert "Предварительный просмотр отчета:" not in result.output

@pytest.mark.asyncio
async def test_run_analysis_error():
    """Test service analysis with error."""
    with patch('main.BusinessAnalyzer') as mock_business, \
         patch('main.TechnicalAnalyzer') as mock_tech, \
         patch('main.UserAnalyzer') as mock_user:
        
        # Setup mock analyzers
        mock_tech_instance = mock_tech.return_value
        mock_user_instance = mock_user.return_value
        mock_business_instance = mock_business.return_value

        # Setup mock to raise exception
        mock_tech_instance.analyze = AsyncMock(side_effect=Exception("Technical Analysis Error"))
        mock_user_instance.analyze = AsyncMock(side_effect=Exception("User Analysis Error"))
        mock_business_instance.analyze = AsyncMock(side_effect=Exception("Business Analysis Error"))

        # Run analysis
        results = await run_analysis(
            service_name="Test Service",
            api_key="test-api-key",
            url="https://test-service.com"
        )

        # Verify results
        assert len(results) == 3
        assert all("error" in result for result in results)
        assert any("Technical Analysis Error" in result["error"] for result in results)
        assert any("User Analysis Error" in result["error"] for result in results)
        assert any("Business Analysis Error" in result["error"] for result in results)

def test_main_error(runner, tmp_path):
    """Test command execution with error."""
    output_file = tmp_path / "analysis.md"
    
    with patch("main.run_analysis", new_callable=AsyncMock) as mock_run_analysis:
        mock_run_analysis.side_effect = Exception("Test error")
        
        result = runner.invoke(app, [
            "test-service",
            "--api-key", "test-key",
            "--url", "http://test.com",
            "--output", str(output_file)
        ])
        
        assert result.exit_code != 0
        assert "Test error" in result.output 