"""
HeartCare AI – Application Entry Point
Run this file to start the Flask development server.
"""
import sys
import os

# Ensure the healthcare_app directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  HeartCare AI – Starting Flask Server")
    print("=" * 60)
    print("  URL: http://127.0.0.1:5000")
    print("  Admin:  admin / admin@123")
    print("  Doctor: arjun.sharma / doctor@123")
    print("  (Register for patient access)")
    print("=" * 60)
    debug = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'}
    app.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', '5000')))
