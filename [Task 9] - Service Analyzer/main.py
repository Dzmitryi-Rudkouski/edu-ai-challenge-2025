import typer
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
import os
import asyncio
from dotenv import load_dotenv
from analyzers.business_analyzer import BusinessAnalyzer
from analyzers.technical_analyzer import TechnicalAnalyzer
from analyzers.user_analyzer import UserAnalyzer
from analyzers.base_analyzer import APIError, APIKeyError, APIRequestError, APIRateLimitError

# Load environment variables
load_dotenv()

app = typer.Typer(
    name="service-analyzer",
    help="Анализ веб-сервисов по названию или описанию с генерацией markdown-отчета",
    add_completion=False
)
console = Console()

def save_report(content: str, output_file: Path) -> None:
    """Save analysis report to file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Add YAML front matter
    report = f"""---
title: Service Analysis
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

{content}
"""
    
    output_file.write_text(report, encoding='utf-8')

async def run_analysis(
    service_name: str,
    api_key: str,
    url: Optional[str] = None,
    description: Optional[str] = None,
    no_preview: bool = False
) -> dict:
    """Run analysis using all analyzers."""
    analyzers = [
        BusinessAnalyzer(service_name, url, api_key, description),
        TechnicalAnalyzer(service_name, url, api_key, description),
        UserAnalyzer(service_name, url, api_key, description)
    ]
    
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for analyzer in analyzers:
            analyzer_type = analyzer.__class__.__name__
            task = progress.add_task(f"Запуск {analyzer_type}...", total=None)
            
            try:
                async with analyzer:  # Use async context manager
                    result = await analyzer.analyze()
                    results.append(result)
                    progress.update(task, description=f"Завершен {analyzer_type}")
            except APIKeyError as e:
                progress.stop()
                console.print(f"[bold red]Ошибка API ключа: {str(e)}[/bold red]")
                raise typer.Exit(1)
            except APIRateLimitError as e:
                progress.stop()
                console.print(f"[bold yellow]Превышен лимит запросов: {str(e)}[/bold yellow]")
                console.print("Попробуйте позже или используйте другой API ключ.")
                raise typer.Exit(1)
            except APIRequestError as e:
                results.append({
                    "error": f"Ошибка во время анализа {analyzer_type}: {str(e)}",
                    "service_info": {
                        "service_name": service_name,
                        "service_url": url,
                        "description": description
                    },
                    "analysis": {},
                    "markdown": f"## Ошибка в {analyzer_type}\n\n{str(e)}"
                })
                progress.update(task, description=f"Ошибка в {analyzer_type}")
            except Exception as e:
                results.append({
                    "error": f"Неожиданная ошибка во время анализа {analyzer_type}: {str(e)}",
                    "service_info": {
                        "service_name": service_name,
                        "service_url": url,
                        "description": description
                    },
                    "analysis": {},
                    "markdown": f"## Неожиданная ошибка в {analyzer_type}\n\n{str(e)}"
                })
                progress.update(task, description=f"Ошибка в {analyzer_type}")
    
    return results

@app.command()
def main(
    name: str = typer.Argument(..., help="Название сервиса (например, 'Spotify', 'Notion')"),
    api_key: str = typer.Option(..., envvar="OPENAI_API_KEY", help="OpenAI API ключ"),
    url: Optional[str] = typer.Option(None, help="URL сервиса (необязательно)"),
    description: Optional[str] = typer.Option(None, help="Описание сервиса или необработанный текст"),
    output: Path = typer.Option(Path("reports") / "analysis.md", help="Путь для сохранения отчета"),
    no_preview: bool = typer.Option(False, help="Отключить предварительный просмотр отчета")
) -> None:
    """Анализ веб-сервиса по названию или описанию."""
    try:
        # Validate API key
        if not api_key:
            console.print("[bold red]Ошибка: Требуется OpenAI API ключ[/bold red]")
            console.print("Укажите API ключ через --api-key или установите переменную окружения OPENAI_API_KEY.")
            raise typer.Exit(1)
        
        # Validate input - either name or description must be provided
        if not name and not description:
            console.print("[bold red]Ошибка: Необходимо указать название сервиса или описание[/bold red]")
            console.print("Примеры использования:")
            console.print("  python main.py 'Spotify'")
            console.print("  python main.py 'Новый сервис' --description 'Платформа для создания онлайн-курсов'")
            raise typer.Exit(1)
        
        # Run analysis
        results = asyncio.run(run_analysis(name, api_key, url, description, no_preview))
        
        # Generate report
        report = f"# Анализ сервиса: {name}\n\n"
        
        for result in results:
            if "error" in result:
                report += f"\n## Ошибка анализа\n\n[bold red]{result['error']}[/bold red]"
            else:
                report += f"\n{result.get('markdown', '')}\n"
        
        report += f"\n---\n*Отчет сгенерирован автоматически с помощью Service Analyzer*\n*Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        # Save report
        save_report(report, output)
        
        if not no_preview:
            console.print("\nПредварительный просмотр отчета:")
            console.print(Markdown(report))
        
        console.print(f"\nОтчет сохранен в: {output}")
        
    except APIKeyError as e:
        console.print(f"[bold red]Ошибка API ключа: {str(e)}[/bold red]")
        console.print("Проверьте ваш API ключ и попробуйте снова.")
        raise typer.Exit(1)
    except APIRateLimitError as e:
        console.print(f"[bold yellow]Превышен лимит запросов: {str(e)}[/bold yellow]")
        console.print("Попробуйте позже или используйте другой API ключ.")
        raise typer.Exit(1)
    except APIRequestError as e:
        console.print(f"[bold red]Ошибка API запроса: {str(e)}[/bold red]")
        console.print("Проверьте подключение к интернету и попробуйте снова.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Неожиданная ошибка: {str(e)}[/bold red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 