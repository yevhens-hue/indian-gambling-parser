# main_parser_playwright.py

import argparse
import asyncio
from provider_parser_playwright import ProviderParserPlaywright
from storage import Storage
from merchants_config import MERCHANTS


async def main_async():
    parser = argparse.ArgumentParser(description="Парсер провайдеров гемблинговых сайтов (Playwright)")
    parser.add_argument("--merchant", type=str, help="ID мерчанта (например, 1xbet, dafabet)")
    parser.add_argument("--url", type=str, help="URL сайта мерчанта")
    parser.add_argument("--headless", action="store_true", help="Запуск в headless режиме")
    parser.add_argument("--list-merchants", action="store_true", help="Показать список доступных мерчантов")
    parser.add_argument("--show-results", action="store_true", help="Показать результаты из БД")
    parser.add_argument("--export-xlsx", type=str, help="Экспортировать результаты в XLSX (укажите путь)")
    
    args = parser.parse_args()
    
    if args.list_merchants:
        print("\nДоступные мерчанты:")
        for merchant_id, config in MERCHANTS.items():
            print(f"  - {merchant_id}: {config['brand']}")
            print(f"    Домены: {', '.join(config['official_domains'])}")
        return
    
    if args.show_results:
        storage = Storage()
        results = storage.get_all_providers(args.merchant if args.merchant else None)
        
        if not results:
            print("В БД нет записей")
            return
        
        print(f"\nНайдено записей: {len(results)}\n")
        print(f"{'Мерчант':<15} {'Домен':<30} {'Провайдер':<30} {'Тип':<10} {'Метод':<15}")
        print("-" * 120)
        
        for row in results:
            print(f"{row.get('merchant', 'N/A'):<15} {row.get('merchant_domain', 'N/A'):<30} {row.get('provider_domain', 'N/A'):<30} {row.get('account_type', 'N/A'):<10} {row.get('payment_method', 'N/A'):<15}")
            if row.get('screenshot_path'):
                print(f"  Скриншот: {row['screenshot_path']}")
        
        return
    
    if args.export_xlsx:
        storage = Storage()
        storage.export_to_xlsx(args.export_xlsx)
        return
    
    if not args.merchant or not args.url:
        print("❌ Необходимо указать --merchant и --url")
        print("Используйте --help для справки")
        return
    
    if args.merchant not in MERCHANTS:
        print(f"❌ Мерчант {args.merchant} не найден")
        print("Используйте --list-merchants для просмотра доступных мерчантов")
        return
    
    print(f"\n🚀 Запуск парсера для мерчанта: {args.merchant}")
    print(f"📍 URL: {args.url}")
    print(f"👁️  Headless режим: {'Да' if args.headless else 'Нет'}\n")
    
    parser_instance = ProviderParserPlaywright(headless=args.headless)
    result = await parser_instance.parse_merchant(args.merchant, args.url, args.headless)
    
    # Обработка результата в зависимости от статуса
    if isinstance(result, dict):
        status = result.get("status")
        
        if status == "LOGIN_ONLY_OK":
            # Summary для login-only flow (выводится только здесь)
            print("\n✅ Login-only flow завершён успешно.")
            print(f"  → Final URL: {result['meta']['final_url']}")
            print(f"  → StorageState: {result['meta']['storage_state_path']}")
            # Парсинг провайдеров и экспорты не выполняются для login-only
        elif status == "OK":
            providers = result.get("providers", [])
            if providers:
                print(f"\n✅ Успешно обработано провайдеров: {len(providers)}")
                for provider in providers:
                    print(f"  - {provider.get('provider_domain', 'N/A')} ({provider.get('provider_name', 'N/A')})")
                    if provider.get('final_url'):
                        print(f"    URL: {provider['final_url']}")
                # Экспорты выполняются только для OK статуса с провайдерами
            else:
                print("\n⚠️  Провайдеры не найдены")
        elif status == "ERROR":
            print(f"\n❌ Ошибка: {result.get('error', 'Unknown error')}")
        else:
            print(f"\n⚠️  Неизвестный статус результата: {status}")
    elif result:
        # Fallback для старого формата (список результатов)
        print(f"\n✅ Успешно обработано провайдеров: {len(result)}")
        for provider in result:
            print(f"  - {provider.get('provider_domain', 'N/A')} ({provider.get('provider_name', 'N/A')})")
            if provider.get('final_url'):
                print(f"    URL: {provider['final_url']}")
    else:
        print("\n⚠️  Провайдеры не найдены или не удалось их обработать")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

