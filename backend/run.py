"""Entry point for the VehicleGrade API.

Run with: python run.py
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(port=5001, debug=True)
