#!/usr/bin/env python3
"""Скрипт запуска FastAPI backend"""
import uvicorn
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
backend_dir = Path(__file__).parent
project_root = backend_dir.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Запуск FastAPI Backend")
    print("=" * 60)
    print(f"📁 Backend directory: {backend_dir}")
    print(f"📁 Project root: {project_root}")
    print(f"🌐 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    print()
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(backend_dir / "app")],
        )
    except KeyboardInterrupt:
        print("\n\n👋 Backend остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")
        sys.exit(1)
