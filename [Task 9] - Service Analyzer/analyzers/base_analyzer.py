from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, TypedDict, NotRequired
from dataclasses import dataclass, field
from enum import Enum
import openai
import os
import json
import aiohttp
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup
import re
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    TECHNICAL = "technical"
    USER = "user"
    BUSINESS = "business"

class APIError(Exception):
    """Base class for API-related errors."""
    pass

class APIKeyError(APIError):
    """Raised when API key is invalid or missing."""
    pass

class APIRequestError(APIError):
    """Raised when API request fails."""
    pass

class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass

@dataclass
class ServiceMetadata:
    """Metadata about the service being analyzed."""
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class WebMetadata:
    """Web-specific metadata about the service."""
    status_code: int
    headers: Dict[str, str]
    security_headers: Dict[str, str]
    technologies: Dict[str, List[str]] = field(default_factory=dict)
    response_time: Optional[float] = None

@dataclass
class AnalysisResult:
    """Base class for analysis results."""
    service_info: ServiceMetadata
    analysis_type: AnalysisType
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

class TechnicalAnalysisResult(AnalysisResult):
    """Technical analysis specific results."""
    architecture: Optional[str] = None
    technical_requirements: List[str] = field(default_factory=list)
    technical_risks: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    scalability: Dict[str, Any] = field(default_factory=dict)
    availability: Optional[Dict[str, Any]] = None

class UserAnalysisResult(AnalysisResult):
    """User experience analysis specific results."""
    user_scenarios: List[str] = field(default_factory=list)
    ux_issues: List[str] = field(default_factory=list)
    interface_requirements: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    improvement_recommendations: List[str] = field(default_factory=list)

class BusinessAnalysisResult(AnalysisResult):
    """Business analysis specific results."""
    business_model: Dict[str, Any] = field(default_factory=dict)
    target_audience: Dict[str, Any] = field(default_factory=dict)
    market_analysis: Dict[str, Any] = field(default_factory=dict)
    competitors: List[Dict[str, Any]] = field(default_factory=list)
    monetization_strategies: List[str] = field(default_factory=list)
    growth_potential: Dict[str, Any] = field(default_factory=dict)

class AnalysisResponse(TypedDict):
    """Type definition for AI analysis response."""
    service_info: Dict[str, Any]
    analysis: Dict[str, Any]
    markdown: str
    error: NotRequired[str]

class BaseAnalyzer(ABC):
    """Base class for all service analyzers."""
    
    # Maximum number of retries for API calls
    MAX_RETRIES = 3
    
    # Maximum tokens for API response
    MAX_TOKENS = 2000
    
    # API model to use
    API_MODEL = "gpt-4-turbo-preview"
    
    # Примеры анализа для few-shot обучения
    EXAMPLES = {
        AnalysisType.BUSINESS: [
            {
                "input": "Платформа для создания и монетизации онлайн-курсов, основанная в 2020 году",
                "output": {
                    "history": {
                        "founded_year": "2020",
                        "key_milestones": [
                            "Запуск платформы с базовым функционалом",
                            "Внедрение системы монетизации в 2021",
                            "Расширение на международные рынки в 2022"
                        ]
                    },
                    "target_audience": {
                        "primary": "Создатели контента и преподаватели",
                        "secondary": "Студенты и обучающиеся",
                        "demographics": "25-45 лет, технически подкованные"
                    },
                    "key_features": [
                        "Создание и публикация курсов",
                        "Система монетизации и подписок",
                        "Инструменты для интерактивного обучения"
                    ],
                    "unique_advantages": [
                        "Простая система монетизации",
                        "Встроенные инструменты для создания контента",
                        "Гибкая система подписок"
                    ],
                    "business_model": {
                        "revenue_streams": [
                            "Комиссия с продаж курсов (20%)",
                            "Премиум-подписка для создателей",
                            "Корпоративные решения"
                        ],
                        "pricing_strategy": "Freemium with premium features"
                    },
                    "perceived_strengths": [
                        "Удобный интерфейс для создателей",
                        "Гибкая система монетизации",
                        "Качественная поддержка"
                    ],
                    "perceived_weaknesses": [
                        "Ограниченные инструменты аналитики",
                        "Высокая комиссия",
                        "Сложность интеграции с внешними системами"
                    ]
                }
            }
        ],
        AnalysisType.TECHNICAL: [
            {
                "input": "Облачное хранилище с шифрованием и синхронизацией, использующее современные технологии",
                "output": {
                    "tech_stack": {
                        "frontend": ["React", "TypeScript", "Material-UI"],
                        "backend": ["Node.js", "Python", "PostgreSQL"],
                        "infrastructure": ["AWS", "Docker", "Kubernetes"],
                        "security": ["End-to-end encryption", "2FA", "OAuth2"]
                    },
                    "architecture": "Микросервисная архитектура с распределенным хранением данных",
                    "technical_requirements": [
                        "Высокая доступность (99.9%)",
                        "Шифрование данных",
                        "Быстрая синхронизация",
                        "Масштабируемость"
                    ],
                    "technical_risks": [
                        "Зависимость от облачных провайдеров",
                        "Риски безопасности данных",
                        "Сложность синхронизации"
                    ],
                    "integrations": [
                        "API для мобильных приложений",
                        "Интеграция с популярными облачными сервисами",
                        "WebDAV поддержка"
                    ],
                    "scalability": {
                        "approach": "Горизонтальное масштабирование",
                        "components": ["Кэширование", "CDN", "Балансировка нагрузки"]
                    }
                }
            }
        ],
        AnalysisType.USER: [
            {
                "input": "Мобильное приложение для заказа еды с доставкой, фокусирующееся на удобстве пользователей",
                "output": {
                    "user_scenarios": [
                        "Поиск ресторанов и просмотр меню",
                        "Оформление и отслеживание заказа",
                        "Управление избранными и историей заказов"
                    ],
                    "ux_issues": [
                        "Сложность навигации по меню",
                        "Неудобный процесс оплаты",
                        "Отсутствие фильтров по диетическим ограничениям"
                    ],
                    "interface_requirements": [
                        "Интуитивная навигация",
                        "Быстрый доступ к корзине",
                        "Понятный статус заказа",
                        "Удобный поиск ресторанов"
                    ],
                    "success_metrics": [
                        "Время до первого заказа",
                        "Частота повторных заказов",
                        "Оценка пользователей",
                        "Конверсия в покупку"
                    ],
                    "improvement_recommendations": [
                        "Упростить процесс оплаты",
                        "Добавить фильтры в меню",
                        "Улучшить систему уведомлений",
                        "Внедрить программу лояльности"
                    ]
                }
            }
        ]
    }

    def __init__(
        self,
        service_name: str,
        service_url: Optional[str] = None,
        api_key: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Initialize the analyzer.
        
        Args:
            service_name: Name of the service to analyze
            service_url: URL of the service (optional)
            api_key: OpenAI API key (optional)
            description: Service description (optional)
        """
        self.service_metadata = ServiceMetadata(
            name=service_name,
            url=service_url,
            description=description
        )
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client: Optional[AsyncOpenAI] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            raise APIKeyError("OpenAI API key not provided")
        
        try:
            self._client = AsyncOpenAI(api_key=self.api_key)
        except Exception as e:
            raise APIKeyError(f"Failed to initialize OpenAI client: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self._session

    def _get_system_prompt(self, analysis_type: AnalysisType) -> str:
        """Возвращает системный промпт с контекстом и примерами."""
        base_prompt = """Ты - эксперт по анализу сервисов и продуктов. Твоя задача - проанализировать описание сервиса и предоставить структурированный анализ НА РУССКОМ ЯЗЫКЕ.
Используй свой опыт и знания для:
1. Выявления неявной информации из контекста
2. Применения лучших практик в отрасли
3. Учета современных трендов
4. Предоставления конкретных рекомендаций
5. Определения истории и этапов развития
6. Выявления восприятия сильных и слабых сторон

ВАЖНО: Все ответы должны быть на русском языке!

Вот пример анализа:"""

        # Добавляем пример для конкретного типа анализа
        example = self.EXAMPLES[analysis_type][0]
        example_str = f"""
Входные данные: {example['input']}
Результат анализа: {json.dumps(example['output'], ensure_ascii=False, indent=2)}

Теперь проанализируй предоставленный сервис в том же формате, учитывая специфику {analysis_type.value} анализа. ВСЕ РЕЗУЛЬТАТЫ ДОЛЖНЫ БЫТЬ НА РУССКОМ ЯЗЫКЕ."""

        # Добавляем специфические инструкции для каждого типа анализа
        type_specific = {
            AnalysisType.BUSINESS: """
Для бизнес-анализа обрати особое внимание на:
- История и этапы развития (год основания, ключевые события)
- Целевая аудитория (основные сегменты, демография)
- Ключевые функции (2-4 основных функционала)
- Уникальные торговые преимущества
- Бизнес-модель и источники дохода
- Восприятие сильных и слабых сторон

Все результаты должны быть на русском языке!""",
            
            AnalysisType.TECHNICAL: """
Для технического анализа рассмотри:
- Технологический стек (фронтенд, бэкенд, инфраструктура)
- Архитектура и масштабируемость
- Технические требования и ограничения
- Потенциальные технические риски
- Необходимые интеграции
- Безопасность и производительность

Все результаты должны быть на русском языке!""",
            
            AnalysisType.USER: """
Для пользовательского анализа сфокусируйся на:
- Ключевые пользовательские сценарии
- Потенциальные проблемы UX
- Требования к интерфейсу
- Метрики успеха
- Рекомендации по улучшению
- Восприятие пользователями

Все результаты должны быть на русском языке!"""
        }

        return base_prompt + example_str + type_specific[analysis_type]

    def _get_user_prompt(self, description: str, analysis_type: AnalysisType) -> str:
        """Формирует пользовательский промпт с контекстом."""
        context = f"""Проанализируй следующий сервис:

Название: {self.service_metadata.name}
Описание: {description}
URL: {self.service_metadata.url or 'Не указан'}

Дополнительный контекст:
- Тип анализа: {analysis_type.value}
- Цель: Получить структурированный анализ для принятия решений
- Формат: JSON с ключами, соответствующими аспектам анализа

Проведи глубокий анализ, учитывая:
1. Явно указанную информацию
2. Неявные детали из контекста
3. Отраслевые тренды и лучшие практики
4. Потенциальные риски и возможности

ВАЖНО: Все результаты анализа должны быть на русском языке!

Верни структурированный ответ в формате JSON на русском языке."""

        return context

    def _validate_analysis_result(self, result: Dict[str, Any]) -> bool:
        """Validate analysis result structure."""
        required_fields = {"service_info", "analysis", "markdown"}
        return all(field in result for field in required_fields)

    def _create_error_result(self, error_msg: str) -> AnalysisResponse:
        """Create standardized error response."""
        return {
            "error": error_msg,
            "service_info": {
                "service_name": self.service_metadata.name,
                "service_url": self.service_metadata.url,
                "description": self.service_metadata.description
            },
            "analysis": {},
            "markdown": f"## Error\n\n{error_msg}"
        }

    async def analyze(self) -> AnalysisResponse:
        """Perform service analysis."""
        try:
            async with self:
                if not self.service_metadata.description and self.service_metadata.url:
                    self.service_metadata.description = await self._get_service_description()
                
                service_info = await self._enrich_service_info()
                analysis_results = await self._perform_specific_analysis(service_info)
                
                if not self._validate_analysis_result(analysis_results):
                    return self._create_error_result("Invalid analysis result structure")
                
                markdown = self.generate_markdown(analysis_results["analysis"])
                analysis_results["markdown"] = markdown
                
                return analysis_results
            
        except Exception as e:
            error_msg = f"Error during analysis: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_result(error_msg)

    async def _get_service_description(self) -> str:
        """
        Get service description from URL.
        
        Returns:
            Service description as string
        """
        if not self.service_metadata.url:
            return f"Service {self.service_metadata.name}"
        
        try:
            session = await self._get_session()
            async with session.get(self.service_metadata.url, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Try to get meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc and meta_desc.get('content'):
                        return meta_desc['content']
                    
                    # Try to get first paragraph
                    first_p = soup.find('p')
                    if first_p and first_p.text.strip():
                        return first_p.text.strip()
                    
                    # Fallback to title
                    title = soup.find('title')
                    if title and title.text.strip():
                        return title.text.strip()
            
            return f"Service {self.service_metadata.name} at {self.service_metadata.url}"
            
        except asyncio.TimeoutError:
            self.logger.warning("Timeout while getting service description")
            return f"Service {self.service_metadata.name} at {self.service_metadata.url}"
        except Exception as e:
            self.logger.warning(f"Error getting service description: {str(e)}")
            return f"Service {self.service_metadata.name} at {self.service_metadata.url}"

    async def _enrich_service_info(self) -> Dict[str, Any]:
        """Enrich service information with metadata."""
        service_info = {
            "service_name": self.service_metadata.name,
            "service_url": self.service_metadata.url,
            "description": self.service_metadata.description,
            "additional_data": {}
        }
        
        if self.service_metadata.url:
            try:
                session = await self._get_session()
                async with session.get(self.service_metadata.url, timeout=30) as response:
                    if response.status == 200:
                        web_metadata = WebMetadata(
                            status_code=response.status,
                            headers=dict(response.headers),
                            security_headers={
                                header: value
                                for header, value in response.headers.items()
                                if header.lower().startswith(('x-', 'strict-', 'content-'))
                            }
                        )
                        
                        html = await response.text()
                        web_metadata.technologies = await self._detect_technologies(html, response.headers)
                        service_info["additional_data"]["web_metadata"] = web_metadata.__dict__
            
            except asyncio.TimeoutError:
                self.logger.warning("Timeout while enriching service info")
            except Exception as e:
                self.logger.warning(f"Error enriching service info: {str(e)}")
        
        return service_info

    async def _detect_technologies(self, html: str, headers: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Detect technologies used by the service based on HTML content and headers.
        
        Args:
            html: HTML content of the page
            headers: HTTP response headers
            
        Returns:
            Dictionary containing detected technologies
        """
        technologies = {
            "frontend": [],
            "backend": [],
            "frameworks": [],
            "libraries": [],
            "tools": []
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check for common frontend frameworks
            if soup.find(attrs={"data-reactroot": True}):
                technologies["frontend"].append("React")
            if soup.find(attrs={"ng-version": True}):
                technologies["frontend"].append("Angular")
            if soup.find(attrs={"data-vue-app": True}):
                technologies["frontend"].append("Vue.js")
            
            # Check for common backend technologies
            server = headers.get("Server", "").lower()
            if "nginx" in server:
                technologies["backend"].append("Nginx")
            if "apache" in server:
                technologies["backend"].append("Apache")
            if "node" in server:
                technologies["backend"].append("Node.js")
            
            # Check for common libraries
            scripts = soup.find_all("script", src=True)
            for script in scripts:
                src = script["src"].lower()
                if "jquery" in src:
                    technologies["libraries"].append("jQuery")
                if "bootstrap" in src:
                    technologies["libraries"].append("Bootstrap")
                if "font-awesome" in src:
                    technologies["libraries"].append("Font Awesome")
            
            # Check for common tools
            if "google-analytics" in html.lower():
                technologies["tools"].append("Google Analytics")
            if "gtm" in html.lower():
                technologies["tools"].append("Google Tag Manager")
            if "hotjar" in html.lower():
                technologies["tools"].append("Hotjar")
        
        except Exception as e:
            self.logger.warning(f"Error detecting technologies: {str(e)}")
        
        return technologies

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIRateLimitError, APIRequestError))
    )
    async def _call_ai_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call OpenAI API with retry logic and proper error handling.
        
        Args:
            prompt: Analysis prompt
            
        Returns:
            API response as dictionary
            
        Raises:
            APIKeyError: If API key is invalid
            APIRateLimitError: If rate limit is exceeded
            APIRequestError: If request fails
        """
        if not self.api_key:
            raise APIKeyError("OpenAI API key not provided")
        
        try:
            # Prepare request
            messages = [
                {"role": "system", "content": "You are a professional service analyzer. Provide detailed analysis in English."},
                {"role": "user", "content": prompt}
            ]
            
            # Make API call
            response = await self._client.chat.completions.create(
                model=self.API_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=self.MAX_TOKENS,
                timeout=30  # 30 seconds timeout
            )
            
            # Extract and return content
            return response.choices[0].message.content
            
        except openai.RateLimitError as e:
            self.logger.warning(f"Rate limit exceeded: {str(e)}")
            raise APIRateLimitError(f"OpenAI API rate limit exceeded: {str(e)}")
            
        except openai.AuthenticationError as e:
            self.logger.error(f"Authentication error: {str(e)}")
            raise APIKeyError(f"Invalid OpenAI API key: {str(e)}")
            
        except openai.APIError as e:
            self.logger.error(f"API error: {str(e)}")
            raise APIRequestError(f"OpenAI API request failed: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error during API call: {str(e)}")
            raise APIRequestError(f"Unexpected error during API call: {str(e)}")

    async def _analyze_with_ai(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze service using AI with improved error handling.
        
        Args:
            service_info: Dictionary containing service information
            
        Returns:
            Dictionary containing AI analysis results
        """
        if not self.api_key:
            return {"error": "OpenAI API key not provided"}
        
        try:
            # Prepare prompt
            prompt = self._prepare_analysis_prompt(service_info)
            
            # Call OpenAI API with retry logic
            response = await self._call_ai_api(prompt)
            
            # Parse response
            if isinstance(response, dict) and "error" in response:
                return response
            
            return self._parse_ai_response(response)
            
        except APIKeyError as e:
            self.logger.error(f"API key error: {str(e)}")
            return {"error": f"API key error: {str(e)}"}
            
        except APIRateLimitError as e:
            self.logger.error(f"Rate limit error: {str(e)}")
            return {"error": f"Rate limit exceeded. Please try again later: {str(e)}"}
            
        except APIRequestError as e:
            self.logger.error(f"API request error: {str(e)}")
            return {"error": f"API request failed: {str(e)}"}
            
        except Exception as e:
            error_msg = f"Error during AI analysis: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}

    async def analyze_description(self, description: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """
        Analyze service description using AI.
        
        Args:
            description: Service description to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Dictionary containing analysis results
        """
        service_info = {
            "service_name": self.service_metadata.name,
            "service_url": self.service_metadata.url,
            "description": description,
            "additional_data": {}
        }
        
        return await self._analyze_with_ai(service_info)

    def _prepare_analysis_prompt(self, service_info: Dict[str, Any]) -> str:
        """
        Prepare prompt for AI analysis.
        
        Args:
            service_info: Dictionary containing service information
            
        Returns:
            Formatted prompt string
        """
        raise NotImplementedError("Subclasses must implement _prepare_analysis_prompt")

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI response into structured format with improved error handling.
        
        Args:
            response: Raw AI response
            
        Returns:
            Parsed response as dictionary
        """
        try:
            # Try to parse as JSON first
            if isinstance(response, str):
                try:
                    # Clean the response string
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:]
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()
                    
                    return json.loads(cleaned_response)
                except json.JSONDecodeError:
                    self.logger.warning("Response is not valid JSON, attempting to parse as structured text")
            
            # If not JSON, try to extract structured information
            result = {}
            current_section = None
            
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Handle markdown headers
                if line.startswith('#'):
                    current_section = line.lstrip('#').strip().lower().replace(' ', '_')
                    result[current_section] = []
                # Handle bullet points
                elif current_section and line.startswith('-'):
                    if not isinstance(result[current_section], list):
                        result[current_section] = []
                    result[current_section].append(line.lstrip('-').strip())
                # Handle key-value pairs
                elif current_section and ':' in line:
                    key, value = line.split(':', 1)
                    if not isinstance(result[current_section], dict):
                        result[current_section] = {}
                    result[current_section][key.strip()] = value.strip()
            
            if not result:
                raise ValueError("Could not parse response into structured format")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {str(e)}")
            return {"error": f"Error parsing AI response: {str(e)}"}

    @abstractmethod
    async def _perform_specific_analysis(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform specific analysis based on analyzer type.
        
        Args:
            service_info: Dictionary containing service information
            
        Returns:
            Analysis results as dictionary
        """
        pass

    @abstractmethod
    def generate_markdown(self, analysis_results: Dict[str, Any]) -> str:
        """
        Generate markdown report from analysis results.
        
        Args:
            analysis_results: Dictionary containing analysis results
            
        Returns:
            Markdown report as string
        """
        pass 