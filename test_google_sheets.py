#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Google Sheets
"""

import os
import sys
from storage import Storage

def test_google_sheets():
    """Тест подключения к Google Sheets"""
    
    # ID таблицы из URL
    sheet_id = "1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE"
    credentials_path = "google_credentials.json"
    
    print("=" * 60)
    print("Тест подключения к Google Sheets")
    print("=" * 60)
    
    # Проверка наличия файла credentials
    if not os.path.exists(credentials_path):
        print(f"\n❌ Файл {credentials_path} не найден!")
        print("\n📋 Инструкция по созданию:")
        print("1. Перейдите в https://console.cloud.google.com/")
        print("2. Создайте проект или выберите существующий")
        print("3. Включите Google Sheets API и Google Drive API")
        print("4. Создайте Service Account (APIs & Services → Credentials)")
        print("5. Скачайте JSON ключ и сохраните как google_credentials.json")
        print("6. Добавьте email из JSON (поле client_email) в редакторы таблицы")
        print("\nПодробная инструкция: см. GOOGLE_SHEETS_SETUP.md")
        return False
    
    print(f"✓ Файл {credentials_path} найден")
    
    # Инициализация Storage
    try:
        storage = Storage(
            google_sheet_id=sheet_id,
            google_credentials_path=credentials_path
        )
        print(f"✓ Storage инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации Storage: {e}")
        return False
    
    # Тест экспорта
    try:
        print("\n→ Тест экспорта данных...")
        storage.export_to_xlsx()
        print("✓ Экспорт выполнен успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_sheets()
    sys.exit(0 if success else 1)



