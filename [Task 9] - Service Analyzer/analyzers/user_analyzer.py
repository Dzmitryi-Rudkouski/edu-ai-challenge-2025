from .base_analyzer import BaseAnalyzer, AnalysisType, UserAnalysisResult, AnalysisResponse
from typing import Dict, Any, List
import json
import asyncio

class UserAnalyzer(BaseAnalyzer):
    """Analyzer for user experience aspects of the service."""
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Performs user experience analysis of the service, including:
        - User scenarios
        - UX issues
        - Interface requirements
        - Success metrics
        - Improvement recommendations
        """
        results = {}
        
        # Analyze service description
        description = self._get_service_description()
        analysis_results = await self.analyze_description(description, AnalysisType.USER)
        
        if "error" not in analysis_results:
            results.update({
                "user_scenarios": analysis_results.get("user_scenarios", []),
                "ux_issues": analysis_results.get("ux_issues", []),
                "interface_requirements": analysis_results.get("interface_requirements", []),
                "success_metrics": analysis_results.get("success_metrics", []),
                "improvement_recommendations": analysis_results.get("improvement_recommendations", [])
            })
        else:
            results.update({
                "user_scenarios": [],
                "ux_issues": [],
                "interface_requirements": [],
                "success_metrics": [],
                "improvement_recommendations": [],
                "error": analysis_results["error"]
            })
        
        return results
    
    def _get_service_description(self) -> str:
        """Formulates service description for user experience analysis."""
        description = f"User experience analysis of service {self.service_metadata.name}"
        
        if self.service_metadata.url:
            description += f" (URL: {self.service_metadata.url})"
        
        if self.service_metadata.description:
            description += f"\n\nService description: {self.service_metadata.description}"
        
        return description
    
    def generate_markdown(self, analysis_results: Dict[str, Any]) -> str:
        """Generate markdown report for user experience analysis."""
        # Создаем объект UserAnalysisResult с правильными параметрами
        result = UserAnalysisResult(
            service_info=analysis_results.get("service_info", self.service_metadata),
            analysis_type=analysis_results.get("analysis_type", AnalysisType.USER),
            error=analysis_results.get("error"),
            raw_data=analysis_results.get("raw_data", {})
        )
        
        # Устанавливаем специфичные для пользовательского анализа поля
        result.user_scenarios = analysis_results.get("user_scenarios", [])
        result.ux_issues = analysis_results.get("ux_issues", [])
        result.interface_requirements = analysis_results.get("interface_requirements", [])
        result.success_metrics = analysis_results.get("success_metrics", [])
        result.improvement_recommendations = analysis_results.get("improvement_recommendations", [])
        
        report = f"""## User Experience Analysis of Service {self.service_metadata.name}

### User Scenarios
{self._format_list(result.user_scenarios)}

### UX Issues
{self._format_list(result.ux_issues)}

### Interface Requirements
{self._format_list(result.interface_requirements)}

### Success Metrics
{self._format_list(result.success_metrics)}

### Improvement Recommendations
{self._format_list(result.improvement_recommendations)}
"""
        
        # Add UX analysis if available
        if "ux_analysis" in result.raw_data:
            ux = result.raw_data["ux_analysis"]
            if "error" not in ux:
                report += "\n### Additional UX Analysis\n"
                
                if "accessibility" in ux:
                    report += "\n#### Accessibility\n"
                    report += self._format_dict(ux["accessibility"])
                
                if "usability" in ux:
                    report += "\n#### Usability\n"
                    report += self._format_dict(ux["usability"])
                
                if "user_feedback" in ux:
                    report += "\n#### User Feedback\n"
                    report += self._format_list(ux["user_feedback"])
                
                if "recommendations" in ux:
                    report += "\n#### Additional Recommendations\n"
                    report += self._format_list(ux["recommendations"])
            else:
                report += f"\n> ⚠️ **Note**: Error in UX analysis: {ux['error']}"
        
        if result.error:
            report += f"\n> ⚠️ **Note**: {result.error}"
        
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
    
    def _prepare_analysis_prompt(self, service_info: Dict[str, Any]) -> str:
        """
        Prepare prompt for user experience analysis.
        
        Args:
            service_info: Dictionary containing service information
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the following web service from a user experience perspective.
        Focus on identifying:
        1. User scenarios and use cases
        2. UX issues and pain points
        3. Interface requirements and design considerations
        4. Success metrics and KPIs
        5. Improvement recommendations
        6. User journey optimization

        Service Information:
        Name: {service_info['service_name']}
        URL: {service_info['service_url']}
        Description: {service_info['description']}

        Additional Data:
        {json.dumps(service_info.get('additional_data', {}), indent=2)}

        Return the analysis as a JSON object with the following structure:
        {{
            "user_scenarios": ["scenario1", "scenario2", ...],
            "ux_issues": ["issue1", "issue2", ...],
            "interface_requirements": ["requirement1", "requirement2", ...],
            "success_metrics": ["metric1", "metric2", ...],
            "improvement_recommendations": ["recommendation1", "recommendation2", ...]
        }}

        Ensure all text is in English and provide specific, actionable insights.
        """
        
        return prompt
    
    async def _perform_specific_analysis(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Perform user experience analysis of the service."""
        try:
            # Create analysis result
            result = UserAnalysisResult(
                service_info=self.service_metadata,
                analysis_type=AnalysisType.USER
            )
            
            # Analyze service description
            description = self._get_service_description()
            analysis_results = await self.analyze_description(description, AnalysisType.USER)
            
            if "error" not in analysis_results:
                result.user_scenarios = analysis_results.get("user_scenarios", [])
                result.ux_issues = analysis_results.get("ux_issues", [])
                result.interface_requirements = analysis_results.get("interface_requirements", [])
                result.success_metrics = analysis_results.get("success_metrics", [])
                result.improvement_recommendations = analysis_results.get("improvement_recommendations", [])
            else:
                result.error = analysis_results["error"]
            
            # Add web metadata if available
            if "web_metadata" in service_info.get("additional_data", {}):
                result.raw_data["web_metadata"] = service_info["additional_data"]["web_metadata"]
            
            return {
                "service_info": self.service_metadata,
                "analysis_type": AnalysisType.USER,
                "user_scenarios": result.user_scenarios,
                "ux_issues": result.ux_issues,
                "interface_requirements": result.interface_requirements,
                "success_metrics": result.success_metrics,
                "improvement_recommendations": result.improvement_recommendations,
                "error": result.error,
                "raw_data": result.raw_data
            }
            
        except Exception as e:
            return self._create_error_result(f"Error during user experience analysis: {str(e)}")

    async def _analyze_ux_aspects(self, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze additional UX aspects of the service."""
        try:
            # Prepare UX analysis prompt
            prompt = self._prepare_ux_analysis_prompt(service_info)
            
            # Get AI analysis
            ux_analysis = await self._analyze_with_ai(prompt)
            
            if "error" in ux_analysis:
                return {"error": ux_analysis["error"]}
            
            return {
                "accessibility": ux_analysis.get("accessibility", {}),
                "usability": ux_analysis.get("usability", {}),
                "user_feedback": ux_analysis.get("user_feedback", []),
                "recommendations": ux_analysis.get("recommendations", [])
            }
            
        except Exception as e:
            self.logger.warning(f"Error during UX analysis: {str(e)}")
            return {"error": str(e)}

    def _prepare_ux_analysis_prompt(self, service_info: Dict[str, Any]) -> str:
        """Prepare prompt for UX analysis."""
        return f"""Analyze the user experience aspects of the service:

Service: {self.service_metadata.name}
URL: {self.service_metadata.url}
Description: {self.service_metadata.description}

Focus on:
1. Accessibility (WCAG compliance, mobile responsiveness)
2. Usability (navigation, content organization, user flows)
3. User feedback and satisfaction
4. Specific recommendations for improvement

Provide a structured analysis with specific examples and actionable recommendations."""

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create an error result for user experience analysis."""
        return {
            "service_info": None,
            "analysis": None,
            "markdown": f"Error: {error_message}"
        } 