#!/usr/bin/env python3
"""
Тестирование API импорта данных из Google Sheets
"""
import requests
import json
import sys

API_URL = "http://localhost:8000/api"

def test_preview():
    """Тест предпросмотра данных"""
    print("=" * 60)
    print("Тест 1: Предпросмотр данных")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{API_URL}/import/google-sheets/preview",
            params={"gid": "396039446", "limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Предпросмотр успешен!")
            print(f"   Найдено записей: {data.get('total_found', 0)}")
            print(f"   Показано: {data.get('preview_count', 0)}")
            print(f"\n   Примеры данных:")
            for i, item in enumerate(data.get('preview', [])[:3], 1):
                print(f"     {i}. {item.get('provider_domain')} ({item.get('merchant')}) - {item.get('account_type')}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend не запущен на http://localhost:8000")
        print("   Запустите: cd web_service/backend && python3 start.py")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_import():
    """Тест импорта данных"""
    print("\n" + "=" * 60)
    print("Тест 2: Импорт данных в БД")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{API_URL}/import/google-sheets",
            params={"gid": "396039446"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Импорт успешен!")
            print(f"   Статус: {data.get('status')}")
            print(f"   Сообщение: {data.get('message')}")
            print(f"   Импортировано: {data.get('imported', 0)}")
            print(f"   Пропущено (дубликаты): {data.get('skipped', 0)}")
            print(f"   Ошибок: {data.get('errors', 0)}")
            if 'total' in data:
                print(f"   Всего найдено: {data.get('total', 0)}")
            return True, data
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False, None

def test_verify_data():
    """Проверка импортированных данных"""
    print("\n" + "=" * 60)
    print("Тест 3: Проверка данных в БД")
    print("=" * 60)
    
    try:
        # Получаем провайдеров для 1win
        response = requests.get(
            f"{API_URL}/providers",
            params={"merchant": "1win", "limit": 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            providers = data.get('providers', [])
            
            print(f"✅ Данные найдены в БД!")
            print(f"   Всего провайдеров 1win: {total}")
            print(f"   Показано: {len(providers)}")
            
            if providers:
                print(f"\n   Примеры импортированных данных:")
                for i, p in enumerate(providers[:5], 1):
                    print(f"     {i}. {p.get('provider_domain')} - {p.get('account_type')} - {p.get('payment_method')}")
            
            return True, total
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False, 0

def main():
    """Основная функция тестирования"""
    print("\n🧪 Тестирование API импорта данных 1win IN\n")
    
    # Тест 1: Предпросмотр
    preview_ok = test_preview()
    if not preview_ok:
        print("\n⚠️  Предпросмотр не работает. Проверьте настройки Google Sheets API.")
        sys.exit(1)
    
    # Тест 2: Импорт
    import_ok, import_result = test_import()
    if not import_ok:
        print("\n⚠️  Импорт не работает.")
        sys.exit(1)
    
    # Тест 3: Проверка данных
    verify_ok, total_count = test_verify_data()
    if not verify_ok:
        print("\n⚠️  Проверка данных не работает.")
        sys.exit(1)
    
    # Итоги
    print("\n" + "=" * 60)
    print("🎉 Все тесты пройдены успешно!")
    print("=" * 60)
    print(f"✅ Предпросмотр: работает")
    print(f"✅ Импорт: {import_result.get('imported', 0)} записей импортировано")
    print(f"✅ Проверка БД: {total_count} записей найдено в БД")
    print("\n💡 Данные доступны в веб-сервисе:")
    print("   http://localhost:5173")
    print("\n💡 API документация:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
