"""Main NiceGUI application for Holocron.

This module provides the web-based graphical interface with:
- Dashboard with progress overview
- Study mode for learning new content
- Review mode for spaced repetition
- Settings for configuration

Note: NiceGUI has two modes:
- Web mode: Uses @ui.page decorators for multi-page apps
- Script/Native mode: Builds UI in global scope, single page only

These modes are mutually exclusive - you cannot mix them.
"""

from holocron.core.models import LearnerProfile
from holocron.learner import Database, LearnerRepository, get_default_db_path

# Ensure domains are loaded
import holocron.domains  # noqa: F401


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


# Global state instance
state = AppState()


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
        native: Run as native desktop app (simplified single-page UI)
    """
    # Import nicegui here to avoid triggering script mode at module load
    from nicegui import app, ui

    if native:
        # Native mode: script mode with single page
        _run_native_ui(app, ui, state, host, port)
    else:
        # Web mode: multi-page with @ui.page decorators
        _run_web_ui(app, ui, state, host, port, reload)


def _run_web_ui(app, ui, state, host: str, port: int, reload: bool):
    """Run in web mode with multi-page support."""
    # Import pages module to register routes
    from holocron.gui.pages import register_pages

    # Configure app startup (do NOT call ui.colors here - it triggers script mode)
    app.on_startup(state.initialize)

    # Register all page routes (colors are set inside pages)
    register_pages(state, ui)

    ui.run(
        host=host,
        port=port,
        reload=reload,
        native=False,
        title="Holocron",
        favicon="🎓",
    )


def _run_native_ui(app, ui, state, host: str, port: int):
    """Run in native/script mode with single-page UI.

    In script mode, we build UI directly (no @ui.page decorators).
    Uses ui.timer for async data loading since app.on_startup is not available.
    """
    from holocron.domains.registry import DomainRegistry

    ui.colors(primary="#3b82f6", secondary="#8b5cf6", accent="#f59e0b")

    # Header
    with ui.header().classes("bg-primary text-white items-center"):
        with ui.row().classes("items-center gap-4"):
            ui.icon("school", size="lg")
            ui.label("Holocron").classes("text-xl font-bold")

    # Main content area with placeholders for async data
    with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-6"):
        welcome_label = ui.label("Loading...").classes("text-2xl font-bold")

        # Stats row
        with ui.row().classes("w-full gap-4"):
            with ui.card().classes("flex-1"):
                with ui.column().classes("items-center p-4"):
                    ui.icon("schedule", size="xl", color="primary")
                    minutes_label = ui.label("0").classes("text-3xl font-bold")
                    ui.label("Minutes").classes("text-gray-500")

            with ui.card().classes("flex-1"):
                with ui.column().classes("items-center p-4"):
                    ui.icon("local_fire_department", size="xl", color="orange")
                    streak_label = ui.label("0").classes("text-3xl font-bold")
                    ui.label("Streak").classes("text-gray-500")

            with ui.card().classes("flex-1"):
                with ui.column().classes("items-center p-4"):
                    ui.icon("emoji_events", size="xl", color="green")
                    mastered_label = ui.label("0").classes("text-3xl font-bold")
                    ui.label("Mastered").classes("text-gray-500")

        # Study section
        with ui.card().classes("w-full"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("Quick Study").classes("font-bold text-lg")

                domains = DomainRegistry.list_domains()
                domain_select = ui.select(options=domains, value="reading-skills", label="Domain").classes("w-full")
                content_area = ui.textarea(placeholder="Paste content to study...").classes("w-full").props("rows=6")

                results = ui.column().classes("w-full")

                async def study():
                    if not content_area.value:
                        ui.notify("Enter content first", type="warning")
                        return

                    from holocron.core.transformer import ContentTransformer, TransformConfig

                    current_learner = await state.get_learner("default")
                    transformer = ContentTransformer(domain_id=domain_select.value, learner=current_learner)
                    result = transformer.transform(content_area.value, TransformConfig())

                    results.clear()
                    with results:
                        ui.label(f"Found {len(result.concepts_found)} concepts").classes("font-bold")
                        for c in result.concepts_found[:5]:
                            ui.label(f"* {c.name}").classes("text-sm")

                    ui.notify(f"Studied {len(result.concepts_found)} concepts!", type="positive")

                ui.button("Study Content", icon="play_arrow", on_click=study).props("color=primary")

    # Footer
    with ui.footer().classes("bg-gray-100 text-gray-600 text-sm"):
        ui.label("Holocron - Evidence-based skill training")

    # Load data asynchronously using timer (runs once after UI is ready)
    async def load_data():
        await state.initialize()
        learner = await state.get_learner("default")
        state.current_learner = learner
        stats = await state.repo.get_learner_stats(learner.learner_id)

        # Update UI elements with loaded data
        welcome_label.set_text(f"Welcome, {learner.name}!")
        minutes_label.set_text(str(stats.get('total_study_time_minutes', 0)))
        streak_label.set_text(str(stats.get('current_streak_days', 0)))
        mastered_label.set_text(str(stats.get('concepts_mastered', 0)))

    # Use timer with once=True to load data after UI is ready
    ui.timer(0.1, load_data, once=True)

    ui.run(
        host=host,
        port=port,
        native=True,
        title="Holocron",
        favicon="🎓",
        window_size=(1024, 768),
        reload=False,
    )
