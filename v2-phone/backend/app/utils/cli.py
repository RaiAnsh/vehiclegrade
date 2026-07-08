"""Custom Flask CLI commands. Run with: flask --app run.py seed-db"""

import click

from app.utils.seed_data import seed_database


def register_cli(app):
    @app.cli.command("seed-db")
    def seed_db():
        """Drop, recreate, and repopulate all tables with mock data."""
        counts = seed_database()
        click.echo(
            f"Seeded {counts['models']} models, {counts['locations']} locations, "
            f"{counts['listings']} listings."
        )
