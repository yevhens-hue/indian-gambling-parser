# Nginx Configuration

## Использование

### Development (HTTP только)

Используйте базовую конфигурацию без SSL.

### Production (HTTPS)

1. **Получите SSL сертификаты:**

   **Option 1: Let's Encrypt (рекомендуется)**
   ```bash
   sudo certbot certonly --standalone -d your-domain.com
   ```

   **Option 2: Собственные сертификаты**
   ```bash
   # Поместите cert.pem и key.pem в /etc/nginx/ssl/
   sudo mkdir -p /etc/nginx/ssl
   sudo cp cert.pem /etc/nginx/ssl/
   sudo cp key.pem /etc/nginx/ssl/
   sudo chmod 600 /etc/nginx/ssl/key.pem
   ```

2. **Обновите конфигурацию:**

   - Раскомментируйте HTTPS server block в `nginx.conf`
   - Замените `your-domain.com` на ваш домен
   - Убедитесь, что пути к сертификатам правильные

3. **Включите HTTP -> HTTPS redirect:**

   Раскомментируйте `return 301 https://$host$request_uri;` в HTTP server block

4. **Проверьте конфигурацию:**
   ```bash
   sudo nginx -t
   ```

5. **Перезагрузите nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

## Docker Compose

Для использования в Docker Compose:

```yaml
services:
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro  # Для production
      - ./frontend/dist:/usr/share/nginx/html:ro
    ports:
      - "80:80"
      - "443:443"  # Для HTTPS
    depends_on:
      - backend
```

## Security Headers

Конфигурация включает:
- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`

## Rate Limiting

- API: 200 запросов в минуту
- WebSocket: 50 подключений в минуту

## SSL/TLS Settings

Используются современные и безопасные настройки:
- TLS 1.2 и 1.3
- Современные cipher suites
- Отключены SSL session tickets
- Оптимизированный session cache
