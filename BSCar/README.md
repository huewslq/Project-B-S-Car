# BSCar - Продажа машин

## Что нужно для запуска

1. Python 3.8+
2. MySQL база данных

## Как запустить

### 1. Установить зависимости
```bash
pip install -r requirements.txt
```

### 2. Настроить базу данных
Создай файл `.env` в папке проекта:
```
SECRET_KEY=твой-секретный-ключ
DATABASE_URL=mysql+pymysql://пользователь:пароль@localhost:3306/bscar
```

### 3. Создать базу данных
```bash
python3 create_empty_db.py
```

### 4. Запустить приложение
```bash
python3 run.py
```