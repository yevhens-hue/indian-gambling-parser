# ⚡ Быстрая установка новых зависимостей

## Backend зависимости

```bash
cd web_service/backend
pip install python-jose[cryptography] passlib[bcrypt] websockets
```

Или через requirements.txt:
```bash
pip install -r requirements.txt
```

## Frontend зависимости

Зависимости уже установлены через `npm install`. Если нужно переустановить:

```bash
cd web_service/frontend
npm install
```

---

## 🔧 Если возникли ошибки импорта

### Backend: ModuleNotFoundError для auth

Проверьте, что файлы созданы:
```bash
ls -la web_service/backend/app/auth/
ls -la web_service/backend/app/api/auth.py
```

### Frontend: Ошибки TypeScript

Пересоберите проект:
```bash
cd web_service/frontend
npm run build
```

---

## ✅ Проверка установки

### Backend
```bash
cd web_service/backend
python3 -c "from app.auth.auth import authenticate_user; print('✅ Auth работает')"
python3 -c "from app.api.websocket import manager; print('✅ WebSocket работает')"
```

### Frontend
```bash
cd web_service/frontend
npm run build 2>&1 | grep -E "(error|Error)" || echo "✅ Компиляция успешна"
```
