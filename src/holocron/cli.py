"""Command-line interface for Holocron.

This module provides the Typer-based CLI for Holocron, including:
- transform: Transform documents with adaptive scaffolding
- learn: Interactive learning mode
- review: Spaced repetition review session
- learner: Learner profile management
- domains: List available domains
- gui: Launch the web GUI
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from holocron import __version__
from holocron.config import get_settings
from holocron.core.models import BloomLevel, LearnerProfile
from holocron.core.transformer import ContentTransformer, TransformConfig
from holocron.domains.registry import DomainRegistry

# Ensure domains are loaded
import holocron.domains  # noqa: F401

app = typer.Typer(
    name="holocron",
    help="A generalized skill training platform using evidence-based pedagogical techniques.",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"Holocron v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Holocron: Learn any skill with adaptive, evidence-based training."""
    pass


# =============================================================================
# Domain Commands
# =============================================================================


@app.command("domains")
def list_domains() -> None:
    """List all available skill domains."""
    domains = DomainRegistry.list_domains()

    if not domains:
        console.print("[yellow]No domains registered yet.[/yellow]")
        console.print("Domains will be available after importing domain adapters.")
        return

    table = Table(title="Available Domains")
    table.add_column("Domain ID", style="cyan")
    table.add_column("Display Name", style="green")
    table.add_column("Description")
    table.add_column("File Types", style="dim")

    for domain_id in domains:
        adapter = DomainRegistry.get(domain_id)
        config = adapter.config
        file_types = ", ".join(config.file_extensions[:4])
        if len(config.file_extensions) > 4:
            file_types += "..."
        table.add_row(
            config.domain_id,
            config.display_name,
            config.description,
            file_types,
        )

    console.print(table)


# =============================================================================
# Transform Command
# =============================================================================


@app.command("transform")
def transform(
    input_file: str = typer.Argument(..., help="Input file to transform"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
    domain: str = typer.Option(
        "reading-skills", "--domain", "-d", help="Skill domain to use"
    ),
    learner_name: Optional[str] = typer.Option(
        None, "--learner", "-l", help="Learner profile name"
    ),
    level: Optional[int] = typer.Option(
        None, "--level", help="Force specific scaffold level (1-5)"
    ),
    show_concepts: bool = typer.Option(
        False, "--concepts", "-c", help="Show extracted concepts"
    ),
    show_assessments: bool = typer.Option(
        False, "--assessments", "-a", help="Show generated assessments"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """Transform a document with adaptive scaffolding.

    Extracts concepts, applies pedagogical techniques, and generates
    assessments based on the learner's mastery level.
    """
    # Validate domain
    if not DomainRegistry.is_registered(domain):
        available = ", ".join(DomainRegistry.list_domains())
        console.print(f"[red]Unknown domain: {domain}[/red]")
        console.print(f"Available domains: {available}")
        raise typer.Exit(1)

    # Read input file
    input_path = Path(input_file)
    if not input_path.exists():
        console.print(f"[red]File not found: {input_file}[/red]")
        raise typer.Exit(1)

    try:
        content = input_path.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)

    # Create or get learner profile
    learner = LearnerProfile(
        learner_id=learner_name or "default",
        name=learner_name or "Default Learner",
    )

    # Configure transformation
    config = TransformConfig(
        include_assessments=True,
        scaffold_level_override=level,
        include_inline_support=False,  # No LLM callback yet
    )

    # Create transformer and process
    with console.status("[bold green]Transforming content..."):
        transformer = ContentTransformer(
            domain_id=domain,
            learner=learner,
        )
        result = transformer.transform(content, config)

    # JSON output
    if json_output:
        output_data = {
            "domain": domain,
            "scaffold_level": result.scaffold_level,
            "concepts": [
                {
                    "id": c.concept_id,
                    "name": c.name,
                    "difficulty": c.difficulty_score,
                }
                for c in result.concepts_found
            ],
            "assessments": [
                {
                    "id": a.assessment_id,
                    "concept": a.concept_id,
                    "bloom_level": a.bloom_level.value,
                    "question": a.question,
                }
                for a in result.assessments
            ],
            "metadata": result.metadata,
        }
        if output:
            Path(output).write_text(json.dumps(output_data, indent=2))
            console.print(f"[green]Output written to {output}[/green]")
        else:
            console.print_json(data=output_data)
        return

    # Rich output
    console.print()
    console.print(
        Panel(
            f"[bold]Domain:[/bold] {domain}\n"
            f"[bold]Scaffold Level:[/bold] {result.scaffold_level}/5\n"
            f"[bold]Concepts Found:[/bold] {len(result.concepts_found)}\n"
            f"[bold]Assessments Generated:[/bold] {len(result.assessments)}",
            title="Transform Results",
            border_style="green",
        )
    )

    # Show concepts
    if show_concepts and result.concepts_found:
        console.print()
        table = Table(title="Extracted Concepts")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Difficulty", justify="right")
        table.add_column("Category", style="dim")

        for concept in result.concepts_found[:20]:  # Limit display
            category = concept.domain_data.get("category", "")
            table.add_row(
                concept.concept_id,
                concept.name,
                str(concept.difficulty_score),
                category,
            )

        if len(result.concepts_found) > 20:
            table.add_row("...", f"[dim]+{len(result.concepts_found) - 20} more[/dim]", "", "")

        console.print(table)

    # Show assessments
    if show_assessments and result.assessments:
        console.print()
        console.print("[bold]Sample Assessments:[/bold]")
        for i, assessment in enumerate(result.assessments[:5], 1):
            console.print()
            console.print(
                Panel(
                    f"[bold]Level:[/bold] {assessment.bloom_level.value}\n\n"
                    f"{assessment.question}",
                    title=f"Assessment {i}: {assessment.concept_id}",
                    border_style="blue",
                )
            )

    # Write transformed content
    if output:
        Path(output).write_text(result.transformed_content)
        console.print(f"\n[green]Transformed content written to {output}[/green]")


# =============================================================================
# Analyze Command (new - quick concept extraction)
# =============================================================================


@app.command("analyze")
def analyze(
    input_file: str = typer.Argument(..., help="Input file to analyze"),
    domain: str = typer.Option(
        None, "--domain", "-d", help="Skill domain to use (auto-detect if not specified)"
    ),
    top: int = typer.Option(10, "--top", "-n", help="Number of top concepts to show"),
) -> None:
    """Analyze a file and extract concepts.

    Quick way to see what concepts are in a file without full transformation.
    """
    input_path = Path(input_file)
    if not input_path.exists():
        console.print(f"[red]File not found: {input_file}[/red]")
        raise typer.Exit(1)

    try:
        content = input_path.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)

    # Auto-detect domain based on file extension
    if domain is None:
        ext = input_path.suffix.lower()
        if ext in [".py", ".pyw", ".pyi"]:
            domain = "python-programming"
        else:
            domain = "reading-skills"
        console.print(f"[dim]Auto-detected domain: {domain}[/dim]")

    if not DomainRegistry.is_registered(domain):
        console.print(f"[red]Unknown domain: {domain}[/red]")
        raise typer.Exit(1)

    adapter = DomainRegistry.get(domain)

    with console.status("[bold green]Extracting concepts..."):
        content = adapter.preprocess_content(content)
        concepts = adapter.extract_concepts(content)

    if not concepts:
        console.print("[yellow]No concepts found in this file.[/yellow]")
        return

    # Sort by difficulty descending
    concepts.sort(key=lambda c: c.difficulty_score, reverse=True)

    table = Table(title=f"Top {min(top, len(concepts))} Concepts")
    table.add_column("#", style="dim")
    table.add_column("Concept", style="cyan")
    table.add_column("Difficulty", justify="center")
    table.add_column("Details", style="dim")

    for i, concept in enumerate(concepts[:top], 1):
        # Get additional details based on domain
        if domain == "reading-skills":
            details = f"freq: {concept.domain_data.get('frequency', '?')}"
        else:
            details = concept.domain_data.get("category", "")

        # Visual difficulty indicator (ASCII-safe for Windows)
        diff = concept.difficulty_score
        diff_bar = "#" * diff + "-" * (10 - diff)

        table.add_row(str(i), concept.name, diff_bar, details)

    console.print(table)
    console.print(f"\n[dim]Total concepts found: {len(concepts)}[/dim]")


# =============================================================================
# Learn Command (placeholder)
# =============================================================================


@app.command("learn")
def learn(
    domain: str = typer.Option(..., "--domain", "-d", help="Skill domain to study"),
    learner_name: str = typer.Option("default", "--learner", "-l", help="Learner profile name"),
) -> None:
    """Start an interactive learning session.

    Enter a REPL-like environment where you study concepts,
    answer assessments, and track your progress in real-time.
    """
    console.print(f"[yellow]Interactive learn mode not yet implemented.[/yellow]")
    console.print(f"Domain: {domain}")
    console.print(f"Learner: {learner_name}")
    console.print()
    console.print("[dim]This will provide a REPL-like learning experience.[/dim]")


# =============================================================================
# Review Command (placeholder)
# =============================================================================


@app.command("review")
def review(
    learner_name: str = typer.Option("default", "--learner", "-l", help="Learner profile name"),
    domain: Optional[str] = typer.Option(
        None, "--domain", "-d", help="Filter by domain"
    ),
) -> None:
    """Start a spaced repetition review session.

    Reviews concepts that are due based on the SM-2 algorithm.
    """
    console.print(f"[yellow]Spaced repetition review not yet implemented.[/yellow]")
    console.print(f"Learner: {learner_name}")
    if domain:
        console.print(f"Domain: {domain}")
    console.print()
    console.print("[dim]This will review concepts due for spaced repetition.[/dim]")


# =============================================================================
# Learner Commands
# =============================================================================

learner_app = typer.Typer(help="Manage learner profiles")
app.add_typer(learner_app, name="learner")


@learner_app.command("create")
def learner_create(
    name: str = typer.Argument(..., help="Name for the new learner profile"),
) -> None:
    """Create a new learner profile."""
    console.print(f"[yellow]Learner creation not yet implemented (requires persistence).[/yellow]")
    console.print(f"Would create learner: {name}")


@learner_app.command("list")
def learner_list() -> None:
    """List all learner profiles."""
    console.print(f"[yellow]Learner listing not yet implemented (requires persistence).[/yellow]")


@learner_app.command("stats")
def learner_stats(
    name: str = typer.Argument(..., help="Learner profile name"),
) -> None:
    """Show statistics for a learner."""
    console.print(f"[yellow]Learner stats not yet implemented (requires persistence).[/yellow]")
    console.print(f"Learner: {name}")


@learner_app.command("delete")
def learner_delete(
    name: str = typer.Argument(..., help="Learner profile name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a learner profile."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete learner '{name}'?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    console.print(f"[yellow]Learner deletion not yet implemented (requires persistence).[/yellow]")


# =============================================================================
# GUI Command (placeholder)
# =============================================================================


@app.command("gui")
def gui(
    port: int = typer.Option(8080, "--port", "-p", help="Port to run on"),
    native: bool = typer.Option(
        False, "--native", help="Run as native desktop app"
    ),
    reload: bool = typer.Option(
        False, "--reload", help="Enable hot reload for development"
    ),
) -> None:
    """Launch the web-based graphical interface.

    Opens a modern web UI with dashboard, study mode, review mode,
    and progress analytics.
    """
    console.print(f"[yellow]GUI not yet implemented.[/yellow]")
    console.print(f"Would launch on port {port}")
    if native:
        console.print("Would run in native mode (pywebview)")


# =============================================================================
# Config Command
# =============================================================================


@app.command("config")
def show_config() -> None:
    """Show current configuration."""
    settings = get_settings()

    table = Table(title="Holocron Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Default Model", settings.default_model)
    table.add_row("Temperature", str(settings.temperature))
    table.add_row("Chunk Size", str(settings.chunk_size))
    table.add_row("Mastery Model", settings.default_mastery_model)
    table.add_row("Mastery Threshold", f"{settings.mastery_threshold}%")
    table.add_row("Web Host", settings.web_host)
    table.add_row("Web Port", str(settings.web_port))

    # Show API key status (not the keys themselves)
    table.add_row(
        "Gemini API Key",
        "[green]Set[/green]" if settings.gemini_api_key else "[red]Not set[/red]",
    )
    table.add_row(
        "OpenAI API Key",
        "[green]Set[/green]" if settings.openai_api_key else "[red]Not set[/red]",
    )
    table.add_row(
        "Anthropic API Key",
        "[green]Set[/green]" if settings.anthropic_api_key else "[red]Not set[/red]",
    )

    console.print(table)


if __name__ == "__main__":
    app()
