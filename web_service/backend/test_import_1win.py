#!/usr/bin/env python3
"""
Тестовый скрипт для проверки импорта данных 1win IN из Google Sheets
"""
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from app.services.google_sheets_importer import GoogleSheetsImporter

def test_import_1win():
    """Тест импорта данных 1win IN"""
    
    print("=" * 60)
    print("Тест импорта данных 1win IN из Google Sheets")
    print("=" * 60)
    print(f"GID листа: 396039446")
    print(f"URL: https://docs.google.com/spreadsheets/d/1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE/edit?gid=396039446")
    print()
    
    try:
        importer = GoogleSheetsImporter()
        print("✓ Импортер инициализирован")
        
        # Тест предпросмотра
        print("\n📋 Предпросмотр данных (первые 5 записей)...")
        providers = importer.parse_google_sheets_data(gid="396039446")
        
        if not providers:
            print("⚠️  Нет данных для импорта")
            print("\nВозможные причины:")
            print("1. Лист пустой")
            print("2. Неправильный GID")
            print("3. Проблемы с доступом к Google Sheets")
            return False
        
        print(f"✓ Найдено записей: {len(providers)}")
        
        # Показываем первые 3 записи
        print("\n📊 Примеры данных (первые 3 записи):")
        for i, provider in enumerate(providers[:3], 1):
            print(f"\n  {i}. Провайдер: {provider.get('provider_domain')}")
            print(f"     Merchant: {provider.get('merchant')}")
            print(f"     Account Type: {provider.get('account_type')}")
            print(f"     Payment Method: {provider.get('payment_method')}")
            print(f"     Provider Name: {provider.get('provider_name')}")
            print(f"     Entry URL: {provider.get('provider_entry_url', '')[:60]}...")
        
        # Тест импорта (только предпросмотр, без сохранения)
        print(f"\n✅ Предпросмотр успешен!")
        print(f"   Всего записей: {len(providers)}")
        print(f"\n💡 Для импорта в БД используйте:")
        print(f"   curl -X POST 'http://localhost:8000/api/import/google-sheets?gid=396039446'")
        print(f"\n   Или через веб-интерфейс:")
        print(f"   http://localhost:5173 (найдите блок 'Импорт данных из Google Sheets')")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ Ошибка: {e}")
        print("\n📋 Убедитесь, что файл google_credentials.json существует")
        print("   См. GOOGLE_SHEETS_SETUP.md для инструкций")
        return False
        
    except Exception as e:
        print(f"\n❌ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import_1win()
    sys.exit(0 if success else 1)
