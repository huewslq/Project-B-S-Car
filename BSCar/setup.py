
import os
import sys
from app import create_app, db
from app.models import User, Category, Listing, ListingImage

def setup_database():
    app = create_app()
    
    with app.app_context():
        print("🔧 Создание таблиц базы данных...")
        db.create_all()
        print("✅ Таблицы созданы")
        categories_count = Category.query.count()
        if categories_count == 0:
            print("📂 Добавление категорий...")
            categories = [
                'Новые',
                'Б/У'
            ]
            
            for cat_name in categories:
                category = Category(name=cat_name)
                db.session.add(category)
            
            db.session.commit()
            print(f"✅ Добавлено {len(categories)} категорий")
        else:
            print(f"✅ Категории уже существуют ({categories_count} шт.)")
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            print("👤 Создание тестового пользователя...")
            test_user = User(
                email='test@example.com',
                password_hash='test123',
                name='Тестовый Пользователь',
                role='user'
            )
            db.session.add(test_user)
            db.session.commit()
            print("✅ Тестовый пользователь создан")
        else:
            print("✅ Тестовый пользователь уже существует")
        listings_count = Listing.query.count()
        if listings_count == 0:
            print("📝 Создание тестовых объявлений...")
            new_category = Category.query.filter_by(name='Новые').first()
            used_category = Category.query.filter_by(name='Б/У').first()
            
            test_listings = [
                {
                    'title': 'BMW X5 2020 года',
                    'description': 'Отличное состояние, один владелец, полная комплектация. Пробег 45000 км.',
                    'price': 3500000,
                    'category_id': used_category.id if used_category else None,
                    'owner_id': test_user.id,
                    'status': 'active'
                },
                {
                    'title': 'Toyota Camry 2024',
                    'description': 'Новый автомобиль, полная гарантия, все опции включены.',
                    'price': 2800000,
                    'category_id': new_category.id if new_category else None,
                    'owner_id': test_user.id,
                    'status': 'active'
                },
                {
                    'title': 'Honda Civic 2024',
                    'description': 'Современный дизайн, экономичный двигатель, полная комплектация.',
                    'price': 2200000,
                    'category_id': new_category.id if new_category else None,
                    'owner_id': test_user.id,
                    'status': 'active'
                },
                {
                    'title': 'Audi A4 2019',
                    'description': 'Премиум седан, отличное состояние, один владелец.',
                    'price': 2400000,
                    'category_id': used_category.id if used_category else None,
                    'owner_id': test_user.id,
                    'status': 'active'
                }
            ]
            
            for listing_data in test_listings:
                listing = Listing(**listing_data)
                db.session.add(listing)
            
            db.session.commit()
            print(f"✅ Создано {len(test_listings)} тестовых объявлений")
        else:
            print(f"✅ Объявления уже существуют ({listings_count} шт.)")

def main():
    print("🚗 BSCar - Настройка системы")
    print("=" * 40)
    
    try:
        setup_database()
        print("\n🎉 Настройка завершена успешно!")
        print("\n📋 Информация для входа:")
        print("   Email: test@example.com")
        print("   Пароль: test123")
        print("\n🚀 Теперь запустите приложение:")
        print("   python run.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка при настройке: {e}")
        print("\n🔍 Возможные причины:")
        print("   1. Не настроена база данных MySQL")
        print("   2. Неверные параметры подключения в .env файле")
        print("   3. База данных 'bscar' не существует")
        sys.exit(1)

if __name__ == '__main__':
    main()
