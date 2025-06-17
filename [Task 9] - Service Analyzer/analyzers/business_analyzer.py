from .base_analyzer import BaseAnalyzer, AnalysisType, BusinessAnalysisResult, AnalysisResponse
from typing import Dict, Any, List
import json
import asyncio

class BusinessAnalyzer(BaseAnalyzer):
    """Analyzer for business aspects of the service."""
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Performs business analysis of the service, including:
        - Business model
        - Target audience
        - Market analysis
        - Competitors
        - Monetization strategies
        - Growth potential
        """
        results = {}
        
        # Analyze service description
        description = self._get_service_description()
        analysis_results = await self.analyze_description(description, AnalysisType.BUSINESS)
        
        if "error" not in analysis_results:
            results.update({
                "business_model": analysis_results.get("business_model", "Not specified"),
                "target_audience": analysis_results.get("target_audience", []),
                "market_analysis": analysis_results.get("market_analysis", "Not specified"),
                "competitors": analysis_results.get("competitors", []),
                "monetization": analysis_results.get("monetization", []),
                "growth_potential": analysis_results.get("growth_potential", "Not specified")
            })
        else:
            results.update({
                "business_model": "Could not be determined",
                "target_audience": [],
                "market_analysis": "Could not be determined",
                "competitors": [],
                "monetization": [],
                "growth_potential": "Could not be determined",
                "error": analysis_results["error"]
            })
        
        return results
    
    def _get_service_description(self) -> str:
        """Formulates service description for business analysis."""
        description = f"Business analysis of service {self.service_metadata.name}"
        
        if self.service_metadata.url:
            description += f" (URL: {self.service_metadata.url})"
        
        if self.service_metadata.description:
            description += f"\n\nService description: {self.service_metadata.description}"
        
        return description
    
    def generate_markdown(self, analysis_results: Dict[str, Any]) -> str:
        """Generate markdown report for business analysis."""
        # Создаем объект BusinessAnalysisResult с правильными параметрами
        result = BusinessAnalysisResult(
            service_info=analysis_results.get("service_info", self.service_metadata),
            analysis_type=analysis_results.get("analysis_type", AnalysisType.BUSINESS),
            error=analysis_results.get("error"),
            raw_data=analysis_results.get("raw_data", {})
        )
        
        # Устанавливаем специфичные для бизнес-анализа поля
        result.business_model = analysis_results.get("business_model", {})
        result.target_audience = analysis_results.get("target_audience", {})
        result.market_analysis = analysis_results.get("market_analysis", {})
        result.competitors = analysis_results.get("competitors", [])
        result.monetization_strategies = analysis_results.get("monetization_strategies", [])
        result.growth_potential = analysis_results.get("growth_potential", {})
        
        report = f"""## Бизнес-анализ сервиса {self.service_metadata.name}

### Краткая история
{self._format_dict(analysis_results.get("history", {}))}

### Целевая аудитория
{self._format_dict(result.target_audience)}

### Основные функции
{self._format_list(analysis_results.get("key_features", []))}

### Уникальные торговые преимущества
{self._format_list(analysis_results.get("unique_advantages", []))}

### Бизнес-модель
{self._format_dict(result.business_model)}

### Информация о технологическом стеке
{self._format_dict(analysis_results.get("tech_stack", {}))}

### Восприятие сильных сторон
{self._format_list(analysis_results.get("perceived_strengths", []))}

### Восприятие слабых сторон
{self._format_list(analysis_results.get("perceived_weaknesses", []))}
"""
        
        # Add market analysis if available
        if "market_analysis" in result.raw_data:
            market = result.raw_data["market_analysis"]
            if "error" not in market:
                report += "\n### Дополнительный анализ рынка\n"
                
                if "market_size" in market:
                    report += "\n#### Размер рынка\n"
                    report += self._format_dict(market["market_size"])
                
                if "market_trends" in market:
                    report += "\n#### Тренды рынка\n"
                    report += self._format_list(market["market_trends"])
                
                if "competitive_landscape" in market:
                    report += "\n#### Конкурентная среда\n"
                    report += self._format_dict(market["competitive_landscape"])
                
                if "growth_opportunities" in market:
                    report += "\n#### Возможности роста\n"
                    report += self._format_list(market["growth_opportunities"])
                
                if "risks" in market:
                    report += "\n#### Риски\n"
                    report += self._format_list(market["risks"])
            else:
                report += f"\n> ⚠️ **Примечание**: Ошибка в анализе рынка: {market['error']}"
        
        if result.error:
            report += f"\n> ⚠️ **Примечание**: {result.error}"
        
        return report

    def _format_list(self, items: List[str]) -> str:
        """Format list items for markdown."""
        if not items:
            return "Not specified"
        return "\n".join(f"- {item}" for item in items)

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary items for markdown."""
        if not data:
            return "Not specified"
        return "\n".join(f"- **{key}**: {value}" for key, value in data.items())

    def _format_list_of_dicts(self, items: List[Dict[str, Any]]) -> str:
        """Format list of dictionaries for markdown."""
        if not items:
            return "Not specified"
        
        result = []
        for i, item in enumerate(items, 1):
            result.append(f"\n#### Competitor {i}")
            result.append(self._format_dict(item))
        
        return "\n".join(result)
    
    def _prepare_analysis_prompt(self, service_info: Dict[str, Any]) -> str:
        """
        Prepare prompt for business analysis.
        
        Args:
            service_info: Dictionary containing service information
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Проанализируй следующий веб-сервис с бизнес-точки зрения.
        Сфокусируйся на выявлении:
        1. Краткой истории (год основания, важные этапы развития)
        2. Целевой аудитории (основные сегменты пользователей)
        3. Основных функций (2-4 ключевых функционала)
        4. Уникальных торговых преимуществ (ключевые отличия от конкурентов)
        5. Бизнес-модели (как сервис зарабатывает деньги)
        6. Информации о технологическом стеке (любые намеки на используемые технологии)
        7. Восприятия сильных сторон (положительные стороны или выделяющиеся особенности)
        8. Восприятия слабых сторон (упомянутые недостатки или ограничения)

        Информация о сервисе:
        Название: {service_info['service_name']}
        URL: {service_info['service_url']}
        Описание: {service_info['description']}

        Дополнительные данные:
        {json.dumps(service_info.get('additional_data', {}), indent=2, ensure_ascii=False)}

        Верни анализ в формате JSON объекта со следующей структурой:
        {{
            "history": {{
                "founded_year": "год основания",
                "key_milestones": ["важное событие 1", "важное событие 2", ...]
            }},
            "target_audience": {{
                "primary": "основная аудитория",
                "secondary": "вторичная аудитория",
                "demographics": "демографические характеристики"
            }},
            "key_features": ["функция 1", "функция 2", "функция 3", "функция 4"],
            "unique_advantages": ["преимущество 1", "преимущество 2", ...],
            "business_model": {{
                "revenue_streams": ["источник дохода 1", "источник дохода 2", ...],
                "pricing_strategy": "стратегия ценообразования"
            }},
            "tech_stack": {{
                "frontend": ["технология 1", "технология 2"],
                "backend": ["технология 1", "технология 2"],
                "infrastructure": ["технология 1", "технология 2"]
            }},
            "perceived_strengths": ["сильная сторона 1", "сильная сторона 2", ...],
            "perceived_weaknesses": ["слабая сторона 1", "слабая сторона 2", ...]
        }}

        ВАЖНО: Все результаты должны быть на русском языке! Предоставь конкретные, практические выводы.
        """
        
        return prompt
    
    async def _perform_specific_analysis(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Perform business analysis of the service."""
        try:
            # Create analysis result
            result = BusinessAnalysisResult(
                service_info=self.service_metadata,
                analysis_type=AnalysisType.BUSINESS
            )
            
            # Analyze service description
            description = self._get_service_description()
            analysis_results = await self.analyze_description(description, AnalysisType.BUSINESS)
            
            if "error" not in analysis_results:
                result.business_model = analysis_results.get("business_model", {})
                result.target_audience = analysis_results.get("target_audience", {})
                result.market_analysis = analysis_results.get("market_analysis", {})
                result.competitors = analysis_results.get("competitors", [])
                result.monetization_strategies = analysis_results.get("monetization_strategies", [])
                result.growth_potential = analysis_results.get("growth_potential", {})
            else:
                result.error = analysis_results["error"]
            
            # Add web metadata if available
            if "web_metadata" in service_info.get("additional_data", {}):
                result.raw_data["web_metadata"] = service_info["additional_data"]["web_metadata"]
            
            # Perform additional market analysis if URL is available
            if self.service_metadata.url:
                market_analysis = await self._analyze_market_aspects(service_info)
                if market_analysis:
                    result.raw_data["market_analysis"] = market_analysis
            
            return {
                "service_info": self.service_metadata,
                "analysis_type": AnalysisType.BUSINESS,
                "business_model": result.business_model,
                "target_audience": result.target_audience,
                "market_analysis": result.market_analysis,
                "competitors": result.competitors,
                "monetization_strategies": result.monetization_strategies,
                "growth_potential": result.growth_potential,
                "error": result.error,
                "raw_data": result.raw_data
            }
            
        except Exception as e:
            return self._create_error_result(f"Error during business analysis: {str(e)}")

    async def _analyze_market_aspects(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze additional market aspects of the service."""
        try:
            # Prepare market analysis prompt
            prompt = self._prepare_market_analysis_prompt(service_info)
            
            # Get AI analysis
            market_analysis = await self._analyze_with_ai(prompt)
            
            if "error" in market_analysis:
                return {"error": market_analysis["error"]}
            
            return {
                "market_size": market_analysis.get("market_size", {}),
                "market_trends": market_analysis.get("market_trends", []),
                "competitive_landscape": market_analysis.get("competitive_landscape", {}),
                "growth_opportunities": market_analysis.get("growth_opportunities", []),
                "risks": market_analysis.get("risks", [])
            }
            
        except Exception as e:
            self.logger.warning(f"Error during market analysis: {str(e)}")
            return {"error": str(e)}

    def _prepare_market_analysis_prompt(self, service_info: Dict[str, Any]) -> str:
        """Prepare prompt for market analysis."""
        return f"""Analyze the market aspects of the service:

Service: {self.service_metadata.name}
URL: {self.service_metadata.url}
Description: {self.service_metadata.description}

Focus on:
1. Market size and potential
2. Current market trends
3. Competitive landscape
4. Growth opportunities
5. Potential risks and challenges

Provide a structured analysis with specific data points and actionable insights."""

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create a result object for an error."""
        return {
            "service_info": self.service_metadata,
            "analysis_type": AnalysisType.BUSINESS,
            "business_model": {},
            "target_audience": {},
            "market_analysis": {},
            "competitors": [],
            "monetization_strategies": [],
            "growth_potential": {},
            "error": error_message,
            "raw_data": {}
        } 