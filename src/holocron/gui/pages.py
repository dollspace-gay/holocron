"""Multi-page routes for web GUI mode.

This module contains the @ui.page decorated routes.
Only import this module when running in web (non-native) mode.
"""

from nicegui import ui

from holocron.config import get_settings
from holocron.domains.registry import DomainRegistry


def register_pages(state, ui_module=None):
    """Register all page routes with the given state.

    Args:
        state: Application state object
        ui_module: The nicegui ui module (optional, for setting colors)
    """
    # Set colors inside a page to avoid triggering script mode
    # Colors will be applied when the first page loads

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

    @ui.page("/")
    async def dashboard():
        """Main dashboard page."""
        # Set colors on first page load (safe inside @ui.page)
        ui.colors(primary="#3b82f6", secondary="#8b5cf6", accent="#f59e0b")
        create_header()

        learner = await state.get_learner("default")
        state.current_learner = learner

        if state.repo is None:
            await state.initialize()

        stats = await state.repo.get_learner_stats(learner.learner_id)

        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-6"):
            ui.label(f"Welcome back, {learner.name}!").classes("text-2xl font-bold")

            with ui.row().classes("w-full gap-4"):
                with ui.card().classes("flex-1"):
                    with ui.column().classes("items-center p-4"):
                        ui.icon("schedule", size="xl", color="primary")
                        ui.label(f"{stats.get('total_study_time_minutes', 0)}").classes("text-3xl font-bold")
                        ui.label("Minutes Studied").classes("text-gray-500")

                with ui.card().classes("flex-1"):
                    with ui.column().classes("items-center p-4"):
                        ui.icon("local_fire_department", size="xl", color="orange")
                        ui.label(f"{stats.get('current_streak_days', 0)}").classes("text-3xl font-bold")
                        ui.label("Day Streak").classes("text-gray-500")

                with ui.card().classes("flex-1"):
                    with ui.column().classes("items-center p-4"):
                        ui.icon("emoji_events", size="xl", color="green")
                        ui.label(f"{stats.get('concepts_mastered', 0)}").classes("text-3xl font-bold")
                        ui.label("Concepts Mastered").classes("text-gray-500")

                with ui.card().classes("flex-1"):
                    with ui.column().classes("items-center p-4"):
                        ui.icon("replay", size="xl", color="purple")
                        ui.label(f"{stats.get('concepts_due_for_review', 0)}").classes("text-3xl font-bold")
                        ui.label("Due for Review").classes("text-gray-500")

            accuracy = stats.get("accuracy", 0)
            with ui.card().classes("w-full"):
                with ui.column().classes("p-4 gap-2"):
                    ui.label("Assessment Accuracy").classes("font-bold")
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.linear_progress(value=accuracy / 100, show_value=False).classes("flex-1")
                        ui.label(f"{accuracy:.0f}%").classes("font-bold")

            domains = stats.get("domains", {})
            if domains:
                with ui.card().classes("w-full"):
                    with ui.column().classes("p-4 gap-4"):
                        ui.label("Domain Progress").classes("font-bold text-lg")
                        for domain_id, domain_stats in domains.items():
                            with ui.row().classes("w-full items-center gap-4"):
                                ui.label(domain_id).classes("w-48")
                                with ui.column().classes("flex-1 gap-1"):
                                    ui.linear_progress(value=domain_stats["avg_mastery"] / 100, show_value=False).classes("w-full")
                                    ui.label(f"{domain_stats['concept_count']} concepts, {domain_stats['avg_mastery']:.0f}% avg mastery").classes("text-sm text-gray-500")

            with ui.row().classes("w-full gap-4 mt-4"):
                ui.button("Start Studying", icon="menu_book", on_click=lambda: ui.navigate.to("/study")).classes("flex-1").props("color=primary size=lg")
                ui.button("Review Due Concepts", icon="replay", on_click=lambda: ui.navigate.to("/review")).classes("flex-1").props("color=secondary size=lg")

        create_footer()

    @ui.page("/study")
    async def study_page():
        """Study mode page."""
        create_header()

        learner = await state.get_learner("default")
        state.current_learner = learner

        with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-6"):
            ui.label("Study Mode").classes("text-2xl font-bold")

            domains = DomainRegistry.list_domains()
            domain_select = ui.select(
                options=domains,
                value=state.current_domain,
                label="Select Domain",
                on_change=lambda e: setattr(state, "current_domain", e.value),
            ).classes("w-full")

            ui.label("Paste content to study:").classes("font-semibold mt-4")
            content_area = ui.textarea(placeholder="Paste text content here...").classes("w-full").props("rows=10")

            ui.label("Or upload a file:").classes("font-semibold mt-2")

            async def handle_upload(e):
                content = e.content.read().decode("utf-8")
                content_area.value = content

            ui.upload(on_upload=handle_upload, auto_upload=True).classes("w-full").props('accept=".txt,.md,.py"')

            results_container = ui.column().classes("w-full gap-4 mt-4")

            async def start_study():
                content = content_area.value
                if not content or not content.strip():
                    ui.notify("Please enter some content to study", type="warning")
                    return

                results_container.clear()

                from holocron.core.transformer import ContentTransformer, TransformConfig
                from holocron.core.models import BloomLevel

                transformer = ContentTransformer(domain_id=state.current_domain, learner=learner)
                config = TransformConfig(
                    include_assessments=True,
                    num_assessments=1,
                    assessment_bloom_levels=[BloomLevel.KNOWLEDGE, BloomLevel.COMPREHENSION],
                )
                result = transformer.transform(content, config)

                with results_container:
                    if not result.concepts_found:
                        ui.label("No concepts found in this content.").classes("text-yellow-600")
                        return

                    ui.label(f"Found {len(result.concepts_found)} concepts").classes("font-bold text-lg")

                    with ui.expansion("View Concepts", icon="lightbulb").classes("w-full"):
                        for concept in result.concepts_found[:15]:
                            with ui.card().classes("w-full mb-2"):
                                with ui.row().classes("items-center justify-between"):
                                    ui.label(concept.name).classes("font-semibold")
                                    ui.badge(f"Difficulty: {concept.difficulty_score}/10")

                    if result.assessments:
                        ui.label(f"Generated {len(result.assessments)} assessments").classes("font-bold text-lg mt-4")

                await state.save_learner()
                ui.notify(f"Studied {len(result.concepts_found)} concepts!", type="positive")

            ui.button("Start Studying", icon="play_arrow", on_click=start_study).classes("mt-4").props("color=primary size=lg")

        create_footer()

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

            due_concepts = await state.repo.get_concepts_due_for_review(learner.learner_id)

            if not due_concepts:
                with ui.card().classes("w-full"):
                    with ui.column().classes("items-center p-8 gap-4"):
                        ui.icon("check_circle", size="6rem", color="green")
                        ui.label("All caught up!").classes("text-xl font-bold")
                        ui.label("No concepts due for review.").classes("text-gray-500")
                        ui.button("Go Study New Content", icon="menu_book", on_click=lambda: ui.navigate.to("/study")).props("color=primary")
            else:
                ui.label(f"{len(due_concepts)} concepts due for review").classes("text-gray-600")

                for domain_id, concept_id in due_concepts[:10]:
                    mastery = learner.get_mastery(domain_id, concept_id)
                    with ui.card().classes("w-full"):
                        with ui.row().classes("items-center justify-between"):
                            with ui.column():
                                ui.label(concept_id.split(".")[-1].replace("_", " ").title()).classes("font-semibold")
                                ui.label(f"Domain: {domain_id}").classes("text-sm text-gray-500")
                            with ui.column().classes("items-end"):
                                ui.label(f"Mastery: {mastery.overall_mastery:.0f}%").classes("font-bold")

                ui.button("Start Review Session", icon="replay", on_click=lambda: ui.notify("Starting review...", type="info")).classes("mt-4").props("color=primary size=lg")

        create_footer()

    @ui.page("/settings")
    async def settings_page():
        """Settings page."""
        create_header()

        learner = await state.get_learner("default")
        state.current_learner = learner
        settings = get_settings()

        with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-6"):
            ui.label("Settings").classes("text-2xl font-bold")

            with ui.card().classes("w-full"):
                with ui.column().classes("p-4 gap-4"):
                    ui.label("Profile Settings").classes("font-bold text-lg")
                    name_input = ui.input("Name", value=learner.name).classes("w-full")
                    daily_goal = ui.number("Daily Goal (minutes)", value=learner.preferences.daily_goal_minutes, min=5, max=120).classes("w-full")

                    async def save_profile():
                        learner.name = name_input.value
                        learner.preferences.daily_goal_minutes = int(daily_goal.value)
                        await state.save_learner()
                        ui.notify("Profile saved!", type="positive")

                    ui.button("Save Profile", icon="save", on_click=save_profile).props("color=primary")

            with ui.card().classes("w-full"):
                with ui.column().classes("p-4 gap-4"):
                    ui.label("Available Domains").classes("font-bold text-lg")
                    for domain_id in DomainRegistry.list_domains():
                        adapter = DomainRegistry.get(domain_id)
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("folder", color="primary")
                            ui.label(adapter.config.display_name).classes("font-semibold")

        create_footer()
