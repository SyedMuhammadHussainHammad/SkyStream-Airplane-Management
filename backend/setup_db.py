from app import app, db
import models

with app.app_context():
    try:
        db.create_all()
        print("✅ Success! Tables created in Neon.")
    except Exception as e:
        print(f"❌ Error: {e}")
