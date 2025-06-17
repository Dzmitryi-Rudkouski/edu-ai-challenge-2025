from .base_analyzer import BaseAnalyzer, AnalysisType, TechnicalAnalysisResult, AnalysisResponse
from typing import Dict, Any, List, Optional
import requests
import json
import aiohttp
import asyncio

class TechnicalAnalyzer(BaseAnalyzer):
    """Analyzer for technical aspects of the service."""
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Performs technical analysis of the service, including:
        - Architecture
        - Performance
        - Security
        - Scalability
        - Technical risks
        """
        results = {}
        
        # Analyze service description
        description = self._get_service_description()
        analysis_results = await self.analyze_description(description, AnalysisType.TECHNICAL)
        
        if "error" not in analysis_results:
            results.update({
                "architecture": analysis_results.get("architecture", "Not specified"),
                "technical_requirements": analysis_results.get("technical_requirements", "Not specified"),
                "technical_risks": analysis_results.get("technical_risks", "Not specified"),
                "integrations": analysis_results.get("integrations", "Not specified"),
                "scalability": analysis_results.get("scalability", "Not specified")
            })
        else:
            results.update({
                "architecture": "Could not be determined",
                "technical_requirements": "Could not be determined",
                "technical_risks": "Could not be determined",
                "integrations": "Could not be determined",
                "scalability": "Could not be determined",
                "error": analysis_results["error"]
            })
        
        # Check service availability
        if self.service_metadata.url:
            availability = await self._check_availability()
            results["availability"] = availability
        
        return results
    
    def _get_service_description(self) -> str:
        """Formulates service description for technical analysis."""
        description = f"Technical analysis of service {self.service_metadata.name}"
        
        if self.service_metadata.url:
            description += f" (URL: {self.service_metadata.url})"
        
        if self.service_metadata.description:
            description += f"\n\nService description: {self.service_metadata.description}"
        
        return description
    
    async def _check_availability(self) -> Dict[str, Any]:
        """Checks service availability."""
        if not self.service_metadata.url:
            return {"error": "URL not specified"}

        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(self.service_metadata.url, timeout=5) as response:
                    end_time = asyncio.get_event_loop().time()
                    response_time = end_time - start_time

                    return {
                        "is_available": response.status < 400,
                        "status_code": response.status,
                        "response_time": response_time,
                        "headers": dict(response.headers)
                    }
        except asyncio.TimeoutError:
            return {"error": "Request timeout exceeded"}
        except Exception as e:
            return {"error": f"Error checking availability: {str(e)}"}
    
    def generate_markdown(self, analysis_results: Dict[str, Any]) -> str:
        """Generate markdown report for technical analysis."""
        # Создаем объект TechnicalAnalysisResult с правильными параметрами
        result = TechnicalAnalysisResult(
            service_info=analysis_results.get("service_info", self.service_metadata),
            analysis_type=analysis_results.get("analysis_type", AnalysisType.TECHNICAL),
            error=analysis_results.get("error"),
            raw_data=analysis_results.get("raw_data", {})
        )
        
        # Устанавливаем специфичные для технического анализа поля
        result.architecture = analysis_results.get("architecture")
        result.technical_requirements = analysis_results.get("technical_requirements", [])
        result.technical_risks = analysis_results.get("technical_risks", [])
        result.integrations = analysis_results.get("integrations", [])
        result.scalability = analysis_results.get("scalability", {})
        result.availability = analysis_results.get("availability")
        
        report = f"""## Технический анализ сервиса {self.service_metadata.name}

### Архитектура
{result.architecture or "Не указана"}

### Технические требования
{self._format_list(result.technical_requirements)}

### Технические риски
{self._format_list(result.technical_risks)}

### Интеграции
{self._format_list(result.integrations)}

### Масштабируемость
{self._format_dict(result.scalability)}

### Доступность
{self._format_availability(result.availability)}
"""
        
        if result.error:
            report += f"\n> ⚠️ **Примечание**: {result.error}"
        
        return report

    def _format_list(self, items: List[str]) -> str:
        """Format list items for markdown."""
        if not items:
            return "Не указано"
        return "\n".join(f"- {item}" for item in items)

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary items for markdown."""
        if not data:
            return "Не указано"
        return "\n".join(f"- **{key}**: {value}" for key, value in data.items())

    def _format_availability(self, availability: Optional[Dict[str, Any]]) -> str:
        """Format availability information for markdown."""
        if not availability:
            return "Не проверено"
        
        if "error" in availability:
            return f"❌ Сервис недоступен\n- Причина: {availability['error']}"
        
        status = "✅ Доступен" if availability.get("is_available") else "❌ Недоступен"
        result = f"- {status}\n"
        result += f"- Код ответа: {availability.get('status_code', 'N/A')}\n"
        result += f"- Время ответа: {availability.get('response_time', 0):.2f} сек\n"
        
        if "headers" in availability:
            result += "\n#### Заголовки ответа\n"
            for key, value in availability["headers"].items():
                result += f"- {key}: {value}\n"
        
        return result

    async def _perform_specific_analysis(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Perform technical analysis of the service."""
        try:
            # Create analysis result
            result = TechnicalAnalysisResult(
                service_info=self.service_metadata,
                analysis_type=AnalysisType.TECHNICAL
            )
            
            # Analyze service description
            description = self._get_service_description()
            analysis_results = await self.analyze_description(description, AnalysisType.TECHNICAL)
            
            if "error" not in analysis_results:
                result.architecture = analysis_results.get("architecture")
                result.technical_requirements = analysis_results.get("technical_requirements", [])
                result.technical_risks = analysis_results.get("technical_risks", [])
                result.integrations = analysis_results.get("integrations", [])
                result.scalability = analysis_results.get("scalability", {})
            else:
                result.error = analysis_results["error"]
            
            # Check service availability
            if self.service_metadata.url:
                availability = await self._check_availability()
                result.availability = availability
            
            # Add web metadata if available
            if "web_metadata" in service_info.get("additional_data", {}):
                result.raw_data["web_metadata"] = service_info["additional_data"]["web_metadata"]
            
            return {
                "service_info": self.service_metadata,
                "analysis_type": AnalysisType.TECHNICAL,
                "architecture": result.architecture,
                "technical_requirements": result.technical_requirements,
                "technical_risks": result.technical_risks,
                "integrations": result.integrations,
                "scalability": result.scalability,
                "availability": result.availability,
                "error": result.error,
                "raw_data": result.raw_data
            }
            
        except Exception as e:
            return self._create_error_result(f"Error during technical analysis: {str(e)}")

    def _prepare_analysis_prompt(self, service_info: Dict[str, Any]) -> str:
        """
        Prepare prompt for technical analysis.
        
        Args:
            service_info: Dictionary containing service information
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the following web service from a technical perspective.
        Focus on identifying:
        1. Technical architecture and stack
        2. Technical requirements and constraints
        3. Potential technical risks and challenges
        4. Required integrations and APIs
        5. Scalability considerations
        6. Performance and security aspects

        Service Information:
        Name: {service_info['service_name']}
        URL: {service_info['service_url']}
        Description: {service_info['description']}

        Additional Data:
        {json.dumps(service_info.get('additional_data', {}), indent=2)}

        Return the analysis as a JSON object with the following structure:
        {{
            "architecture": "description of the technical architecture",
            "technical_requirements": ["requirement1", "requirement2", ...],
            "technical_risks": ["risk1", "risk2", ...],
            "integrations": ["integration1", "integration2", ...],
            "scalability": "scalability analysis"
        }}

        Ensure all text is in English and provide specific, actionable insights.
        """
        
        return prompt 