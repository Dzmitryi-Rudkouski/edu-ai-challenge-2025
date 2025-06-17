import os
import sys
import pytest

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Фикстуры, которые будут доступны во всех тестах
@pytest.fixture(scope="session")
def test_data_dir():
    """Возвращает путь к директории с тестовыми данными."""
    return os.path.join(project_root, "tests", "data")

@pytest.fixture(scope="session")
def mock_api_key():
    """Возвращает тестовый API ключ."""
    return "test_api_key"

@pytest.fixture(scope="session")
def mock_service_name():
    """Возвращает тестовое имя сервиса."""
    return "TestService"

@pytest.fixture(scope="session")
def mock_service_url():
    """Возвращает тестовый URL сервиса."""
    return "https://test.com"

@pytest.fixture(scope="session")
def mock_service_description():
    """Возвращает тестовое описание сервиса."""
    return "Test service description" 
 