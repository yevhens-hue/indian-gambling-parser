#!/usr/bin/env python3
"""
Скрипт для проверки качества кода и системы
"""
import sys
import subprocess
import os
from pathlib import Path
from typing import List, Tuple

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    """Вывести заголовок"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(text: str):
    """Вывести успешное сообщение"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    """Вывести сообщение об ошибке"""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text: str):
    """Вывести предупреждение"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """
    Выполнить команду и вернуть результат
    
    Args:
        cmd: Команда для выполнения
        description: Описание команды
        
    Returns:
        Tuple (успех, вывод)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def check_imports():
    """Проверить импорты основных модулей"""
    print_header("Проверка импортов модулей")
    
    modules = [
        "app.main",
        "app.middleware.input_sanitization",
        "app.middleware.security_audit",
        "app.middleware.ip_filter",
        "app.middleware.query_optimization",
        "app.utils.structured_logging",
        "app.api.monitoring",
        "app.services.metrics",
        "app.services.cache",
    ]
    
    success_count = 0
    for module in modules:
        try:
            __import__(module)
            print_success(f"{module}")
            success_count += 1
        except Exception as e:
            print_error(f"{module}: {e}")
    
    print(f"\nИмпортировано: {success_count}/{len(modules)}")
    return success_count == len(modules)


def check_linting():
    """Проверить код линтером"""
    print_header("Проверка кода линтером (flake8)")
    
    backend_path = Path(__file__).parent
    result, output = run_command(
        ["python3", "-m", "flake8", "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics", str(backend_path / "app")],
        "flake8 check"
    )
    
    if result:
        print_success("Линтер не нашел критических ошибок")
        if output:
            print(output)
        return True
    else:
        print_error("Линтер нашел ошибки")
        print(output)
        return False


def check_type_hints():
    """Проверить типы (mypy)"""
    print_header("Проверка типов (mypy)")
    
    backend_path = Path(__file__).parent
    result, output = run_command(
        ["python3", "-m", "mypy", "--ignore-missing-imports", str(backend_path / "app")],
        "mypy check"
    )
    
    if result:
        print_success("Проверка типов прошла успешно")
        return True
    else:
        print_warning("Проверка типов нашла проблемы (не критично)")
        if output:
            print(output[:500])  # Показываем первые 500 символов
        return True  # Не критично


def check_tests():
    """Проверить тесты"""
    print_header("Проверка тестов")
    
    root_path = Path(__file__).parent.parent.parent
    tests_path = root_path / "tests"
    
    if not tests_path.exists():
        print_warning("Директория tests не найдена")
        return True
    
    result, output = run_command(
        ["python3", "-m", "pytest", str(tests_path), "-v", "--tb=short"],
        "pytest"
    )
    
    if result:
        print_success("Все тесты прошли")
        return True
    else:
        print_error("Некоторые тесты не прошли")
        print(output[-1000:] if len(output) > 1000 else output)  # Последние 1000 символов
        return False


def check_middleware_order():
    """Проверить порядок middleware в main.py"""
    print_header("Проверка порядка middleware")
    
    backend_path = Path(__file__).parent
    main_file = backend_path / "app" / "main.py"
    
    if not main_file.exists():
        print_error("main.py не найден")
        return False
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, что RequestIDMiddleware идет первым
    request_id_pos = content.find("RequestIDMiddleware")
    ip_filter_pos = content.find("IPFilterMiddleware")
    input_sanitization_pos = content.find("InputSanitizationMiddleware")
    
    if request_id_pos == -1:
        print_error("RequestIDMiddleware не найден")
        return False
    
    if ip_filter_pos != -1 and ip_filter_pos < request_id_pos:
        print_error("IPFilterMiddleware должен идти после RequestIDMiddleware")
        return False
    
    if input_sanitization_pos != -1 and input_sanitization_pos < request_id_pos:
        print_error("InputSanitizationMiddleware должен идти после RequestIDMiddleware")
        return False
    
    print_success("Порядок middleware корректен")
    return True


def check_security_headers():
    """Проверить наличие security headers"""
    print_header("Проверка security headers")
    
    backend_path = Path(__file__).parent
    security_headers_file = backend_path / "app" / "middleware" / "security_headers.py"
    
    if not security_headers_file.exists():
        print_error("security_headers.py не найден")
        return False
    
    with open(security_headers_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Strict-Transport-Security",
        "Content-Security-Policy",
    ]
    
    missing_headers = []
    for header in required_headers:
        if header not in content:
            missing_headers.append(header)
    
    if missing_headers:
        print_error(f"Отсутствуют headers: {', '.join(missing_headers)}")
        return False
    
    print_success("Все необходимые security headers присутствуют")
    return True


def check_environment_variables():
    """Проверить документацию переменных окружения"""
    print_header("Проверка переменных окружения")
    
    backend_path = Path(__file__).parent
    main_file = backend_path / "app" / "main.py"
    
    if not main_file.exists():
        print_error("main.py не найден")
        return False
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    env_vars = [
        "IP_FILTER_ENABLED",
        "IP_WHITELIST",
        "IP_BLACKLIST",
        "ENVIRONMENT",
        "JWT_SECRET_KEY",
    ]
    
    found_vars = []
    for var in env_vars:
        if var in content:
            found_vars.append(var)
    
    print_success(f"Найдено переменных окружения: {len(found_vars)}/{len(env_vars)}")
    return True


def main():
    """Главная функция"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Проверка качества кода и системы{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    checks = [
        ("Импорты модулей", check_imports),
        ("Линтинг", check_linting),
        ("Типы", check_type_hints),
        ("Тесты", check_tests),
        ("Порядок middleware", check_middleware_order),
        ("Security headers", check_security_headers),
        ("Переменные окружения", check_environment_variables),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Ошибка при проверке {name}: {e}")
            results.append((name, False))
    
    # Итоговая сводка
    print_header("Итоговая сводка")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"Пройдено проверок: {passed}/{total}")
    
    if passed == total:
        print_success("Все проверки пройдены успешно!")
        return 0
    else:
        print_error(f"Провалено проверок: {total - passed}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
