"""API endpoints для работы со скриншотами"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.config import BASE_DIR, SCREENSHOTS_DIR

router = APIRouter(prefix="/screenshots", tags=["screenshots"])


@router.get("/{screenshot_path:path}")
async def get_screenshot(screenshot_path: str):
    """
    Получить скриншот по пути
    
    Args:
        screenshot_path: Относительный путь к скриншоту (например, screenshot.png)
    """
    try:
        # Безопасная обработка пути (защита от path traversal)
        screenshot_file = SCREENSHOTS_DIR / Path(screenshot_path).name
        
        if not screenshot_file.exists():
            # Попробуем найти в корневой директории (если путь абсолютный)
            screenshot_file = BASE_DIR / screenshot_path
            if not screenshot_file.exists():
                raise HTTPException(status_code=404, detail=f"Скриншот не найден: {screenshot_path}")
        
        # Определяем MIME тип по расширению
        suffix = screenshot_file.suffix.lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_types.get(suffix, 'image/png')
        
        return FileResponse(
            path=str(screenshot_file),
            media_type=media_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении скриншота: {str(e)}")
