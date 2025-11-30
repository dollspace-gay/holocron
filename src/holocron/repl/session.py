"""Interactive REPL session controller for Holocron.

This module provides the SessionController that manages interactive
learning sessions with real-time feedback and progress tracking.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from holocron.core.grader import AssessmentGrader, GradingResult
from holocron.core.mastery import MasteryEngine
from holocron.core.models import (
    Assessment,
    AssessmentResult,
    BloomLevel,
    Concept,
    ConceptMastery,
    LearnerProfile,
    LearningSession,
)
from holocron.core.transformer import ContentTransformer, TransformConfig
from holocron.domains.registry import DomainRegistry
from holocron.learner import Database, LearnerRepository


class SessionState(str, Enum):
    """States for the REPL session."""

    IDLE = "idle"
    STUDYING = "studying"
    ASSESSMENT = "assessment"
    REVIEW = "review"
    PAUSED = "paused"


@dataclass
class REPLCommand:
    """A REPL command definition."""

    name: str
    aliases: list[str]
    description: str
    handler: Callable[["SessionController", list[str]], None]


@dataclass
class SessionStats:
    """Statistics for the current session."""

    concepts_studied: int = 0
    assessments_attempted: int = 0
    assessments_correct: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_minutes: float = 0.0

    @property
    def accuracy(self) -> float:
        """Calculate assessment accuracy."""
        if self.assessments_attempted == 0:
            return 0.0
        return (self.assessments_correct / self.assessments_attempted) * 100


class SessionController:
    """Controls an interactive learning session.

    Provides a REPL-like experience for studying concepts, answering
    assessments, and tracking progress in real-time.

    Example:
        ```python
        controller = SessionController(
            learner_id="student-1",
            domain_id="python-programming",
        )
        await controller.run()
        ```
    """

    def __init__(
        self,
        learner_id: str,
        domain_id: str,
        db: Database | None = None,
        console: Console | None = None,
        grader: AssessmentGrader | None = None,
    ) -> None:
        """Initialize the session controller.

        Args:
            learner_id: The learner's identifier
            domain_id: The domain to study
            db: Database instance (creates default if not provided)
            console: Rich console (creates default if not provided)
            grader: Assessment grader (creates default if not provided)
        """
        self.learner_id = learner_id
        self.domain_id = domain_id
        self.console = console or Console()
        self.grader = grader or AssessmentGrader()

        # Database and repository
        if db is None:
            from holocron.learner import get_default_db_path
            db = Database(get_default_db_path())
        self.db = db
        self.repo = LearnerRepository(db)

        # Session state
        self.state = SessionState.IDLE
        self.running = False
        self.stats = SessionStats()
        self.session_id = str(uuid4())[:8]

        # Current learning context
        self.learner: LearnerProfile | None = None
        self.adapter = DomainRegistry.get(domain_id)
        self.transformer: ContentTransformer | None = None
        self.mastery_engine: MasteryEngine | None = None

        # Current study items
        self.current_concepts: list[Concept] = []
        self.current_assessments: list[Assessment] = []
        self.current_assessment_index: int = 0

        # Register commands
        self._commands: dict[str, REPLCommand] = {}
        self._register_commands()

    def _register_commands(self) -> None:
        """Register available REPL commands."""
        commands = [
            REPLCommand("help", ["h", "?"], "Show available commands", self._cmd_help),
            REPLCommand("stats", ["s"], "Show session statistics", self._cmd_stats),
            REPLCommand("progress", ["p"], "Show learning progress", self._cmd_progress),
            REPLCommand("review", ["r"], "Start spaced repetition review", self._cmd_review),
            REPLCommand("load", ["l"], "Load content from a file", self._cmd_load),
            REPLCommand("concept", ["c"], "Show current concept details", self._cmd_concept),
            REPLCommand("skip", [], "Skip current assessment", self._cmd_skip),
            REPLCommand("hint", [], "Get a hint for current assessment", self._cmd_hint),
            REPLCommand("quit", ["q", "exit"], "End the session", self._cmd_quit),
        ]

        for cmd in commands:
            self._commands[cmd.name] = cmd
            for alias in cmd.aliases:
                self._commands[alias] = cmd

    async def initialize(self) -> bool:
        """Initialize the session and load learner profile.

        Returns:
            True if initialization succeeded
        """
        # Initialize database
        await self.db.initialize()

        # Load or create learner profile
        self.learner = await self.repo.get(self.learner_id)
        if self.learner is None:
            self.console.print(f"[yellow]Creating new learner profile: {self.learner_id}[/yellow]")
            self.learner = LearnerProfile(
                learner_id=self.learner_id,
                name=self.learner_id.replace("-", " ").title(),
            )
            await self.repo.save(self.learner)

        # Initialize transformer and mastery engine
        self.transformer = ContentTransformer(
            domain_id=self.domain_id,
            learner=self.learner,
        )
        self.mastery_engine = self.transformer.mastery_engine

        return True

    async def run(self) -> None:
        """Run the interactive REPL session."""
        self.running = True

        # Initialize
        if not await self.initialize():
            self.console.print("[red]Failed to initialize session.[/red]")
            return

        # Welcome message
        self._show_welcome()

        # Main REPL loop
        while self.running:
            try:
                # Get user input
                prompt = self._get_prompt()
                user_input = Prompt.ask(prompt).strip()

                if not user_input:
                    continue

                # Check for command (starts with /)
                if user_input.startswith("/"):
                    await self._handle_command(user_input[1:])
                elif self.state == SessionState.ASSESSMENT:
                    # In assessment mode, input is an answer
                    await self._handle_assessment_response(user_input)
                else:
                    # Free input - could be content to study
                    await self._handle_free_input(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[dim]Use /quit to exit[/dim]")
            except EOFError:
                await self._end_session()
                break

        # Save session
        await self._end_session()

    def _show_welcome(self) -> None:
        """Display welcome message."""
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]Welcome to Holocron Interactive Learning[/bold cyan]\n\n"
                f"Learner: [green]{self.learner.name}[/green]\n"
                f"Domain: [green]{self.adapter.config.display_name}[/green]\n\n"
                f"[dim]Type /help for commands, or paste content to study.[/dim]",
                border_style="cyan",
            )
        )
        self.console.print()

    def _get_prompt(self) -> str:
        """Get the current prompt based on state."""
        state_prompts = {
            SessionState.IDLE: "[cyan]holocron[/cyan]",
            SessionState.STUDYING: "[green]studying[/green]",
            SessionState.ASSESSMENT: "[yellow]answer[/yellow]",
            SessionState.REVIEW: "[magenta]review[/magenta]",
            SessionState.PAUSED: "[dim]paused[/dim]",
        }
        return state_prompts.get(self.state, "")

    async def _handle_command(self, cmd_input: str) -> None:
        """Handle a command input."""
        parts = cmd_input.split(maxsplit=1)
        cmd_name = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []

        if cmd_name in self._commands:
            cmd = self._commands[cmd_name]
            try:
                result = cmd.handler(self, args)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
        else:
            self.console.print(f"[red]Unknown command: /{cmd_name}[/red]")
            self.console.print("[dim]Type /help for available commands[/dim]")

    async def _handle_assessment_response(self, response: str) -> None:
        """Handle a response to the current assessment."""
        if not self.current_assessments or self.current_assessment_index >= len(self.current_assessments):
            self.state = SessionState.IDLE
            return

        assessment = self.current_assessments[self.current_assessment_index]

        # Grade the response
        with self.console.status("[bold green]Evaluating..."):
            result = self.grader.grade(assessment, response, self.learner_id)

        self.stats.assessments_attempted += 1
        if result.is_correct:
            self.stats.assessments_correct += 1

        # Display result
        self._show_grading_result(assessment, result)

        # Update mastery
        if self.mastery_engine:
            assessment_result = AssessmentResult(
                assessment_id=assessment.assessment_id,
                learner_id=self.learner_id,
                timestamp=datetime.now(timezone.utc),
                response=response,
                is_correct=result.is_correct,
                score=result.score,
                feedback=result.feedback,
            )
            self.mastery_engine.update_from_assessment(
                concept_id=assessment.concept_id,
                result=assessment_result,
                bloom_level=assessment.bloom_level,
            )

        # Move to next assessment or finish
        self.current_assessment_index += 1
        if self.current_assessment_index < len(self.current_assessments):
            self._show_current_assessment()
        else:
            self.console.print()
            self.console.print("[green]All assessments completed![/green]")
            self._show_session_summary()
            self.state = SessionState.IDLE

    def _show_grading_result(self, assessment: Assessment, result: GradingResult) -> None:
        """Display grading result with feedback."""
        self.console.print()

        if result.is_correct:
            self.console.print("[bold green]Correct![/bold green]")
        else:
            self.console.print("[bold red]Not quite.[/bold red]")

        # Score display
        score_pct = int(result.score * 100)
        self.console.print(f"Score: {score_pct}%")

        # Feedback
        if result.feedback:
            self.console.print()
            self.console.print(Panel(result.feedback, title="Feedback", border_style="blue"))

        # Strengths
        if result.strengths:
            self.console.print()
            self.console.print("[green]Strengths:[/green]")
            for strength in result.strengths:
                self.console.print(f"  + {strength}")

        # Areas for improvement
        if result.areas_for_improvement:
            self.console.print()
            self.console.print("[yellow]Areas to improve:[/yellow]")
            for area in result.areas_for_improvement:
                self.console.print(f"  - {area}")

        self.console.print()

    async def _handle_free_input(self, content: str) -> None:
        """Handle free text input (content to study)."""
        # Check if it's a file path
        path = Path(content)
        if path.exists() and path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
                self.console.print(f"[dim]Loaded content from: {path}[/dim]")
            except Exception as e:
                self.console.print(f"[red]Error reading file: {e}[/red]")
                return

        # Process content
        await self._study_content(content)

    async def _study_content(self, content: str) -> None:
        """Study the given content."""
        self.state = SessionState.STUDYING

        with self.console.status("[bold green]Analyzing content..."):
            config = TransformConfig(
                include_assessments=True,
                num_assessments=1,
                assessment_bloom_levels=[BloomLevel.KNOWLEDGE, BloomLevel.COMPREHENSION],
            )
            result = self.transformer.transform(content, config)

        if not result.concepts_found:
            self.console.print("[yellow]No concepts found in this content.[/yellow]")
            self.state = SessionState.IDLE
            return

        self.current_concepts = result.concepts_found
        self.current_assessments = result.assessments
        self.current_assessment_index = 0
        self.stats.concepts_studied += len(result.concepts_found)

        # Show extracted concepts
        self.console.print()
        self.console.print(f"[green]Found {len(result.concepts_found)} concepts[/green]")

        table = Table(title="Concepts to Study")
        table.add_column("Concept", style="cyan")
        table.add_column("Difficulty", justify="center")
        table.add_column("Your Mastery", justify="center")

        for concept in result.concepts_found[:10]:
            mastery = self.learner.get_mastery(self.domain_id, concept.concept_id)
            mastery_pct = f"{int(mastery.overall_mastery)}%"
            diff_bar = "#" * concept.difficulty_score + "-" * (10 - concept.difficulty_score)
            table.add_row(concept.name, diff_bar, mastery_pct)

        if len(result.concepts_found) > 10:
            table.add_row("...", "", f"+{len(result.concepts_found) - 10} more")

        self.console.print(table)

        # Start assessments if available
        if self.current_assessments:
            self.console.print()
            if Confirm.ask(f"Ready to test your understanding? ({len(self.current_assessments)} questions)"):
                self.state = SessionState.ASSESSMENT
                self._show_current_assessment()
            else:
                self.state = SessionState.IDLE
        else:
            self.state = SessionState.IDLE

    def _show_current_assessment(self) -> None:
        """Display the current assessment."""
        if not self.current_assessments or self.current_assessment_index >= len(self.current_assessments):
            return

        assessment = self.current_assessments[self.current_assessment_index]
        progress = f"[{self.current_assessment_index + 1}/{len(self.current_assessments)}]"

        self.console.print()
        self.console.print(
            Panel(
                f"[bold]{assessment.question}[/bold]",
                title=f"{progress} {assessment.bloom_level.value.title()} Question",
                subtitle=f"Concept: {assessment.concept_id}",
                border_style="yellow",
            )
        )

        # Show options for multiple choice
        if assessment.options:
            self.console.print()
            for i, option in enumerate(assessment.options):
                letter = chr(65 + i)  # A, B, C, D
                self.console.print(f"  {letter}. {option.text}")
            self.console.print()
            self.console.print("[dim]Enter your answer (A, B, C, D) or type your response[/dim]")
        else:
            self.console.print()
            self.console.print("[dim]Type your answer below[/dim]")

    def _show_session_summary(self) -> None:
        """Show a summary of the current session."""
        elapsed = (datetime.now(timezone.utc) - self.stats.start_time).total_seconds() / 60

        self.console.print()
        self.console.print(
            Panel(
                f"[bold]Concepts Studied:[/bold] {self.stats.concepts_studied}\n"
                f"[bold]Assessments:[/bold] {self.stats.assessments_correct}/{self.stats.assessments_attempted} correct\n"
                f"[bold]Accuracy:[/bold] {self.stats.accuracy:.1f}%\n"
                f"[bold]Time:[/bold] {elapsed:.1f} minutes",
                title="Session Summary",
                border_style="green",
            )
        )

    # ==========================================================================
    # Command Handlers
    # ==========================================================================

    def _cmd_help(self, args: list[str]) -> None:
        """Show help for commands."""
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Aliases", style="dim")
        table.add_column("Description")

        seen = set()
        for cmd in self._commands.values():
            if cmd.name in seen:
                continue
            seen.add(cmd.name)
            aliases = ", ".join(cmd.aliases) if cmd.aliases else "-"
            table.add_row(f"/{cmd.name}", aliases, cmd.description)

        self.console.print(table)
        self.console.print()
        self.console.print("[dim]You can also paste text or file paths to study content.[/dim]")

    def _cmd_stats(self, args: list[str]) -> None:
        """Show session statistics."""
        self._show_session_summary()

    async def _cmd_progress(self, args: list[str]) -> None:
        """Show learning progress."""
        if not self.learner:
            return

        # Reload learner data
        self.learner = await self.repo.get(self.learner_id)
        stats = await self.repo.get_learner_stats(self.learner_id)

        self.console.print()
        self.console.print(
            Panel(
                f"[bold]Total Study Time:[/bold] {stats.get('total_study_time_minutes', 0)} minutes\n"
                f"[bold]Current Streak:[/bold] {stats.get('current_streak_days', 0)} days\n"
                f"[bold]Concepts Mastered:[/bold] {stats.get('concepts_mastered', 0)}\n"
                f"[bold]Due for Review:[/bold] {stats.get('concepts_due_for_review', 0)}",
                title=f"Progress: {self.learner.name}",
                border_style="cyan",
            )
        )

        # Domain breakdown
        domains = stats.get("domains", {})
        if domains:
            table = Table(title="Domain Progress")
            table.add_column("Domain", style="cyan")
            table.add_column("Concepts", justify="right")
            table.add_column("Avg Mastery", justify="right")

            for domain_id, domain_stats in domains.items():
                table.add_row(
                    domain_id,
                    str(domain_stats["concept_count"]),
                    f"{domain_stats['avg_mastery']}%",
                )
            self.console.print(table)

    async def _cmd_review(self, args: list[str]) -> None:
        """Start spaced repetition review."""
        due_concepts = await self.repo.get_concepts_due_for_review(self.learner_id, self.domain_id)

        if not due_concepts:
            self.console.print("[green]No concepts due for review![/green]")
            return

        self.console.print(f"[yellow]{len(due_concepts)} concepts due for review[/yellow]")

        # Generate review assessments
        self.state = SessionState.REVIEW
        self.current_assessments = []
        self.current_assessment_index = 0

        for domain_id, concept_id in due_concepts[:5]:  # Limit to 5 per session
            try:
                concept = Concept(
                    concept_id=concept_id,
                    domain_id=domain_id,
                    name=concept_id.split(".")[-1].replace("_", " ").title(),
                    description="Review concept",
                )
                assessment = self.adapter.generate_assessment(
                    concept=concept,
                    bloom_level=BloomLevel.KNOWLEDGE,
                )
                self.current_assessments.append(assessment)
            except Exception:
                pass

        if self.current_assessments:
            self.state = SessionState.ASSESSMENT
            self._show_current_assessment()
        else:
            self.console.print("[yellow]Could not generate review assessments.[/yellow]")
            self.state = SessionState.IDLE

    async def _cmd_load(self, args: list[str]) -> None:
        """Load content from a file."""
        if not args:
            self.console.print("[yellow]Usage: /load <filepath>[/yellow]")
            return

        filepath = " ".join(args)
        path = Path(filepath)

        if not path.exists():
            self.console.print(f"[red]File not found: {filepath}[/red]")
            return

        try:
            content = path.read_text(encoding="utf-8")
            self.console.print(f"[green]Loaded: {path.name}[/green]")
            await self._study_content(content)
        except Exception as e:
            self.console.print(f"[red]Error reading file: {e}[/red]")

    def _cmd_concept(self, args: list[str]) -> None:
        """Show details about current concept."""
        if not self.current_concepts:
            self.console.print("[yellow]No concepts loaded. Paste content to study.[/yellow]")
            return

        # Show first concept or specified index
        index = 0
        if args and args[0].isdigit():
            index = int(args[0]) - 1

        if index < 0 or index >= len(self.current_concepts):
            self.console.print(f"[red]Invalid concept index. Range: 1-{len(self.current_concepts)}[/red]")
            return

        concept = self.current_concepts[index]
        mastery = self.learner.get_mastery(self.domain_id, concept.concept_id)

        content = f"[bold]Name:[/bold] {concept.name}\n"
        content += f"[bold]ID:[/bold] {concept.concept_id}\n"
        content += f"[bold]Difficulty:[/bold] {concept.difficulty_score}/10\n"
        content += f"[bold]Your Mastery:[/bold] {mastery.overall_mastery:.1f}%\n"

        if concept.description:
            content += f"\n[bold]Description:[/bold]\n{concept.description}\n"

        if concept.examples:
            content += f"\n[bold]Examples:[/bold]\n"
            for ex in concept.examples[:3]:
                content += f"  - {ex}\n"

        self.console.print(Panel(content, title="Concept Details", border_style="cyan"))

    def _cmd_skip(self, args: list[str]) -> None:
        """Skip the current assessment."""
        if self.state != SessionState.ASSESSMENT:
            self.console.print("[yellow]Not in assessment mode.[/yellow]")
            return

        self.current_assessment_index += 1
        self.stats.assessments_attempted += 1  # Count as attempted but incorrect

        if self.current_assessment_index < len(self.current_assessments):
            self.console.print("[dim]Skipped.[/dim]")
            self._show_current_assessment()
        else:
            self.console.print("[green]All assessments completed![/green]")
            self._show_session_summary()
            self.state = SessionState.IDLE

    def _cmd_hint(self, args: list[str]) -> None:
        """Show a hint for the current assessment."""
        if self.state != SessionState.ASSESSMENT:
            self.console.print("[yellow]Not in assessment mode.[/yellow]")
            return

        if not self.current_assessments or self.current_assessment_index >= len(self.current_assessments):
            return

        assessment = self.current_assessments[self.current_assessment_index]

        if assessment.hints:
            hint = assessment.hints[0]
            self.console.print(Panel(hint, title="Hint", border_style="yellow"))
        else:
            # Generate a hint from the concept
            for concept in self.current_concepts:
                if concept.concept_id == assessment.concept_id:
                    if concept.description:
                        self.console.print(Panel(concept.description, title="Hint", border_style="yellow"))
                        return
            self.console.print("[yellow]No hints available for this question.[/yellow]")

    def _cmd_quit(self, args: list[str]) -> None:
        """End the session."""
        self.running = False

    async def _end_session(self) -> None:
        """End the session and save progress."""
        if self.learner:
            elapsed = (datetime.now(timezone.utc) - self.stats.start_time).total_seconds() / 60
            self.learner.total_study_time_minutes += int(elapsed)

            # Save learner progress
            await self.repo.save(self.learner)

        self._show_session_summary()
        self.console.print()
        self.console.print("[cyan]Session ended. Progress saved![/cyan]")


async def start_session(
    learner_id: str,
    domain_id: str,
    db: Database | None = None,
) -> None:
    """Start an interactive learning session.

    Args:
        learner_id: The learner's identifier
        domain_id: The domain to study
        db: Optional database instance
    """
    controller = SessionController(
        learner_id=learner_id,
        domain_id=domain_id,
        db=db,
    )
    await controller.run()
