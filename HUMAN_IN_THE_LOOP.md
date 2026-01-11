# Human-in-the-Loop для логина с капчей

Механизм для обработки капчи и ручного логина при автоматизации парсинга.

## Как это работает

1. **Автоматический логин** - парсер пытается автоматически войти с креденшиалами
2. **Обнаружение капчи** - если обнаружена капча или логин не удался, парсер останавливается
3. **Human-in-the-loop** - открывается браузер, пользователь решает капчу и логинится вручную
4. **Сохранение состояния** - после успешного логина сохраняется `storageState` (cookies/localStorage)
5. **Переиспользование** - при следующих запусках используется сохранённый `storageState`

## Использование

### Первый запуск (с капчей)

```bash
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com
```

**Что произойдёт:**
1. Парсер попытается автоматически залогиниться
2. Если обнаружена капча или логин не удался:
   - Откроется браузер (если не headless)
   - В терминале появится сообщение:
   ```
   🔐 HUMAN-IN-THE-LOOP: Требуется ручное вмешательство
   ============================================================
   Мерчант: 1xbet
   URL: https://indian.1xbet.com/login
   
   📋 Инструкции:
   1. Решите капчу в открытом браузере (если есть)
   2. Введите креденшиалы и войдите в систему
   3. После успешного входа нажмите Enter в этом терминале
   
   ⏸️  Ожидание ручного логина...
   ```
3. Вы решаете капчу и логинитесь вручную
4. Нажимаете Enter в терминале
5. Парсер сохраняет `storageState` и продолжает работу

### Последующие запуски

При следующих запусках парсер автоматически загрузит сохранённый `storageState` и пропустит этап логина (если cookies ещё действительны).

## Файлы

### StorageState
- **Путь**: `storage_states/{merchant_id}_storage_state.json`
- **Содержит**: cookies, localStorage, sessionStorage
- **Использование**: автоматическая загрузка при следующем запуске

### Trace файлы
- **Путь**: `traces/{merchant_id}_trace.zip`
- **Содержит**: полную запись сессии для отладки
- **Просмотр**: `playwright show-trace traces/1xbet_trace.zip`

### Уведомления
- **Путь**: `notification_{merchant_id}_{timestamp}.txt`
- **Содержит**: информацию о необходимости ручного вмешательства
- **Использование**: для интеграции с системами мониторинга

## Интеграция с системами мониторинга

### Отправка уведомлений

Можно настроить отправку уведомлений при обнаружении капчи:

```python
# В wait_for_manual_login можно добавить:
import requests

notification = {
    "merchant": merchant_id,
    "url": page.url,
    "trace": trace_path,
    "timestamp": time.time()
}

# Отправка в Slack/Telegram/Email
requests.post("https://your-webhook-url", json=notification)
```

### VNC/Remote Desktop

Для удалённого доступа к браузеру можно использовать:
- **VNC**: запуск браузера в VNC-сессии
- **Playwright trace viewer**: `playwright show-trace trace.zip`
- **BrowserStack/LambdaTest**: для облачного доступа

## Пример workflow

```bash
# Запуск 1: Первый логин с капчей
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com
# → Обнаружена капча
# → Human-in-the-loop: решаете капчу вручную
# → StorageState сохранён

# Запуск 2: Использует сохранённый StorageState
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com
# → StorageState загружен
# → Логин пропущен (cookies действительны)
# → Парсинг продолжается

# Запуск 3: Cookies истекли
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com
# → StorageState загружен, но cookies недействительны
# → Human-in-the-loop: требуется повторный логин
```

## Преимущества

✅ **Не нарушает правила сайтов** - капча решается человеком  
✅ **Эффективность** - после первого логина не требуется повторное вмешательство  
✅ **Отладка** - trace файлы для анализа проблем  
✅ **Масштабируемость** - можно интегрировать с системами мониторинга  

## Ограничения

⚠️ **Требуется операционное окно** - нужен доступ к браузеру для ручного решения  
⚠️ **Cookies могут истечь** - потребуется повторный логин  
⚠️ **Не полностью автоматизировано** - требуется участие человека при капче  

## Настройка

### Отключение headless режима

Для human-in-the-loop браузер должен быть видимым:

```python
parser = ProviderParserPlaywright(headless=False)  # Важно!
```

### Настройка таймаутов

В `wait_for_manual_login` можно добавить таймаут:

```python
# Ждём максимум 5 минут
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout waiting for manual login")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(300)  # 5 минут
```

## Troubleshooting

### Проблема: StorageState не загружается

**Решение**: Убедитесь, что файл существует и имеет правильные права:
```bash
ls -la storage_states/1xbet_storage_state.json
```

### Проблема: Cookies истекли

**Решение**: Это нормально. Парсер автоматически обнаружит это и запросит повторный логин.

### Проблема: Trace не сохраняется

**Решение**: Проверьте права на запись в директорию `traces/`:
```bash
chmod 755 traces/
```

