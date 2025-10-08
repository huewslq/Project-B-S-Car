#!/usr/bin/env python3

import os
import sys
from app import create_app, db

def create_empty_database():
    """Создает пустую базу данных без каких-либо данных"""
    app = create_app()
    
    with app.app_context():
        print("Создание базы данных...")
        
        try:
            db.create_all()
            print("БД создана успешно")
            
        except Exception as e:
            print(f"Ошибка при создании базы данных: {e}")
            sys.exit(1)

def main():
    print("Создание базы данных")
    print("=" * 40)
    
    try:
        create_empty_database()
        print("База данных создана")
        
    except Exception as e:
        print(f"\nОшибка при создании базы данных: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
