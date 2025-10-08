from __future__ import annotations

from datetime import datetime
from . import db


class TimestampMixin:
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(db.Model, TimestampMixin):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(255), unique=True, nullable=False)
	password_hash = db.Column(db.String(255), nullable=False)
	name = db.Column(db.String(120))
	role = db.Column(db.String(32), default='user', nullable=False)
	avatar_filename = db.Column(db.String(255))

	listings = db.relationship('Listing', back_populates='owner', cascade='all, delete-orphan')
	favorites = db.relationship('Favorite', back_populates='user', cascade='all, delete-orphan')
	messages = db.relationship('Message', back_populates='author', cascade='all, delete-orphan')


class Category(db.Model):
	__tablename__ = 'categories'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=True, nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
	parent = db.relationship('Category', remote_side=[id])

	listings = db.relationship('Listing', back_populates='category')


class Listing(db.Model, TimestampMixin):
	__tablename__ = 'listings'

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	description = db.Column(db.Text)
	price = db.Column(db.Numeric(12, 2))
	status = db.Column(db.String(32), default='active', nullable=False)

	owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

	owner = db.relationship('User', back_populates='listings')
	category = db.relationship('Category', back_populates='listings')
	favorited_by = db.relationship('Favorite', back_populates='listing', cascade='all, delete-orphan')
	complaints = db.relationship('Complaint', back_populates='listing', cascade='all, delete-orphan')
	images = db.relationship('ListingImage', back_populates='listing', cascade='all, delete-orphan')


class Favorite(db.Model, TimestampMixin):
	__tablename__ = 'favorites'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)

	user = db.relationship('User', back_populates='favorites')
	listing = db.relationship('Listing', back_populates='favorited_by')

	__table_args__ = (db.UniqueConstraint('user_id', 'listing_id', name='uq_favorite'),)


class Chat(db.Model, TimestampMixin):
	__tablename__ = 'chats'

	id = db.Column(db.Integer, primary_key=True)
	listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
	buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

	listing = db.relationship('Listing')
	buyer = db.relationship('User', foreign_keys=[buyer_id])
	seller = db.relationship('User', foreign_keys=[seller_id])
	messages = db.relationship('Message', back_populates='chat', cascade='all, delete-orphan')

	__table_args__ = (db.UniqueConstraint('listing_id', 'buyer_id', 'seller_id', name='uq_chat_triplet'),)


class Message(db.Model, TimestampMixin):
	__tablename__ = 'messages'

	id = db.Column(db.Integer, primary_key=True)
	chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	content = db.Column(db.Text, nullable=False)

	chat = db.relationship('Chat', back_populates='messages')
	author = db.relationship('User', back_populates='messages')


class Complaint(db.Model, TimestampMixin):
	__tablename__ = 'complaints'

	id = db.Column(db.Integer, primary_key=True)
	listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
	submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	reason = db.Column(db.String(255), nullable=False)
	status = db.Column(db.String(32), default='pending', nullable=False)

	listing = db.relationship('Listing', back_populates='complaints')
	submitter = db.relationship('User')


class ModerationAction(db.Model, TimestampMixin):
	__tablename__ = 'moderation_actions'

	id = db.Column(db.Integer, primary_key=True)
	listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'))
	moderator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	action = db.Column(db.String(64), nullable=False)
	details = db.Column(db.Text)

	listing = db.relationship('Listing')
	moderator = db.relationship('User')


class ListingImage(db.Model, TimestampMixin):
	__tablename__ = 'listing_images'

	id = db.Column(db.Integer, primary_key=True)
	listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
	filename = db.Column(db.String(255), nullable=False)
	original_filename = db.Column(db.String(255), nullable=False)
	file_size = db.Column(db.Integer)
	is_primary = db.Column(db.Boolean, default=False, nullable=False)

	listing = db.relationship('Listing', back_populates='images')


class SupportTicket(db.Model, TimestampMixin):
	__tablename__ = 'support_tickets'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	subject = db.Column(db.String(255), nullable=False)
	message = db.Column(db.Text, nullable=False)
	reply = db.Column(db.Text)
	status = db.Column(db.String(32), default='pending', nullable=False)

	user = db.relationship('User')


