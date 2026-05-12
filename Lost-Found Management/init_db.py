import os
from app import app
from models import db, Category

with app.app_context():
    # Create all database tables
    db.create_all()
    print("Created database tables.")

    # Check if categories exist, if not, add some default ones
    if not Category.query.first():
        default_categories = ['Electronics', 'Books', 'Clothing', 'Keys', 'Wallets', 'Bags', 'Other']
        for cat_name in default_categories:
            category = Category(name=cat_name)
            db.session.add(category)
        
        db.session.commit()
        print("Inserted default categories.")
    else:
        print("Categories already exist.")
