"""Main NiceGUI application for Holocron.

This module provides the web-based graphical interface with:
- Dashboard with progress overview
- Study mode for learning new content
- Review mode for spaced repetition
- Settings for configuration
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nicegui import app, ui

from holocron.config import get_settings
from holocron.core.models import LearnerProfile
from holocron.domains.registry import DomainRegistry
from holocron.learner import Database, LearnerRepository, get_default_db_path

# Ensure domains are loaded
import holocron.domains  # noqa: F401


# Global state
class AppState:
    """Application state management."""

    def __init__(self):
        self.db: Database | None = None
        self.repo: LearnerRepository | None = None
        self.current_learner: LearnerProfile | None = None
        self.current_domain: str = "reading-skills"

    async def initialize(self):
        """Initialize database connection."""
        self.db = Database(get_default_db_path())
        await self.db.initialize()
        self.repo = LearnerRepository(self.db)

    async def get_learner(self, learner_id: str) -> LearnerProfile | None:
        """Get or create a learner profile."""
        if self.repo is None:
            await self.initialize()

        learner = await self.repo.get(learner_id)
        if learner is None:
            learner = LearnerProfile(
                learner_id=learner_id,
                name=learner_id.replace("-", " ").title(),
            )
            await self.repo.save(learner)
        return learner

    async def save_learner(self):
        """Save current learner profile."""
        if self.current_learner and self.repo:
            await self.repo.save(self.current_learner)


state = AppState()


def create_header():
    """Create the application header."""
    with ui.header().classes("bg-primary text-white items-center justify-between"):
        with ui.row().classes("items-center gap-4"):
            ui.icon("school", size="lg")
            ui.label("Holocron").classes("text-xl font-bold")

        with ui.row().classes("gap-2"):
            ui.button("Dashboard", on_click=lambda: ui.navigate.to("/")).props("flat")
            ui.button("Study", on_click=lambda: ui.navigate.to("/study")).props("flat")
            ui.button("Review", on_click=lambda: ui.navigate.to("/review")).props("flat")
            ui.button("Settings", on_click=lambda: ui.navigate.to("/settings")).props("flat")


def create_footer():
    """Create the application footer."""
    with ui.footer().classes("bg-gray-100 text-gray-600 text-sm"):
        ui.label("Holocron - Evidence-based skill training")


# =============================================================================
# Dashboard Page
# =============================================================================


@ui.page("/")
async def dashboard():
    """Main dashboard page."""
    create_header()

    # Initialize state
    learner = await state.get_learner("default")
    state.current_learner = learner

    if state.repo is None:
        await state.initialize()

    stats = await state.repo.get_learner_stats(learner.learner_id)

    with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-6"):
        # Welcome section
        ui.label(f"Welcome back, {learner.name}!").classes("text-2xl font-bold")

        # Stats cards row
        with ui.row().classes("w-full gap-4"):
            # Study time card
            with ui.card().classes("flex-1"):
                with ui.column().classes("items-center p-4"):
                    ui.icon("schedule", size="xl", color="primary")
                    ui.label(f"{stats.get('total_study_time_minutes', 0)}").classes("text-3xl font-bold")
                    ui.label("Minutes Studied").classes("text-gray-500")

            # Streak card
            with ui.card().classes("flex-1"):
                with ui.column().classes("items-center p-4"):
                    ui.icon("local_fire_department", size="xl", color="orange")
                    ui.label(f"{stats.get('current_streak_days', 0)}").classes("text-3xl font-bold")
                    ui.label("Day Streak").classes("text-gray-500")

            # Concepts mastered card
            with ui.card().classes("flex-1"):
                with ui.column().classes("items-center p-4"):
                    ui.icon("emoji_events", size="xl", color="green")
                    ui.label(f"{stats.get('concepts_mastered', 0)}").classes("text-3xl font-bold")
                    ui.label("Concepts Mastered").classes("text-gray-500")

            # Due for review card
            with ui.card().classes("flex-1"):
                with ui.column().classes("items-center p-4"):
                    ui.icon("replay", size="xl", color="purple")
                    ui.label(f"{stats.get('concepts_due_for_review', 0)}").classes("text-3xl font-bold")
                    ui.label("Due for Review").classes("text-gray-500")

        # Assessment accuracy
        accuracy = stats.get("accuracy", 0)
        with ui.card().classes("w-full"):
            with ui.column().classes("p-4 gap-2"):
                ui.label("Assessment Accuracy").classes("font-bold")
                with ui.row().classes("w-full items-center gap-2"):
                    ui.linear_progress(value=accuracy / 100, show_value=False).classes("flex-1")
                    ui.label(f"{accuracy:.0f}%").classes("font-bold")

        # Domain progress
        domains = stats.get("domains", {})
        if domains:
            with ui.card().classes("w-full"):
                with ui.column().classes("p-4 gap-4"):
                    ui.label("Domain Progress").classes("font-bold text-lg")

                    for domain_id, domain_stats in domains.items():
                        with ui.row().classes("w-full items-center gap-4"):
                            ui.label(domain_id).classes("w-48")
                            with ui.column().classes("flex-1 gap-1"):
                                ui.linear_progress(
                                    value=domain_stats["avg_mastery"] / 100,
                                    show_value=False
                                ).classes("w-full")
                                ui.label(f"{domain_stats['concept_count']} concepts, {domain_stats['avg_mastery']:.0f}% avg mastery").classes("text-sm text-gray-500")

        # Quick actions
        with ui.row().classes("w-full gap-4 mt-4"):
            ui.button("Start Studying", icon="menu_book", on_click=lambda: ui.navigate.to("/study")).classes("flex-1").props("color=primary size=lg")
            ui.button("Review Due Concepts", icon="replay", on_click=lambda: ui.navigate.to("/review")).classes("flex-1").props("color=secondary size=lg")

    create_footer()


# =============================================================================
# Study Page
# =============================================================================


@ui.page("/study")
async def study_page():
    """Study mode page."""
    create_header()

    learner = await state.get_learner("default")
    state.current_learner = learner

    with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-6"):
        ui.label("Study Mode").classes("text-2xl font-bold")

        # Domain selector
        domains = DomainRegistry.list_domains()
        domain_select = ui.select(
            options=domains,
            value=state.current_domain,
            label="Select Domain",
            on_change=lambda e: setattr(state, "current_domain", e.value),
        ).classes("w-full")

        # Content input
        ui.label("Paste content to study:").classes("font-semibold mt-4")
        content_area = ui.textarea(placeholder="Paste text content here to extract concepts and generate assessments...").classes("w-full").props("rows=10")

        # File upload
        ui.label("Or upload a file:").classes("font-semibold mt-2")

        async def handle_upload(e):
            content = e.content.read().decode("utf-8")
            content_area.value = content

        ui.upload(on_upload=handle_upload, auto_upload=True).classes("w-full").props('accept=".txt,.md,.py"')

        # Study results container
        results_container = ui.column().classes("w-full gap-4 mt-4")

        async def start_study():
            content = content_area.value
            if not content or not content.strip():
                ui.notify("Please enter some content to study", type="warning")
                return

            results_container.clear()

            with results_container:
                ui.spinner("dots", size="lg")
                ui.label("Analyzing content...").classes("text-gray-500")

            # Transform content
            from holocron.core.transformer import ContentTransformer, TransformConfig
            from holocron.core.models import BloomLevel

            transformer = ContentTransformer(
                domain_id=state.current_domain,
                learner=learner,
            )

            config = TransformConfig(
                include_assessments=True,
                num_assessments=1,
                assessment_bloom_levels=[BloomLevel.KNOWLEDGE, BloomLevel.COMPREHENSION],
            )

            result = transformer.transform(content, config)

            results_container.clear()

            with results_container:
                if not result.concepts_found:
                    ui.label("No concepts found in this content.").classes("text-yellow-600")
                    return

                # Show concepts
                ui.label(f"Found {len(result.concepts_found)} concepts").classes("font-bold text-lg")

                with ui.expansion("View Concepts", icon="lightbulb").classes("w-full"):
                    for concept in result.concepts_found[:15]:
                        with ui.card().classes("w-full mb-2"):
                            with ui.row().classes("items-center justify-between"):
                                ui.label(concept.name).classes("font-semibold")
                                ui.badge(f"Difficulty: {concept.difficulty_score}/10")
                            if concept.description:
                                ui.label(concept.description).classes("text-sm text-gray-600")

                # Show assessments
                if result.assessments:
                    ui.label(f"Generated {len(result.assessments)} assessments").classes("font-bold text-lg mt-4")

                    for i, assessment in enumerate(result.assessments[:5], 1):
                        with ui.card().classes("w-full"):
                            with ui.column().classes("gap-2"):
                                ui.label(f"Question {i}").classes("font-bold")
                                ui.badge(assessment.bloom_level.value.title()).props("color=secondary")
                                ui.label(assessment.question).classes("mt-2")

                                if assessment.options:
                                    with ui.column().classes("mt-2 gap-1"):
                                        for j, opt in enumerate(assessment.options):
                                            ui.label(f"{chr(65+j)}. {opt.text}").classes("text-sm")

                # Save button
                await state.save_learner()
                ui.notify(f"Studied {len(result.concepts_found)} concepts!", type="positive")

        ui.button("Start Studying", icon="play_arrow", on_click=start_study).classes("mt-4").props("color=primary size=lg")

    create_footer()


# =============================================================================
# Review Page
# =============================================================================


@ui.page("/review")
async def review_page():
    """Spaced repetition review page."""
    create_header()

    learner = await state.get_learner("default")
    state.current_learner = learner

    if state.repo is None:
        await state.initialize()

    with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-6"):
        ui.label("Review Mode").classes("text-2xl font-bold")

        # Get due concepts
        due_concepts = await state.repo.get_concepts_due_for_review(learner.learner_id)

        if not due_concepts:
            with ui.card().classes("w-full"):
                with ui.column().classes("items-center p-8 gap-4"):
                    ui.icon("check_circle", size="6rem", color="green")
                    ui.label("All caught up!").classes("text-xl font-bold")
                    ui.label("No concepts due for review. Great job!").classes("text-gray-500")
                    ui.button("Go Study New Content", icon="menu_book", on_click=lambda: ui.navigate.to("/study")).props("color=primary")
        else:
            ui.label(f"{len(due_concepts)} concepts due for review").classes("text-gray-600")

            # Review cards
            review_container = ui.column().classes("w-full gap-4")

            with review_container:
                for domain_id, concept_id in due_concepts[:10]:
                    mastery = learner.get_mastery(domain_id, concept_id)

                    with ui.card().classes("w-full"):
                        with ui.row().classes("items-center justify-between"):
                            with ui.column():
                                ui.label(concept_id.split(".")[-1].replace("_", " ").title()).classes("font-semibold")
                                ui.label(f"Domain: {domain_id}").classes("text-sm text-gray-500")
                            with ui.column().classes("items-end"):
                                ui.label(f"Mastery: {mastery.overall_mastery:.0f}%").classes("font-bold")
                                ui.linear_progress(value=mastery.overall_mastery / 100).classes("w-32")

            if len(due_concepts) > 10:
                ui.label(f"+{len(due_concepts) - 10} more concepts due").classes("text-gray-500 mt-2")

            ui.button("Start Review Session", icon="replay", on_click=lambda: ui.notify("Review session starting...", type="info")).classes("mt-4").props("color=primary size=lg")

    create_footer()


# =============================================================================
# Settings Page
# =============================================================================


@ui.page("/settings")
async def settings_page():
    """Settings page."""
    create_header()

    learner = await state.get_learner("default")
    state.current_learner = learner
    settings = get_settings()

    with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-6"):
        ui.label("Settings").classes("text-2xl font-bold")

        # Profile settings
        with ui.card().classes("w-full"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("Profile Settings").classes("font-bold text-lg")

                name_input = ui.input("Name", value=learner.name).classes("w-full")
                daily_goal = ui.number("Daily Goal (minutes)", value=learner.preferences.daily_goal_minutes, min=5, max=120).classes("w-full")

                style_select = ui.select(
                    options=["detailed", "concise", "visual", "example-heavy"],
                    value=learner.preferences.explanation_style,
                    label="Explanation Style",
                ).classes("w-full")

                async def save_profile():
                    learner.name = name_input.value
                    learner.preferences.daily_goal_minutes = int(daily_goal.value)
                    learner.preferences.explanation_style = style_select.value
                    await state.save_learner()
                    ui.notify("Profile saved!", type="positive")

                ui.button("Save Profile", icon="save", on_click=save_profile).props("color=primary")

        # LLM settings
        with ui.card().classes("w-full"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("LLM Settings").classes("font-bold text-lg")

                ui.label(f"Default Model: {settings.default_model}").classes("text-gray-600")
                ui.label(f"Temperature: {settings.temperature}").classes("text-gray-600")

                with ui.row().classes("gap-4"):
                    api_status = lambda key, name: ui.label(f"{name}: {'✓ Set' if key else '✗ Not set'}").classes("text-sm")
                    api_status(settings.gemini_api_key, "Gemini")
                    api_status(settings.openai_api_key, "OpenAI")
                    api_status(settings.anthropic_api_key, "Anthropic")

                ui.label("Set API keys via environment variables or .env file").classes("text-sm text-gray-500")

        # Available domains
        with ui.card().classes("w-full"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("Available Domains").classes("font-bold text-lg")

                domains = DomainRegistry.list_domains()
                for domain_id in domains:
                    adapter = DomainRegistry.get(domain_id)
                    config = adapter.config
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("folder", color="primary")
                        ui.label(config.display_name).classes("font-semibold")
                        ui.label(f"- {config.description}").classes("text-gray-600")

        # Danger zone
        with ui.card().classes("w-full border-red-200"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("Danger Zone").classes("font-bold text-lg text-red-600")

                async def reset_progress():
                    if state.repo and state.current_learner:
                        state.current_learner.domain_mastery = {}
                        state.current_learner.total_study_time_minutes = 0
                        state.current_learner.current_streak_days = 0
                        state.current_learner.concepts_mastered = 0
                        await state.save_learner()
                        ui.notify("Progress reset!", type="warning")

                ui.button("Reset All Progress", icon="delete_forever", on_click=reset_progress).props("color=negative outline")

    create_footer()


# =============================================================================
# Application Entry Points
# =============================================================================


def create_app():
    """Create and configure the NiceGUI application."""
    # Configure app
    app.on_startup(state.initialize)

    # Theme
    ui.colors(primary="#3b82f6", secondary="#8b5cf6", accent="#f59e0b")

    return app


def run_gui(
    host: str = "127.0.0.1",
    port: int = 8080,
    reload: bool = False,
    native: bool = False,
):
    """Run the Holocron GUI.

    Args:
        host: Host to bind to
        port: Port to run on
        reload: Enable hot reload for development
        native: Run as native desktop app
    """
    create_app()

    ui.run(
        host=host,
        port=port,
        reload=reload,
        native=native,
        title="Holocron",
        favicon="🎓",
    )
