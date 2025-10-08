from __future__ import annotations

import os
from flask import Flask, session
from sqlalchemy import inspect, text
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()


db = SQLAlchemy()
migrate = Migrate()


def create_app(test_config: dict | None = None) -> Flask:
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
		SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'mysql+pymysql://user:password@localhost:3306/bscar'),
		SQLALCHEMY_TRACK_MODIFICATIONS=False,
	)

	if test_config is None:
		app.config.from_pyfile('config.py', silent=True)
	else:
		app.config.update(test_config)

	try:
		os.makedirs(app.instance_path, exist_ok=True)
	except OSError:
		pass

	db.init_app(app)
	migrate.init_app(app, db)

	@app.context_processor
	def inject_auth_flags():
		from .models import User
		is_admin = False
		current_user = None
		user_id = session.get('user_id')
		if user_id:
			current_user = db.session.get(User, user_id)
			if current_user and current_user.role == 'admin':
				is_admin = True
		return dict(is_admin=is_admin, current_user=current_user)

	from .blueprints.main import bp as main_bp
	from . import models
	app.register_blueprint(main_bp)

	@app.cli.command('init-db')
	def init_db_command():
		
		with app.app_context():
			db.create_all()

	@app.cli.command('init-categories')
	def init_categories_command():
		
		from .models import Category
		with app.app_context():
			categories = [
				'Новые',
				'Б/У'
			]
			
			for cat_name in categories:
				existing = Category.query.filter_by(name=cat_name).first()
				if not existing:
					category = Category(name=cat_name)
					db.session.add(category)
					print(f"Added category: {cat_name}")
			
			db.session.commit()
			print("Categories initialized successfully!")

	@app.cli.command('upgrade-schema')
	def upgrade_schema_command():
		
		from .models import User
		with app.app_context():
			inspector = inspect(db.engine)
			columns = [col['name'] for col in inspector.get_columns('users')]
			if 'avatar_filename' not in columns:
				print('Adding users.avatar_filename ...')
				db.session.execute(text('ALTER TABLE users ADD COLUMN avatar_filename VARCHAR(255) NULL'))
				db.session.commit()
				print('Done.')
			else:
				print('users.avatar_filename already exists. Nothing to do.')

	return app
