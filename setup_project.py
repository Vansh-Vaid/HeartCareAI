"""
Setup script - creates the project directory structure
"""
import os

dirs = [
    'templates',
    'static/css',
    'static/js',
    'static/images',
    'static/charts',
    'models',
    'data',
    'reports',
    'instance',
]

base = os.path.dirname(os.path.abspath(__file__))
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)
    print(f"Created: {d}")

print("Done - all directories created!")
