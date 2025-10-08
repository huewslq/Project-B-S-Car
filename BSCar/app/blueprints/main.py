from __future__ import annotations

import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_from_directory
from .. import db
from ..models import Listing, Favorite, Chat, User, Category, ListingImage, Message, Complaint, SupportTicket


bp = Blueprint('main', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, listing_id):
    if file and allowed_file(file.filename):
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{listing_id}_{uuid.uuid4().hex}.{file_ext}"
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'listings')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        return unique_filename
    return None


@bp.get('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    category_filter = request.args.get('category', 'all')
    search_query = request.args.get('search', '').strip()
    query = db.select(Listing).options(db.joinedload(Listing.images))
    if search_query:
        query = query.where(Listing.title.ilike(f'%{search_query}%'))
    if category_filter == 'new':
        new_category = db.session.execute(db.select(Category).where(Category.name == 'Новые')).scalar_one_or_none()
        if new_category:
            query = query.where(Listing.category_id == new_category.id)
    elif category_filter == 'used':
        used_category = db.session.execute(db.select(Category).where(Category.name == 'Б/У')).scalar_one_or_none()
        if used_category:
            query = query.where(Listing.category_id == used_category.id)
    
    listings = db.session.execute(
        query.order_by(Listing.created_at.desc())
    ).scalars().unique().all()
    new_category = db.session.execute(db.select(Category).where(Category.name == 'Новые')).scalar_one_or_none()
    used_category = db.session.execute(db.select(Category).where(Category.name == 'Б/У')).scalar_one_or_none()
    
    base_conditions = []
    if search_query:
        base_conditions.append(Listing.title.ilike(f'%{search_query}%'))
    
    all_count_query = db.select(db.func.count(Listing.id))
    if base_conditions:
        all_count_query = all_count_query.where(*base_conditions)
    
    new_count_query = db.select(db.func.count(Listing.id))
    if new_category:
        new_conditions = [Listing.category_id == new_category.id]
        if base_conditions:
            new_conditions.extend(base_conditions)
        new_count_query = new_count_query.where(*new_conditions)
    else:
        new_count_query = db.select(db.func.count(Listing.id)).where(False)
    
    used_count_query = db.select(db.func.count(Listing.id))
    if used_category:
        used_conditions = [Listing.category_id == used_category.id]
        if base_conditions:
            used_conditions.extend(base_conditions)
        used_count_query = used_count_query.where(*used_conditions)
    else:
        used_count_query = db.select(db.func.count(Listing.id)).where(False)
    
    stats = {
        'all': db.session.execute(all_count_query).scalar() or 0,
        'new': db.session.execute(new_count_query).scalar() or 0,
        'used': db.session.execute(used_count_query).scalar() or 0
    }
    
    return render_template('index.html', 
                         title='BSCar', 
                         mode='listings', 
                         listings=listings, 
                         current_filter=category_filter, 
                         search_query=search_query,
                         stats=stats)


@bp.get('/favorites')
def favorites():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user_id = session['user_id']
    listings = []
    if user_id:
        listings = (
            db.session.execute(
                db.select(Listing)
                .options(db.joinedload(Listing.images))
                .join(Favorite, Favorite.listing_id == Listing.id)
                .where(Favorite.user_id == user_id)
                .order_by(Listing.created_at.desc())
            ).scalars().unique().all()
        )
    return render_template('index.html', title='Избранное', mode='favorites', listings=listings)


@bp.get('/chats')
def chats():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user_id = session['user_id']
    threads = []
    if user_id:
        threads = (
            db.session.execute(
                db.select(Chat)
                .options(db.joinedload(Chat.listing), db.joinedload(Chat.buyer), db.joinedload(Chat.seller))
                .where((Chat.buyer_id == user_id) | (Chat.seller_id == user_id))
                .order_by(Chat.updated_at.desc())
            ).scalars().unique().all()
        )
    return render_template('index.html', title='Чаты', mode='chats', chats=threads)


@bp.get('/chats/<int:chat_id>')
def view_chat(chat_id):
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    
    chat = db.session.execute(
        db.select(Chat)
        .options(
            db.joinedload(Chat.listing),
            db.joinedload(Chat.buyer),
            db.joinedload(Chat.seller),
            db.joinedload(Chat.messages).joinedload(Message.author)
        )
        .where(Chat.id == chat_id)
    ).scalars().unique().first()
    
    if not chat:
        flash('Чат не найден')
        return redirect(url_for('main.chats'))
    
    if chat.buyer_id != user_id and chat.seller_id != user_id:
        flash('У вас нет доступа к этому чату')
        return redirect(url_for('main.chats'))
    
    if chat.buyer_id == user_id:
        other_user = chat.seller
    else:
        other_user = chat.buyer
    
    return render_template('index.html', 
                         title=f'Чат с {other_user.name or other_user.email}', 
                         mode='chat_detail', 
                         chat=chat, 
                         other_user=other_user)


@bp.post('/chats/<int:chat_id>/message')
def send_message(chat_id):
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Сообщение не может быть пустым')
        return redirect(url_for('main.view_chat', chat_id=chat_id))
    
    chat = db.session.get(Chat, chat_id)
    if not chat:
        flash('Чат не найден')
        return redirect(url_for('main.chats'))
    
    if chat.buyer_id != user_id and chat.seller_id != user_id:
        flash('У вас нет доступа к этому чату')
        return redirect(url_for('main.chats'))
    
    message = Message(
        chat_id=chat_id,
        author_id=user_id,
        content=content
    )
    db.session.add(message)
    
    chat.updated_at = db.func.now()
    
    db.session.commit()
    
    return redirect(url_for('main.view_chat', chat_id=chat_id))


@bp.get('/account')
def account():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = db.session.get(User, session['user_id'])
    return render_template('account.html', title='Аккаунт', user=user)

@bp.get('/account/edit')
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = db.session.get(User, session['user_id'])
    return render_template('index.html', title='Изменить профиль', mode='account_edit', user=user)

@bp.post('/account/edit')
def edit_profile_post():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = db.session.get(User, session['user_id'])
    if not user:
        flash('Пользователь не найден')
        return redirect(url_for('main.login'))

    name = request.form.get('name')
    email = request.form.get('email')
    avatar_file = request.files.get('avatar')

    if name:
        user.name = name
    if email:
        existing = db.session.execute(db.select(User).where(User.email == email, User.id != user.id)).scalar_one_or_none()
        if existing:
            flash('Почта уже используется другим пользователем')
            return redirect(url_for('main.edit_profile'))
        user.email = email

    if avatar_file and avatar_file.filename:
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'avatars')
        os.makedirs(upload_folder, exist_ok=True)
        ext = avatar_file.filename.rsplit('.', 1)[-1].lower()
        filename = f"user_{user.id}_{uuid.uuid4().hex}.{ext}"
        avatar_file.save(os.path.join(upload_folder, filename))
        user.avatar_filename = filename

    db.session.commit()
    flash('Профиль обновлён', 'success')
    return redirect(url_for('main.account'))

@bp.get('/admin')
def admin_panel():
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    listings = db.session.execute(
        db.select(Listing).order_by(Listing.created_at.desc()).limit(20)
    ).scalars().all()
    return render_template('index.html', title='Админ-панель', mode='admin', listings=listings)


@bp.get('/my-listings')
def my_listings():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user_id = session['user_id']
    listings = []
    if user_id:
        listings = (
            db.session.execute(
                db.select(Listing)
                .options(db.joinedload(Listing.images))
                .where(Listing.owner_id == user_id)
                .order_by(Listing.created_at.desc())
            ).scalars().unique().all()
        )
    return render_template('index.html', title='Мои объявления', mode='my', listings=listings)


@bp.get('/listings/new')
def new_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    categories = db.session.execute(db.select(Category)).scalars().all()
    return render_template('index.html', title='Создать объявление', mode='new', categories=categories)


@bp.post('/listings/new')
def create_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')
    category_id = request.form.get('category_id')
    
    if not title or not price:
        flash('Название и цена обязательны для заполнения')
        return redirect(url_for('main.new_listing'))
    
    try:
        price = float(price)
    except ValueError:
        flash('Неверный формат цены')
        return redirect(url_for('main.new_listing'))
    
    listing = Listing(
        title=title,
        description=description,
        price=price,
        category_id=int(category_id) if category_id else None,
        owner_id=session['user_id'],
        status='active'
    )
    
    db.session.add(listing)
    db.session.flush()
    
    uploaded_files = request.files.getlist('images')
    primary_image_set = False
    
    for i, file in enumerate(uploaded_files):
        if file and file.filename:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                flash(f'Файл {file.filename} слишком большой (максимум 5MB)')
                continue
            
            filename = save_uploaded_file(file, listing.id)
            if filename:
                is_primary = not primary_image_set
                primary_image_set = True
                
                image = ListingImage(
                    listing_id=listing.id,
                    filename=filename,
                    original_filename=file.filename,
                    file_size=file_size,
                    is_primary=is_primary
                )
                db.session.add(image)
    
    db.session.commit()
    
    flash('Объявление успешно создано!', 'success')
    return redirect(url_for('main.my_listings'))


@bp.get('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Вход')


@bp.post('/login')
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if user and user.password_hash == password:
        session['user_id'] = user.id
        return redirect(url_for('main.index'))
    else:
        flash('Неверный email или пароль')
        return redirect(url_for('main.login'))


@bp.get('/register')
def register():
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    return render_template('register.html', title='Регистрация')


@bp.post('/register')
def register_post():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    avatar_file = request.files.get('avatar')
    
    existing = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        flash('Пользователь с таким email уже существует')
        return redirect(url_for('main.register'))
    
    user = User(email=email, password_hash=password, name=name, role='user')
    if avatar_file and avatar_file.filename:
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'avatars')
        os.makedirs(upload_folder, exist_ok=True)
        ext = avatar_file.filename.rsplit('.', 1)[-1].lower()
        filename = f"user_{uuid.uuid4().hex}.{ext}"
        avatar_path = os.path.join(upload_folder, filename)
        avatar_file.save(avatar_path)
        user.avatar_filename = filename
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    return redirect(url_for('main.index'))


@bp.get('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.login'))


@bp.get('/listings/<int:listing_id>')
def view_listing(listing_id):
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    listing = db.session.execute(
        db.select(Listing)
        .options(
            db.joinedload(Listing.images),
            db.joinedload(Listing.category),
            db.joinedload(Listing.owner)
        )
        .where(Listing.id == listing_id)
    ).scalars().unique().first()
    
    if not listing:
        flash('Объявление не найдено')
        return redirect(url_for('main.index'))
    
    user_id = session['user_id']
    is_favorited = False
    if user_id:
        favorite = db.session.execute(
            db.select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.listing_id == listing_id
            )
        ).scalar_one_or_none()
        is_favorited = favorite is not None
    
    return render_template('index.html', 
                         title=listing.title, 
                         mode='listing_detail', 
                         listing=listing, 
                         is_favorited=is_favorited)


@bp.post('/listings/<int:listing_id>/favorite')
def toggle_favorite(listing_id):
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    
    listing = db.session.get(Listing, listing_id)
    if not listing:
        flash('Объявление не найдено')
        return redirect(url_for('main.index'))
    
    favorite = db.session.execute(
        db.select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.listing_id == listing_id
        )
    ).scalar_one_or_none()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash('Объявление удалено из избранного')
    else:
        favorite = Favorite(user_id=user_id, listing_id=listing_id)
        db.session.add(favorite)
        db.session.commit()
        flash('Объявление добавлено в избранное')
    
    return redirect(url_for('main.view_listing', listing_id=listing_id))


@bp.post('/listings/<int:listing_id>/contact')
def contact_seller(listing_id):
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    
    listing = db.session.get(Listing, listing_id)
    if not listing:
        flash('Объявление не найдено')
        return redirect(url_for('main.index'))
    
    if listing.owner_id == user_id:
        flash('Нельзя написать самому себе')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    existing_chat = db.session.execute(
        db.select(Chat).where(
            Chat.listing_id == listing_id,
            Chat.buyer_id == user_id,
            Chat.seller_id == listing.owner_id
        )
    ).scalar_one_or_none()
    
    if existing_chat:
        flash('Чат с этим продавцом уже существует')
        return redirect(url_for('main.chats'))
    
    chat = Chat(
        listing_id=listing_id,
        buyer_id=user_id,
        seller_id=listing.owner_id
    )
    db.session.add(chat)
    db.session.commit()
    
    flash('Чат с продавцом создан!', 'success')
    return redirect(url_for('main.chats'))


@bp.post('/admin/add-admin')
def add_admin():
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    
    email = request.form.get('email')
    if not email:
        flash('Email обязателен')
        return redirect(url_for('main.admin_panel'))
    
    target_user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if not target_user:
        flash('Пользователь не найден')
        return redirect(url_for('main.admin_panel'))
    
    if target_user.role == 'admin':
        flash('Пользователь уже является админом')
        return redirect(url_for('main.admin_panel'))
    
    target_user.role = 'admin'
    db.session.commit()
    
    flash(f'Пользователь {target_user.name or target_user.email} назначен админом', 'success')
    return redirect(url_for('main.admin_panel'))


@bp.post('/admin/block-user')
def block_user():
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    
    email = request.form.get('email')
    reason = request.form.get('reason')
    
    if not email or not reason:
        flash('Email и причина обязательны')
        return redirect(url_for('main.admin_panel'))
    
    target_user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if not target_user:
        flash('Пользователь не найден')
        return redirect(url_for('main.admin_panel'))
    
    if target_user.role == 'admin':
        flash('Нельзя заблокировать админа')
        return redirect(url_for('main.admin_panel'))
    
    target_user.role = 'blocked'
    db.session.commit()
    
    flash(f'Пользователь {target_user.name or target_user.email} заблокирован', 'success')
    return redirect(url_for('main.admin_panel'))


@bp.post('/admin/delete-listing')
def delete_listing():
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    
    listing_id = request.form.get('listing_id')
    reason = request.form.get('reason')
    
    if not listing_id or not reason:
        flash('ID объявления и причина обязательны')
        return redirect(url_for('main.admin_panel'))
    
    try:
        listing_id = int(listing_id)
    except ValueError:
        flash('Неверный ID объявления')
        return redirect(url_for('main.admin_panel'))
    
    listing = db.session.get(Listing, listing_id)
    if not listing:
        flash('Объявление не найдено')
        return redirect(url_for('main.admin_panel'))
    
    listing_title = listing.title
    
    chats = db.session.execute(
        db.select(Chat).where(Chat.listing_id == listing_id)
    ).scalars().all()
    
    for chat in chats:
        db.session.execute(
            db.delete(Message).where(Message.chat_id == chat.id)
        )
    
    db.session.execute(
        db.delete(Chat).where(Chat.listing_id == listing_id)
    )
    
    db.session.execute(
        db.delete(Complaint).where(Complaint.listing_id == listing_id)
    )
    
    db.session.execute(
        db.delete(Favorite).where(Favorite.listing_id == listing_id)
    )
    
    db.session.execute(
        db.delete(ListingImage).where(ListingImage.listing_id == listing_id)
    )
    
    db.session.delete(listing)
    db.session.commit()
    
    flash(f'Объявление "{listing_title}" удалено', 'success')
    return redirect(url_for('main.admin_panel'))


@bp.post('/listings/<int:listing_id>/report')
def report_listing(listing_id):
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    
    listing = db.session.get(Listing, listing_id)
    if not listing:
        flash('Объявление не найдено')
        return redirect(url_for('main.index'))
    
    if listing.owner_id == user_id:
        flash('Нельзя жаловаться на свои объявления')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    existing_complaint = db.session.execute(
        db.select(Complaint).where(
            Complaint.listing_id == listing_id,
            Complaint.submitter_id == user_id
        )
    ).scalar_one_or_none()
    
    if existing_complaint:
        flash('Вы уже жаловались на это объявление')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    complaint = Complaint(
        listing_id=listing_id,
        submitter_id=user_id,
        reason='Жалоба от пользователя',
        status='pending'
    )
    db.session.add(complaint)
    db.session.commit()
    
    flash('Жалоба отправлена администраторам', 'success')
    return redirect(url_for('main.view_listing', listing_id=listing_id))


@bp.post('/admin/delete-listing-direct')
def delete_listing_admin():
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    
    listing_id = request.form.get('listing_id')
    reason = request.form.get('reason', 'Удалено администратором')
    
    if not listing_id:
        flash('ID объявления обязателен')
        return redirect(url_for('main.index'))
    
    try:
        listing_id = int(listing_id)
    except ValueError:
        flash('Неверный ID объявления')
        return redirect(url_for('main.index'))
    
    listing = db.session.get(Listing, listing_id)
    if not listing:
        flash('Объявление не найдено')
        return redirect(url_for('main.index'))
    
    listing_title = listing.title
    
    chats = db.session.execute(
        db.select(Chat).where(Chat.listing_id == listing_id)
    ).scalars().all()
    
    for chat in chats:
        db.session.execute(
            db.delete(Message).where(Message.chat_id == chat.id)
        )
    
    db.session.execute(
        db.delete(Chat).where(Chat.listing_id == listing_id)
    )
    
    db.session.execute(
        db.delete(Complaint).where(Complaint.listing_id == listing_id)
    )
    
    db.session.execute(
        db.delete(Favorite).where(Favorite.listing_id == listing_id)
    )
    
    db.session.execute(
        db.delete(ListingImage).where(ListingImage.listing_id == listing_id)
    )
    
    db.session.delete(listing)
    db.session.commit()
    
    flash(f'Объявление "{listing_title}" удалено', 'success')
    return redirect(url_for('main.index'))


@bp.get('/support')
def support():
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = db.session.get(User, session['user_id'])
    if not user:
        return redirect(url_for('main.login'))
    
    if user.role == 'admin':
        support_tickets = db.session.execute(
            db.select(SupportTicket)
            .options(db.joinedload(SupportTicket.user))
            .order_by(SupportTicket.created_at.desc())
        ).scalars().all()
        return render_template('index.html', 
                             title='Техподдержка', 
                             mode='support', 
                             support_tickets=support_tickets)
    else:
        user_tickets = db.session.execute(
            db.select(SupportTicket)
            .where(SupportTicket.user_id == user.id)
            .order_by(SupportTicket.created_at.desc())
        ).scalars().all()
        return render_template('index.html', 
                             title='Техподдержка', 
                             mode='support', 
                             user_tickets=user_tickets)


@bp.post('/support/create')
def create_support_ticket():
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if not subject or not message:
        flash('Тема и сообщение обязательны')
        return redirect(url_for('main.support'))
    
    ticket = SupportTicket(
        user_id=user_id,
        subject=subject,
        message=message,
        status='pending'
    )
    db.session.add(ticket)
    db.session.commit()
    
    flash('Обращение отправлено в техподдержку', 'success')
    return redirect(url_for('main.support'))


@bp.post('/support/<int:ticket_id>/reply')
def reply_support(ticket_id):
    
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = db.session.get(User, session['user_id'])
    if not user or user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    
    ticket = db.session.get(SupportTicket, ticket_id)
    if not ticket:
        flash('Обращение не найдено')
        return redirect(url_for('main.support'))
    
    reply = request.form.get('reply')
    if not reply:
        flash('Ответ не может быть пустым')
        return redirect(url_for('main.support'))
    
    ticket.reply = reply
    ticket.status = 'answered'
    db.session.commit()
    
    flash('Ответ отправлен пользователю', 'success')
    return redirect(url_for('main.support'))


@bp.get('/uploads/listings/<filename>')
def uploaded_file(filename):
    
    return send_from_directory(
        os.path.join(current_app.static_folder, 'uploads', 'listings'),
        filename
    )
