
# provider_parser_playwright.py
# Парсер провайдеров на Playwright с обработкой iframe, popup, network requests

import asyncio
import time
import os
import sys
import re
from urllib.parse import urlparse
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Page, Frame, BrowserContext, Error as PWError
import tldextract

from storage import Storage
from merchants_config import MERCHANTS


class ProviderParserPlaywright:
    def __init__(self, headless: bool = False, screenshot_dir: str = "screenshots", storage_state_dir: str = "storage_states", trace_dir: str = "traces"):
        self.headless = headless
        self.screenshot_dir = screenshot_dir
        self.storage_state_dir = storage_state_dir
        self.trace_dir = trace_dir
        self.storage = Storage()
        
        # Создаём директории
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.storage_state_dir, exist_ok=True)
        os.makedirs(self.trace_dir, exist_ok=True)
        
    def get_storage_state_path(self, merchant_id: str) -> str:
        """Путь к файлу storageState для мерчанта"""
        return os.path.join(self.storage_state_dir, f"{merchant_id}_storage_state.json")
    
    def get_trace_path(self, merchant_id: str) -> str:
        """Путь к файлу trace для мерчанта"""
        return os.path.join(self.trace_dir, f"{merchant_id}_trace.zip")
    
    async def detect_captcha(self, page: Page) -> bool:
        """Обнаружение капчи на странице"""
        captcha_indicators = [
            "//iframe[contains(@src, 'recaptcha')]",
            "//iframe[contains(@src, 'captcha')]",
            "//div[contains(@class, 'captcha')]",
            "//div[contains(@class, 'recaptcha')]",
            "//div[contains(@id, 'captcha')]",
            "//div[contains(@id, 'recaptcha')]",
            "//*[contains(text(), 'captcha')]",
            "//*[contains(text(), 'CAPTCHA')]",
            "//*[contains(text(), 'Verify')]",
            "//*[contains(text(), 'verify')]",
        ]
        
        for xpath in captcha_indicators:
            try:
                element = page.locator(f"xpath={xpath}").first
                if await element.is_visible(timeout=2000):
                    return True
            except:
                continue
        
        # Проверяем iframe с капчей
        for frame in page.frames:
            if frame != page.main_frame:
                frame_url = frame.url.lower()
                if any(keyword in frame_url for keyword in ["recaptcha", "captcha", "hcaptcha", "turnstile"]):
                    return True
        
        return False
    
    async def wait_for_manual_login(self, page: Page, merchant_id: str, context: BrowserContext) -> bool:
        """Ожидание ручного решения капчи и логина"""
        print("\n" + "="*60)
        print("🔐 HUMAN-IN-THE-LOOP: Требуется ручное вмешательство")
        print("="*60)
        print(f"Мерчант: {merchant_id}")
        print(f"URL: {page.url}")
        print(f"\n📋 Инструкции:")
        print("1. Решите капчу в открытом браузере (если есть)")
        print("2. Введите креденшиалы и войдите в систему")
        print("3. После успешного входа нажмите Enter в этом терминале")
        print("\n⏸️  Ожидание ручного логина...")
        print("="*60 + "\n")
        
        # Сохраняем trace для отладки
        trace_path = self.get_trace_path(merchant_id)
        try:
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            print(f"📹 Trace запись начата: {trace_path}")
        except Exception as e:
            print(f"⚠️  Не удалось начать trace: {e}")
        
        # Создаём файл уведомления
        notification_file = f"notification_{merchant_id}_{int(time.time())}.txt"
        with open(notification_file, "w") as f:
            f.write(f"HUMAN-IN-THE-LOOP: Требуется ручное вмешательство\n")
            f.write(f"Мерчант: {merchant_id}\n")
            f.write(f"URL: {page.url}\n")
            f.write(f"Trace: {trace_path}\n")
            f.write(f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"📄 Уведомление сохранено: {notification_file}")
        
        # Ждём ввода от пользователя или автоматически проверяем состояние
        try:
            input("Нажмите Enter после успешного логина...")
        except (KeyboardInterrupt, EOFError):
            # Если интерактивный ввод недоступен, автоматически проверяем состояние
            if isinstance(sys.exc_info()[1], EOFError):
                print("\n⚠️  Интерактивный режим недоступен, переходим к автоматической проверке...")
                print("⏳ Ожидание логина (проверка каждые 5 секунд, максимум 5 минут)...")
                
                max_wait_time = 300  # 5 минут
                check_interval = 5  # 5 секунд
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                    
                    current_url = page.url
                    if "login" not in current_url.lower() and "signin" not in current_url.lower():
                        print(f"✓ Логин выполнен успешно (проверено через {elapsed_time} секунд)")
                        break
                    
                    if elapsed_time % 30 == 0:  # Сообщение каждые 30 секунд
                        print(f"⏳ Ожидание логина... ({elapsed_time}/{max_wait_time} сек)")
                else:
                    print("⚠️  Превышено время ожидания логина")
            else:
                print("\n⚠️  Прервано пользователем")
                return False
        
        # Останавливаем trace
        try:
            await context.tracing.stop(path=trace_path)
            print(f"✓ Trace сохранён: {trace_path}")
            print(f"  Просмотр: playwright show-trace {trace_path}")
        except Exception as e:
            print(f"⚠️  Ошибка при сохранении trace: {e}")
        
        # Проверяем, что логин успешен
        current_url = page.url
        if "login" not in current_url.lower() and "signin" not in current_url.lower():
            print("✓ Логин выполнен успешно")
            return True
        else:
            print("⚠️  Возможно, логин не выполнен. Проверьте URL.")
            return True  # Продолжаем в любом случае
    
    
    def get_domain(self, url: str) -> str:
        """Извлечение домена из URL (eTLD+1)"""
        if not url or not url.startswith(("http://", "https://")):
            return ""
        try:
            extracted = tldextract.extract(url)
            if extracted.domain and extracted.suffix:
                return f"{extracted.domain}.{extracted.suffix}".lower()
            return extracted.domain.lower() if extracted.domain else ""
        except Exception:
            return ""
    
    def is_external_provider_domain(self, domain: str, merchant_domain: str) -> bool:
        """Проверка, является ли домен внешним доменом провайдера (не служебным)"""
        if not domain or not merchant_domain:
            return False
        
        # Список трекинг доменов, которые не являются провайдерами
        TRACKING_DOMAINS = (
            "google.", "gstatic.", "doubleclick.", "googlesyndication.",
            "googletagmanager.", "google-analytics.", "facebook.", "fbcdn.",
            "vk.com", "yandex.", "tiktok.", "hotjar.", "suphelper.",
            "1xbet.com", "dafabet.com", "widget.suphelper.top",
        )
        
        domain_lower = domain.lower()
        
        # Проверяем, не является ли это доменом мерчанта
        if domain_lower == merchant_domain.lower():
            return False
        
        # Проверяем, не является ли это трекинг доменом
        for tracking in TRACKING_DOMAINS:
            if tracking in domain_lower:
                return False
        
        # Если домен отличается от домена мерчанта и не в списке трекинга - это внешний провайдер
        return True
    
    async def login(self, page: Page, merchant_id: str, config: dict) -> bool:
        """Логин на сайт мерчанта"""
        try:
            credentials = config.get("credentials", {})
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            
            if not username or not password:
                print(f"⚠️  Креденшиалы не указаны для {merchant_id}. Пропускаем логин.")
                return False
            
            print(f"Попытка входа с username: {username[:3]}***")
            
            selectors = config.get("selectors", {})
            
            # НЕ переходим на /login напрямую, так как может быть 404
            # Остаёмся на главной странице и ищем кнопку логина там
            current_url = page.url
            print(f"Текущий URL: {current_url}")
            
            # Проверяем, не попали ли на 404
            try:
                page_content = await page.content()
                if "404" in page_content or "ОШИБКА 404" in page_content or "Такой страницы нет" in page_content:
                    print("⚠️  Обнаружена 404 ошибка, возвращаемся на главную")
                    base_url = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}"
                    await page.goto(base_url, wait_until="domcontentloaded", timeout=10000)
                    await page.wait_for_timeout(3000)
                    current_url = page.url
            except:
                pass
            
            # Поиск и клик по кнопке логина
            login_selectors = selectors.get("login_button", "").split(", ")
            login_clicked = False
            
            # Пробуем CSS селекторы
            for selector in login_selectors:
                if not selector.strip():
                    continue
                try:
                    login_btn = page.locator(selector).first
                    if await login_btn.is_visible(timeout=3000):
                        await login_btn.click()
                        login_clicked = True
                        print(f"✓ Нажата кнопка логина: {selector}")
                        await page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue
            
            # Если не нашли через CSS, пробуем поиск по тексту (включая русский)
            if not login_clicked:
                text_selectors = [
                    "//a[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'LOGIN')]",
                    "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'LOGIN')]",
                    "//a[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'SIGN IN')]",
                    "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'SIGN IN')]",
                    "//a[contains(text(), 'Вход')]",
                    "//button[contains(text(), 'Вход')]",
                    "//a[contains(text(), 'Войти')]",
                    "//button[contains(text(), 'Войти')]",
                    "//a[contains(@href, 'login')]",
                    "//a[contains(@href, 'signin')]",
                    "//a[contains(@href, 'auth')]",
                ]
                for xpath in text_selectors:
                    try:
                        login_btn = page.locator(f"xpath={xpath}").first
                        if await login_btn.is_visible(timeout=3000):
                            await login_btn.click()
                            login_clicked = True
                            print(f"✓ Нажата кнопка логина через XPath: {xpath}")
                            await page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue
            
            if not login_clicked:
                print("⚠️  Кнопка логина не найдена. Возможно, уже на странице логина.")
            
            # Ждём появления формы логина (может быть модальное окно или iframe)
            await page.wait_for_timeout(5000)
            
            # Проверяем, не появился ли iframe с формой логина
            login_frame = None
            for frame in page.frames:
                if frame != page.main_frame:
                    try:
                        # Проверяем наличие полей ввода в iframe
                        username_in_frame = frame.locator("input[type='text'], input[name*='login'], input[name*='username']").first
                        if await username_in_frame.is_visible(timeout=2000):
                            login_frame = frame
                            print("✓ Найдена форма логина в iframe")
                            break
                    except:
                        continue
            
            # Если не нашли iframe, проверяем все фреймы более тщательно
            if not login_frame:
                print(f"  Проверка iframe: найдено {len(page.frames)} фреймов")
                for i, frame in enumerate(page.frames):
                    if frame != page.main_frame:
                        try:
                            frame_url = frame.url
                            print(f"    Frame {i}: {frame_url}")
                            # Пробуем найти любые input в этом фрейме
                            inputs = await frame.locator("input").all()
                            if inputs:
                                print(f"      Найдено {len(inputs)} input полей в iframe")
                                login_frame = frame
                                break
                        except:
                            continue
            
            # Ввод username - используем нужный контекст (iframe или main page)
            target_page = login_frame if login_frame else page
            username_selectors = selectors.get("username_input", "").split(", ")
            username_entered = False
            
            for selector in username_selectors:
                if not selector.strip():
                    continue
                try:
                    username_input = target_page.locator(selector).first
                    if await username_input.is_visible(timeout=3000):
                        await username_input.fill(username)
                        username_entered = True
                        print(f"✓ Введён username: {selector}")
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue
            
            # Если не нашли через CSS, пробуем XPath
            if not username_entered:
                xpath_selectors = [
                    "//input[@type='text' and not(@type='password')]",
                    "//input[contains(@placeholder, 'login') or contains(@placeholder, 'Login') or contains(@placeholder, 'phone') or contains(@placeholder, 'Phone')]",
                    "//input[contains(@name, 'login') or contains(@name, 'username') or contains(@name, 'phone')]",
                    "//input[contains(@id, 'login') or contains(@id, 'username') or contains(@id, 'phone')]",
                    "//input[@type='text'][1]",
                ]
                for xpath in xpath_selectors:
                    try:
                        username_input = target_page.locator(f"xpath={xpath}").first
                        if await username_input.is_visible(timeout=3000):
                            await username_input.fill(username)
                            username_entered = True
                            print(f"✓ Введён username через XPath: {xpath}")
                            await page.wait_for_timeout(1000)
                            break
                    except Exception:
                        continue
            
            # Последняя попытка - ищем все input[type='text'] и берём первый
            if not username_entered:
                try:
                    all_text_inputs = await target_page.locator("input[type='text']").all()
                    if all_text_inputs:
                        # Берём первый видимый input
                        for inp in all_text_inputs:
                            try:
                                if await inp.is_visible(timeout=1000):
                                    await inp.fill(username)
                                    username_entered = True
                                    print(f"✓ Введён username в первый видимый input[type='text']")
                                    await page.wait_for_timeout(1000)
                                    break
                            except:
                                continue
                except Exception as e:
                    print(f"⚠️  Ошибка при поиске всех text inputs: {e}")
            
            if not username_entered:
                print("❌ Поле username не найдено")
                # Логируем все input поля на странице для отладки
                try:
                    all_inputs = await target_page.locator("input").all()
                    print(f"  Найдено input полей на странице: {len(all_inputs)}")
                    for i, inp in enumerate(all_inputs[:5]):  # Показываем первые 5
                        try:
                            inp_type = await inp.get_attribute("type")
                            inp_name = await inp.get_attribute("name")
                            inp_id = await inp.get_attribute("id")
                            print(f"    Input {i+1}: type={inp_type}, name={inp_name}, id={inp_id}")
                        except:
                            pass
                except:
                    pass
                return False
            
            # Ввод password - используем тот же контекст
            password_selectors = selectors.get("password_input", "").split(", ")
            password_entered = False
            
            for selector in password_selectors:
                if not selector.strip():
                    continue
                try:
                    password_input = target_page.locator(selector).first
                    if await password_input.is_visible(timeout=3000):
                        await password_input.fill(password)
                        password_entered = True
                        print(f"✓ Введён password: {selector}")
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue
            
            # Если не нашли через CSS, пробуем XPath
            if not password_entered:
                xpath = "//input[@type='password']"
                try:
                    password_input = target_page.locator(f"xpath={xpath}").first
                    if await password_input.is_visible(timeout=3000):
                        await password_input.fill(password)
                        password_entered = True
                        print(f"✓ Введён password через XPath")
                        await page.wait_for_timeout(1000)
                except Exception:
                    pass
            
            if not password_entered:
                print("❌ Поле password не найдено")
                return False
            
            # Нажатие кнопки submit - используем тот же контекст
            submit_selectors = selectors.get("submit_button", "").split(", ")
            submitted = False
            
            for selector in submit_selectors:
                if not selector.strip():
                    continue
                try:
                    submit_btn = target_page.locator(selector).first
                    if await submit_btn.is_visible(timeout=3000):
                        await submit_btn.click()
                        submitted = True
                        print(f"✓ Нажата кнопка submit: {selector}")
                        try:
                            await page.wait_for_load_state("networkidle", timeout=10000)
                        except:
                            await page.wait_for_load_state("load", timeout=5000)
                        break
                except Exception:
                    continue
            
            if not submitted:
                print("⚠️  Кнопка submit не найдена, пробуем Enter")
                try:
                    await password_input.press("Enter")
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        await page.wait_for_load_state("load", timeout=5000)
                except:
                    pass
            
            # Проверка на капчу
            captcha_detected = await self.detect_captcha(target_page)
            if captcha_detected:
                print("🔐 Обнаружена капча!")
                return "captcha"  # Возвращаем специальный статус
            
            # Проверка успешности логина
            current_url = page.url
            if "login" not in current_url.lower() or "dashboard" in current_url.lower() or "account" in current_url.lower():
                print("✓ Логин выполнен успешно")
                return True
            else:
                print("⚠️  Возможно, логин не выполнен. Продолжаем...")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка при логине: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def fill_provider_form(self, container, config: dict):
        """Заполнение полей формы провайдера в модальном окне"""
        try:
            form_data = config.get("provider_form_data", {})
            if not form_data:
                return
            
            upi_id = form_data.get("upi_id", "")
            phone_number = form_data.get("phone_number", "")
            aadhaar = form_data.get("aadhaar", "")
            
            if not upi_id and not phone_number and not aadhaar:
                return
            
            # Ищем поле UPI ID
            upi_selectors = [
                "input[name*='upi']",
                "input[id*='upi']",
                "input[placeholder*='upi']",
                "input[placeholder*='UPI']",
            ]
            
            for selector in upi_selectors:
                try:
                    upi_input = container.locator(selector).first
                    if await upi_input.is_visible(timeout=2000):
                        await upi_input.clear()
                        await upi_input.fill(upi_id)
                        print(f"  ✓ Заполнено UPI ID: {upi_id}")
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue
            
            # Ищем поле Phone Number
            phone_selectors = [
                "input[name*='phone']",
                "input[name*='number']",
                "input[id*='phone']",
                "input[id*='number']",
                "input[type='tel']",
                "input[placeholder*='phone']",
                "input[placeholder*='number']",
            ]
            
            for selector in phone_selectors:
                try:
                    phone_input = container.locator(selector).first
                    if await phone_input.is_visible(timeout=2000):
                        await phone_input.clear()
                        await phone_input.fill(phone_number)
                        print(f"  ✓ Заполнено Phone Number: {phone_number}")
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue
            
            # Ищем поле Aadhaar
            aadhaar_selectors = [
                "input[name*='aadhaar']",
                "input[id*='aadhaar']",
                "input[placeholder*='aadhaar']",
            ]
            
            for selector in aadhaar_selectors:
                try:
                    aadhaar_input = container.locator(selector).first
                    if await aadhaar_input.is_visible(timeout=2000):
                        await aadhaar_input.clear()
                        await aadhaar_input.fill(aadhaar)
                        print(f"  ✓ Заполнено Aadhaar: {aadhaar}")
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue
            
            # Если не нашли по селекторам, пробуем поиск по label или тексту рядом
            try:
                all_inputs = await container.locator("input[type='text'], input[type='tel'], input[type='number']").all()
                for inp in all_inputs:
                    try:
                        input_id = await inp.get_attribute("id")
                        input_name = (await inp.get_attribute("name") or "").lower()
                        input_placeholder = (await inp.get_attribute("placeholder") or "").lower()
                        
                        # Ищем label
                        label_text = ""
                        if input_id:
                            try:
                                label = container.locator(f"label[for='{input_id}']").first
                                if await label.is_visible(timeout=500):
                                    label_text = (await label.inner_text()).lower()
                            except:
                                pass
                        
                        # Ищем текст перед input
                        try:
                            parent = inp.locator("xpath=./ancestor::div[1] | ./ancestor::label[1]").first
                            parent_text = (await parent.inner_text()).lower() if await parent.is_visible(timeout=500) else ""
                        except:
                            parent_text = ""
                        
                        combined_text = f"{label_text} {parent_text} {input_name} {input_placeholder}".lower()
                        
                        # Определяем тип поля
                        if "upi" in combined_text and upi_id:
                            await inp.clear()
                            await inp.fill(upi_id)
                            print(f"  ✓ Заполнено UPI ID по тексту: {upi_id}")
                            await asyncio.sleep(0.5)
                        elif ("phone" in combined_text or "number" in combined_text) and "aadhaar" not in combined_text and phone_number:
                            await inp.clear()
                            await inp.fill(phone_number)
                            print(f"  ✓ Заполнено Phone Number по тексту: {phone_number}")
                            await asyncio.sleep(0.5)
                        elif "aadhaar" in combined_text and aadhaar:
                            await inp.clear()
                            await inp.fill(aadhaar)
                            print(f"  ✓ Заполнено Aadhaar по тексту: {aadhaar}")
                            await asyncio.sleep(0.5)
                    except:
                        continue
            except:
                pass
            
        except Exception as e:
            print(f"  ⚠️  Ошибка при заполнении формы: {e}")
    
    async def fill_provider_form_in_frame(self, frame: Frame, config: dict):
        """Заполнение полей формы провайдера в iframe"""
        try:
            form_data = config.get("provider_form_data", {})
            if not form_data:
                return
            
            upi_id = form_data.get("upi_id", "")
            phone_number = form_data.get("phone_number", "")
            aadhaar = form_data.get("aadhaar", "")
            
            # Ищем поле UPI ID в iframe
            upi_selectors = [
                "input[name*='upi']",
                "input[id*='upi']",
                "input[placeholder*='upi']",
            ]
            
            for selector in upi_selectors:
                try:
                    upi_input = frame.locator(selector).first
                    if await upi_input.is_visible(timeout=2000):
                        await upi_input.clear()
                        await upi_input.fill(upi_id)
                        print(f"  ✓ Заполнено UPI ID в iframe: {upi_id}")
                        break
                except:
                    continue
            
            # Ищем поле Phone Number в iframe
            phone_selectors = [
                "input[name*='phone']",
                "input[name*='number']",
                "input[type='tel']",
            ]
            
            for selector in phone_selectors:
                try:
                    phone_input = frame.locator(selector).first
                    if await phone_input.is_visible(timeout=2000):
                        await phone_input.clear()
                        await phone_input.fill(phone_number)
                        print(f"  ✓ Заполнено Phone Number в iframe: {phone_number}")
                        break
                except:
                    continue
            
            # Ищем поле Aadhaar в iframe
            aadhaar_selectors = [
                "input[name*='aadhaar']",
                "input[id*='aadhaar']",
            ]
            
            for selector in aadhaar_selectors:
                try:
                    aadhaar_input = frame.locator(selector).first
                    if await aadhaar_input.is_visible(timeout=2000):
                        await aadhaar_input.clear()
                        await aadhaar_input.fill(aadhaar)
                        print(f"  ✓ Заполнено Aadhaar в iframe: {aadhaar}")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"  ⚠️  Ошибка при заполнении формы в iframe: {e}")
    
    async def navigate_to_cashier(self, page: Page, config: dict) -> Optional[str]:
        """Переход на страницу кэшира"""
        try:
            # Сначала проверяем, есть ли прямой URL кэшира в конфиге
            cashier_url = config.get("cashier_url")
            if cashier_url:
                print(f"→ Переход на страницу кэшира: {cashier_url}")
                await page.goto(cashier_url, wait_until="domcontentloaded", timeout=30000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    await page.wait_for_load_state("load", timeout=5000)
                await page.wait_for_timeout(2000)  # Дополнительная пауза для загрузки
                print(f"✓ Переход на кэшир выполнен: {page.url}")
                return page.url
            
            selectors = config.get("selectors", {})
            
            # Пробуем найти ссылку на кэшир
            cashier_selectors = (selectors.get("cashier_link", "") + ", " + 
                               selectors.get("cashier_button", "")).split(", ")
            
            for selector in cashier_selectors:
                if not selector.strip():
                    continue
                try:
                    cashier_element = page.locator(selector).first
                    if await cashier_element.is_visible(timeout=3000):
                        await cashier_element.click()
                        print(f"✓ Переход на кэшир: {selector}")
                        try:
                            await page.wait_for_load_state("networkidle", timeout=10000)
                        except:
                            await page.wait_for_load_state("load", timeout=5000)
                        return page.url
                except Exception:
                    continue
            
            # Если не нашли по селекторам, пробуем прямой переход
            current_url = page.url
            base_url = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}"
            
            cashier_urls = [
                f"{base_url}/en/office/recharge",  # Приоритетный URL для 1xbet
                f"{base_url}/cashier",
                f"{base_url}/deposit",
                f"{base_url}/payment",
                f"{base_url}/payments",
            ]
            
            for cashier_url in cashier_urls:
                try:
                    await page.goto(cashier_url, wait_until="domcontentloaded", timeout=10000)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        await page.wait_for_load_state("load", timeout=5000)
                    if "cashier" in page.url.lower() or "deposit" in page.url.lower():
                        print(f"✓ Переход на кэшир через прямой URL: {cashier_url}")
                        return page.url
                except Exception:
                    continue
            
            print("⚠️  Не удалось найти кэшир. Продолжаем на текущей странице.")
            return page.url
            
        except Exception as e:
            print(f"❌ Ошибка при переходе на кэшир: {e}")
            return page.url
    
    async def get_deposit_frame(self, page: Page, timeout_ms: int = 15000) -> Optional[Frame]:
        """Получить deposit iframe с retry"""
        deadline = time.time() + timeout_ms / 1000
        while time.time() < deadline:
            for fr in page.frames:
                if fr.url and "paysystems/deposit" in fr.url:
                    try:
                        await fr.evaluate("() => document.readyState")
                        return fr
                    except Exception:
                        pass
            await page.wait_for_timeout(250)
        return None
    
    async def wait_deposit_ready(self, deposit_frame: Frame, timeout_ms: int = 12000):
        """Ждём, пока внутри iframe появится E-WALLETS (признак, что UI отрисован)"""
        try:
            await deposit_frame.locator("text=E-WALLETS").first.wait_for(state="visible", timeout=timeout_ms)
        except Exception as e:
            print(f"  ⚠️  E-WALLETS не появился в deposit_frame: {e}")
    
    async def build_provider_locator(self, deposit_frame: Frame, provider_key: str):
        """Построить locator провайдера заново на базе ключа"""
        import re
        from playwright.async_api import TimeoutError as PWTimeout
        
        # 1) Пробуем по тексту
        if provider_key.lower() == "upi fast":
            txt = deposit_frame.get_by_text(re.compile(r"\bupi\s*fast\b", re.I)).first
        else:
            txt = deposit_frame.get_by_text(re.compile(r"\bpaytm\b", re.I)).first
        
        # Если текста нет (бывает) — fallback по img src
        try:
            await txt.wait_for(state="attached", timeout=1200)
            base = txt
        except PWTimeout:
            hint = "paytm" if "paytm" in provider_key.lower() else "upi"
            base = deposit_frame.locator(f"img[src*='{hint}' i]").first
            try:
                await base.wait_for(state="attached", timeout=1200)
            except PWTimeout:
                # Если и по img не нашли, возвращаем текстовый locator (он может сработать позже)
                base = txt
        
        # Кликаем по кликабельному предку (тайл)
        clickable = base.locator(
            "xpath=ancestor-or-self::*[self::a or self::button or @role='button' or @onclick or self::div][1]"
        ).first
        return clickable
    
    async def prepare_cashier_context(self, page: Page, cashier_url: str, config: dict) -> Optional[Frame]:
        """Восстановление deposit iframe перед обработкой каждого провайдера (чистый контекст)"""
        print("  → Восстановление контекста cashier...")
        await page.goto(cashier_url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            await page.wait_for_load_state("load", timeout=5000)
        
        # Нажимаем "Make Deposit" если нужно
        try:
            await self.click_make_deposit(page, config)
            await page.wait_for_timeout(2000)
        except:
            pass
        
        # Получаем deposit iframe
        deposit_frame = await self.get_deposit_frame(page, timeout_ms=15000)
        if deposit_frame:
            print(f"  ✓ Deposit iframe найден: {deposit_frame.url}")
            # Ждём, пока UI отрисуется
            try:
                await self.wait_deposit_ready(deposit_frame, timeout_ms=12000)
                print("  ✓ Deposit iframe готов (E-WALLETS виден)")
            except:
                print("  ⚠️  E-WALLETS не найден, но продолжаем")
            return deposit_frame
        
        print("  ⚠️  Deposit iframe не найден")
        return None
    
    async def click_make_deposit(self, page: Page, config: dict) -> bool:
        """Нажатие на кнопку 'Make Deposit'"""
        try:
            selectors = config.get("selectors", {})
            make_deposit_selectors = selectors.get("make_deposit_button", "").split(", ")
            
            # Пробуем CSS селекторы
            for selector in make_deposit_selectors:
                if not selector.strip():
                    continue
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=3000):
                        await button.click()
                        print(f"✓ Нажата кнопка 'Make Deposit': {selector}")
                        await page.wait_for_timeout(3000)
                        return True
                except Exception:
                    continue
            
            # Пробуем XPath селекторы по тексту
            xpath_selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'MAKE A DEPOSIT')]",
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'MAKE DEPOSIT')]",
                "//a[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'MAKE A DEPOSIT')]",
            ]
            
            for xpath in xpath_selectors:
                try:
                    button = page.locator(f"xpath={xpath}").first
                    if await button.is_visible(timeout=3000):
                        await button.click()
                        print(f"✓ Нажата кнопка 'Make Deposit' через XPath")
                        await page.wait_for_timeout(3000)
                        return True
                except Exception:
                    continue
            
            print("⚠️  Кнопка 'Make Deposit' не найдена. Продолжаем...")
            return False
            
        except Exception as e:
            print(f"⚠️  Ошибка при поиске кнопки 'Make Deposit': {e}")
            return False
    
    async def find_wallets_context(self, page: Page):
        """Найти контекст (page или frame), где находится E-WALLETS"""
        # Сначала ищем iframe с депозитами (приоритет)
        print(f"  → Поиск iframe с депозитами...")
        deposit_frame = None
        for fr in page.frames:
            try:
                if fr != page.main_frame and fr.url:
                    if "paysystems/deposit" in fr.url or "deposit" in fr.url.lower():
                        deposit_frame = fr
                        print(f"  ✓ Найден iframe депозитов: {fr.url}")
                        break
            except:
                continue
        
        # Если нашли iframe депозитов, проверяем наличие E-WALLETS
        if deposit_frame:
            try:
                await deposit_frame.wait_for_load_state("domcontentloaded", timeout=5000)
                count = await deposit_frame.locator("text=E-WALLETS").count()
                if count > 0:
                    print(f"  ✓ E-WALLETS найден в iframe депозитов")
                    return deposit_frame
            except:
                pass
        
        # Проверяем main page
        try:
            if await page.locator("text=E-WALLETS").count() > 0:
                print("  ✓ E-WALLETS найден на главной странице")
                return page
        except:
            pass
        
        # Потом проверяем остальные фреймы
        print(f"  → Проверка остальных фреймов ({len(page.frames)} фреймов)...")
        for fr in page.frames:
            try:
                if fr != page.main_frame and fr != deposit_frame:
                    count = await fr.locator("text=E-WALLETS").count()
                    if count > 0:
                        print(f"  ✓ E-WALLETS найден в iframe: {fr.url}")
                        return fr
            except:
                continue
        
        print("  ⚠️  E-WALLETS не найден ни на странице, ни во фреймах")
        return None
    
    def tile_clickable_from(self, node_locator):
        """Найти кликабельный элемент (карточку) от узла"""
        return node_locator.locator(
            "xpath=ancestor-or-self::*[self::a or self::button or @role='button' or @onclick or self::div][1]"
        )
    
    def frame_urls(self, page: Page):
        """Получить список URL всех фреймов"""
        return sorted(set([fr.url for fr in page.frames if fr.url and fr.url.startswith(("http://", "https://"))]))
    
    async def wait_payment_ui(self, frame, timeout=8000):
        """Ожидание появления платёжного UI после клика"""
        PAY_UI_SELECTORS = [
            "input[name*='amount' i]",
            "input[placeholder*='amount' i]",
            "input[placeholder*='сумма' i]",
            "button:has-text('Continue')",
            "button:has-text('Pay')",
            "button:has-text('Deposit')",
            "button:has-text('Submit')",
            "text=Enter amount",
            "text=UPI",
            "text=VPA",
            "input[name*='upi' i]",
            "input[name*='vpa' i]",
            "input[name*='phone' i]",
            "input[type='tel']",
            "[class*='payment-form']",
            "[class*='deposit-form']",
            "[class*='amount']",
        ]
        
        for sel in PAY_UI_SELECTORS:
            try:
                loc = frame.locator(sel).first
                await loc.wait_for(state="visible", timeout=timeout)
                return sel
            except:
                    continue
        return None
    
    async def _fill_if_visible(self, locator, value: str, timeout=800) -> bool:
        """Заполнить поле, если оно видимо и пустое"""
        try:
            element = locator.first
            await element.wait_for(state="visible", timeout=timeout)
            # Проверяем, что поле пустое
            current_value = await element.input_value()
            if current_value and current_value.strip():
                # Поле уже заполнено, пропускаем
                return False
            await element.fill(value)
            return True
        except:
            return False
    
    async def find_confirm_clickable(self, frame):
        """Универсальный поиск кнопки confirm/continue/deposit/pay"""
        import re
        from playwright.async_api import TimeoutError as PWTimeout
        
        CONFIRM_RE = re.compile(r"(подтвердить|confirm|continue|proceed|next|deposit|pay)", re.I)
        
        # 1) Нормальная кнопка через role
        try:
            btn = frame.get_by_role("button", name=CONFIRM_RE).first
            await btn.wait_for(state="visible", timeout=5000)
            # Проверяем, что кнопка enabled
            is_disabled = await btn.evaluate("el => el.disabled || el.getAttribute('aria-disabled')==='true'")
            if not is_disabled:
                return btn
        except PWTimeout:
            pass
        except Exception as e:
            print(f"  → Ошибка при поиске кнопки через role: {e}")
        
        # 2) Поиск по тексту (более широкий поиск)
        try:
            txt = frame.get_by_text(CONFIRM_RE).first
            await txt.wait_for(state="visible", timeout=5000)
            # Ищем кликабельный предок
            clickable = txt.locator("xpath=ancestor-or-self::*[self::button or self::a or @role='button' or @onclick][1]")
            if await clickable.count() > 0:
                # Проверяем, что элемент enabled
                is_disabled = await clickable.first.evaluate("el => el.disabled || el.getAttribute('aria-disabled')==='true'")
                if not is_disabled:
                    return clickable.first
            # Если предок не найден, возвращаем сам текст (может быть кликабельным)
            return txt
        except PWTimeout:
            pass
        except Exception as e:
            print(f"  → Ошибка при поиске кнопки по тексту: {e}")
        
        # 3) Поиск по селекторам button с текстом CONFIRM
        try:
            buttons = frame.locator("button").filter(has_text=CONFIRM_RE)
            count = await buttons.count()
            if count > 0:
                for i in range(count):
                    btn = buttons.nth(i)
                    try:
                        await btn.wait_for(state="visible", timeout=2000)
                        is_disabled = await btn.evaluate("el => el.disabled || el.getAttribute('aria-disabled')==='true'")
                        if not is_disabled:
                            return btn
                    except:
                        continue
        except Exception as e:
            print(f"  → Ошибка при поиске через button селекторы: {e}")
        
        # 4) Поиск по классам и атрибутам
        try:
            confirm_selectors = [
                "button[class*='confirm' i]",
                "button[class*='submit' i]",
                "button[class*='deposit' i]",
                "button[class*='continue' i]",
                "button[id*='confirm' i]",
                "button[id*='submit' i]",
                "[role='button'][class*='confirm' i]",
            ]
            for selector in confirm_selectors:
                try:
                    btn = frame.locator(selector).first
                    if await btn.count() > 0:
                        await btn.wait_for(state="visible", timeout=2000)
                        is_disabled = await btn.evaluate("el => el.disabled || el.getAttribute('aria-disabled')==='true'")
                        if not is_disabled:
                            return btn
                except:
                    continue
        except Exception as e:
            print(f"  → Ошибка при поиске через селекторы: {e}")
        
        return None
    
    def parse_amount(self, s: str) -> float:
        """Парсит сумму из строки, возвращает float"""
        if not s:
            return 0.0
        s = s.replace(",", "").replace(" ", "").strip()
        try:
            return float(s)
        except:
            return 0.0
    
    async def ensure_valid_amount(self, deposit_frame, default_amount: str = "300"):
        """
        Устанавливает валидную сумму (>= 300 INR)
        Если текущее значение >= 300 - не трогает
        Если меньше 300 или пусто - устанавливает default_amount
        Returns: amount_input Locator или None если не найдено
        """
        from playwright.async_api import TimeoutError as PWTimeout
        
        # Расширенные селекторы для amount (включая xpath fallback)
        amount_locators = [
            "input[name*='amount' i]",
            "input[placeholder*='amount' i]",
            "input[type='number']",
            "input[inputmode='decimal']",
            "xpath=//div[contains(., 'Amount') or contains(., 'Сумма')]/following::input[1]",
            "xpath=//label[contains(., 'Amount') or contains(., 'Сумма')]/following::input[1]",
        ]

        for sel in amount_locators:
            loc = deposit_frame.locator(sel).first
            try:
                await loc.wait_for(state="visible", timeout=2000)
                current_str = await loc.input_value()
                current_val = self.parse_amount(current_str)
                print(f"  → Найден amount input ({sel}), текущее значение: '{current_str}' ({current_val})")

                # Если текущее значение >= 300 - не трогаем
                if current_val >= 300:
                    print(f"  ✓ Amount уже валиден (>= 300): {current_val}")
                    return loc

                # Устанавливаем минимальное значение (300)
                await loc.fill(default_amount)
                # Коммитим значение через события
                await loc.dispatch_event("input")
                await loc.dispatch_event("change")
                await loc.press("Tab")  # blur через Tab
                
                # Проверяем, что значение установилось корректно
                after_fill = await loc.input_value()
                after_val = self.parse_amount(after_fill)
                if after_val >= 300:
                    print(f"  ✓ Amount выставлен и закоммичен: {default_amount} (проверено: {after_val} >= 300)")
                else:
                    print(f"  ⚠️  Amount установлен, но значение невалидно: {after_val} (ожидалось >= 300)")

                return loc
            except PWTimeout:
                continue
            except Exception:
                continue

        print("  ❌ Amount input НЕ НАЙДЕН")
        return None
    
    async def find_action_button(self, frame):
        """
        Находит кнопку действия (Confirm/Continue/Deposit/Pay/Submit)
        Returns: Locator кнопки или None
        """
        import re
        ACTION_RE = re.compile(r"(deposit|confirm|continue|pay|proceed|submit|подтвердить)", re.I)
        
        # 1) role=button
        btn = frame.get_by_role("button", name=ACTION_RE).first
        if await btn.count() > 0:
            return btn
        
        # 2) fallback: текст + кликабельный предок
        txt = frame.get_by_text(ACTION_RE).first
        if await txt.count() > 0:
            clickable = txt.locator("xpath=ancestor-or-self::*[self::button or self::a or @role='button' or @onclick][1]").first
            if await clickable.count() > 0:
                return clickable
            return txt
        
        return None
    
    async def click_deposit_action(self, deposit_frame):
        """
        Находит и нажимает кнопку действия (Confirm/Continue/Deposit/Pay/Submit)
        Returns: True если кнопка была найдена и нажата, False иначе
        """
        import re
        from playwright.async_api import TimeoutError as PWTimeout
        
        BTN_RE = re.compile(r"^(deposit|confirm|continue|pay|proceed|submit|подтвердить)$", re.I)
        
        # Сначала проверим чекбоксы "I agree" / "accept"
        try:
            # Ищем чекбоксы рядом с текстом "agree/accept/terms"
            checkboxes = deposit_frame.locator("input[type='checkbox']")
            checkbox_count = await checkboxes.count()
            for i in range(checkbox_count):
                try:
                    cb = checkboxes.nth(i)
                    # Проверяем текст рядом с чекбоксом (label или родитель)
                    parent = cb.locator("xpath=ancestor::*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'terms')]")
                    if await parent.count() > 0:
                        await cb.check()
                        print("  ✓ Чекбокс 'I agree' установлен")
                        break
                except:
                    continue
        except:
            pass
        
        # Проверяем disabled состояние кнопки перед кликом
        try:
            btn_any = deposit_frame.get_by_role("button", name=BTN_RE).first
            if await btn_any.count() > 0:
                disabled = await btn_any.evaluate("el => el.disabled || el.getAttribute('aria-disabled')==='true'")
                if disabled:
                    print(f"  ⚠️  Action button disabled - возможно невалидный amount")
                else:
                    print(f"  → Action button enabled")
        except:
            pass
        
        # 2-шаговый флоу: нажимаем кнопку до 2 раз (DEPOSIT → CONFIRM)
        clicked_any = False
        for step in range(2):
            try:
                # 1) role=button
                btn = deposit_frame.get_by_role("button", name=BTN_RE).first
                await btn.wait_for(state="visible", timeout=2500)
                await btn.click(force=True, timeout=8000)
                print(f"  ✓ Нажата action-кнопка (step {step + 1})")
                clicked_any = True
                await deposit_frame.wait_for_timeout(300)  # дать UI перейти на следующий шаг
            except PWTimeout:
                # fallback: текст + кликабельный предок
                try:
                    txt = deposit_frame.get_by_text(BTN_RE).first
                    await txt.wait_for(state="visible", timeout=1500)
                    clickable = txt.locator("xpath=ancestor-or-self::*[self::button or self::a or @role='button' or @onclick][1]").first
                    if await clickable.count() == 0:
                        clickable = txt
                    await clickable.click(force=True, timeout=8000)
                    print(f"  ✓ Нажата action-кнопка text-fallback (step {step + 1})")
                    clicked_any = True
                    await deposit_frame.wait_for_timeout(300)
                except PWTimeout:
                    break
                except Exception:
                    break
            except Exception:
                break
        
        if not clicked_any:
            print("  ⚠️  Кнопка действия не найдена")
        
        return clicked_any
    
    async def fill_popup_and_confirm(self, deposit_frame, config: dict) -> tuple:
        """
        Заполнение ВСЕХ пустых полей в попапе и нажатие Confirm/Continue/Deposit/Pay
        Returns: (filled_fields_list, did_click_confirm)
        filled_fields_list: список заполненных полей ['upi', 'phone', 'aadhaar', 'fullname']
        did_click_confirm: True если кнопка confirm была найдена и нажата
        """
        import re
        
        # 1) Сначала заполняем все пустые поля
        
        # Получаем значения из конфига
        provider_form_data = config.get("provider_form_data", {})
        upi_id = provider_form_data.get("upi_id", "")
        phone = provider_form_data.get("phone_number", "")
        aadhaar = provider_form_data.get("aadhaar", "")
        fullname = provider_form_data.get("fullname", "")
        
        filled_fields = []
        did_fill_any = False
        
        # 2) Заполняем UPI ID (если пустое)
        if upi_id:
            filled = await self._fill_if_visible(
                deposit_frame.get_by_label(re.compile(r"upi\s*id", re.I)),
                upi_id
            ) or await self._fill_if_visible(
                deposit_frame.locator("input[name*='upi' i], input[placeholder*='upi' i], input[id*='upi' i]"),
                upi_id
            )
            if filled:
                filled_fields.append("upi")
                did_fill_any = True
                print("  ✓ Заполнено поле UPI ID")
        
        # 3) Заполняем Phone Number (если пустое)
        if phone:
            filled = await self._fill_if_visible(
                deposit_frame.get_by_label(re.compile(r"number|phone|mobile", re.I)),
                phone
            ) or await self._fill_if_visible(
                deposit_frame.locator("input[type='tel'], input[name*='phone' i], input[placeholder*='phone' i], input[id*='phone' i]"),
                phone
            )
            if filled:
                filled_fields.append("phone")
                did_fill_any = True
                print("  ✓ Заполнено поле Phone Number")
        
        # 4) Заполняем Aadhaar (если пустое)
        if aadhaar:
            filled = await self._fill_if_visible(
                deposit_frame.get_by_label(re.compile(r"aadhaar", re.I)),
                aadhaar
            ) or await self._fill_if_visible(
                deposit_frame.locator("input[name*='aadhaar' i], input[placeholder*='aadhaar' i], input[id*='aadhaar' i]"),
                aadhaar
            )
            if filled:
                filled_fields.append("aadhaar")
                did_fill_any = True
                print("  ✓ Заполнено поле Aadhaar")
        
        # 5) Заполняем Full Name / First name and surname (если пустое)
        if fullname:
            filled = await self._fill_if_visible(
                deposit_frame.get_by_label(re.compile(r"first\s*name\s*(and|&)?\s*surname|full\s*name|name", re.I)),
                fullname
            ) or await self._fill_if_visible(
                deposit_frame.locator("input[name*='name' i], input[placeholder*='name' i], input[id*='name' i], input[name*='fullname' i], input[name*='full_name' i]"),
                fullname
            )
            if filled:
                filled_fields.append("fullname")
                did_fill_any = True
                print("  ✓ Заполнено поле First name and surname")
        
        if not did_fill_any:
            print("  → Поля не найдены или уже заполнены, продолжаем")
        else:
            print(f"  ✓ Всего заполнено полей: {len(filled_fields)} ({', '.join(filled_fields)})")
        
        # ВСЕГДА нажимаем кнопку подтверждения после заполнения полей (или если поля уже заполнены)
        did_click_confirm = False
        
        # Небольшая задержка перед поиском кнопки (UI может обновляться)
        await deposit_frame.wait_for_timeout(500)
        
        # Диагностика: проверяем наличие всех кнопок на странице
        try:
            all_buttons = deposit_frame.locator("button")
            button_count = await all_buttons.count()
            print(f"  → Найдено кнопок на странице: {button_count}")
            if button_count > 0:
                for i in range(min(button_count, 5)):  # Показываем первые 5
                    try:
                        btn = all_buttons.nth(i)
                        text = await btn.inner_text()
                        is_visible = await btn.is_visible()
                        print(f"    Кнопка {i+1}: '{text[:30]}' (visible={is_visible})")
                    except:
                        pass
        except Exception as e:
            print(f"  → Ошибка при диагностике кнопок: {e}")
        
        # Пробуем несколько способов найти и нажать кнопку
        confirm_btn = await self.find_confirm_clickable(deposit_frame)
        if confirm_btn:
            try:
                # Проверяем видимость и enabled состояние
                is_visible = await confirm_btn.is_visible()
                is_disabled = await confirm_btn.evaluate("el => el.disabled || el.getAttribute('aria-disabled')==='true'")
                
                if is_visible and not is_disabled:
                    # Пробуем обычный клик
                    try:
                        await confirm_btn.click(force=True, timeout=8000)
                        print("  ✓ Нажата кнопка Confirm/Continue/Deposit/Pay после заполнения полей")
                        did_click_confirm = True
                    except Exception as e1:
                        # Fallback: клик через координаты
                        try:
                            box = await confirm_btn.bounding_box()
                            if box:
                                # Получаем page через owner_frame
                                page = deposit_frame.page if hasattr(deposit_frame, 'page') else None
                                if page:
                                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    print("  ✓ Нажата кнопка через координаты мыши")
                                    did_click_confirm = True
                        except Exception as e2:
                            print(f"  ⚠️  Ошибка при нажатии кнопки (обычный клик: {e1}, координаты: {e2})")
                else:
                    print(f"  ⚠️  Кнопка найдена, но не доступна (visible={is_visible}, disabled={is_disabled})")
            except Exception as e:
                print(f"  ⚠️  Ошибка при проверке/нажатии кнопки подтверждения: {e}")
        
        # Если кнопка не найдена или не нажата, пробуем fallback методы
        if not did_click_confirm:
            print("  → Кнопка не найдена через find_confirm_clickable, пробуем fallback методы...")
            # Fallback 1: используем click_deposit_action
            try:
                clicked = await self.click_deposit_action(deposit_frame)
                if clicked:
                    print("  ✓ Нажата кнопка действия через click_deposit_action")
                    did_click_confirm = True
            except Exception as e:
                print(f"  ⚠️  Ошибка при нажатии кнопки через click_deposit_action: {e}")
            
            # Fallback 2: поиск по XPath
            if not did_click_confirm:
                try:
                    import re
                    xpath_selectors = [
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]",
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'deposit')]",
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                        "//*[@role='button' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]",
                    ]
                    for xpath in xpath_selectors:
                        try:
                            btn = deposit_frame.locator(f"xpath={xpath}").first
                            if await btn.count() > 0:
                                await btn.wait_for(state="visible", timeout=2000)
                                is_disabled = await btn.evaluate("el => el.disabled || el.getAttribute('aria-disabled')==='true'")
                                if not is_disabled:
                                    await btn.click(force=True, timeout=8000)
                                    print(f"  ✓ Нажата кнопка через XPath: {xpath[:50]}...")
                                    did_click_confirm = True
                                    break
                        except:
                            continue
                except Exception as e:
                    print(f"  ⚠️  Ошибка при поиске через XPath: {e}")
        
        return filled_fields, did_click_confirm
    
    def etld1(self, url: str) -> str:
        """Извлекает eTLD+1 домен из URL"""
        if not url or not url.startswith(("http://", "https://")):
            return ""
        try:
            extracted = tldextract.extract(url)
            if extracted.domain and extracted.suffix:
                return f"{extracted.domain}.{extracted.suffix}".lower()
            return extracted.domain.lower() if extracted.domain else ""
        except:
            return ""
    
    async def wait_external_signal(self, page: Page, merchant_etld1: str, timeout_ms: int = 12000, network_requests: List[str] = None) -> tuple:
        """
        Ждём внешний домен провайдера (iframe, navigation, network requests)
        Проверяет каждые 250ms
        Returns: (detected_in, url, domain) или (None, None, None)
        """
        NOISY = ("googleapis.com", "gstatic.com", "cedexis.com", "doubleclick.net", 
                 "googletagmanager.com", "google-analytics.com", "facebook.com", "fbcdn.net",
                 "hotjar.com", "yandex.ru", "suphelper.top")
        
        if network_requests is None:
            network_requests = []
        
        deadline = time.time() + timeout_ms / 1000.0
        
        while time.time() < deadline:
            # 1) Проверяем iframes (приоритет)
            for fr in page.frames:
                url = fr.url or ""
                if not url.startswith(("http://", "https://")):
                    continue
                
                d = self.etld1(url)
                if d and d != merchant_etld1 and not any(n in d for n in NOISY):
                    print(f"  ✓ Найден внешний домен провайдера (iframe): {d} ({url[:80]})")
                    return "frame", url, d
            
            # 2) Проверяем navigation
            current_url = page.url
            current_domain = self.etld1(current_url)
            if current_domain and current_domain != merchant_etld1 and not any(n in current_domain for n in NOISY):
                print(f"  ✓ Найден внешний домен провайдера (navigation): {current_domain}")
                return "navigation", current_url, current_domain
            
            # 3) Проверяем network requests
            for req_url in network_requests:
                if not req_url or not req_url.startswith(("http://", "https://")):
                    continue
                
                d = self.etld1(req_url)
                if d and d != merchant_etld1 and not any(n in d for n in NOISY):
                    print(f"  ✓ Найден внешний домен провайдера (network): {d} ({req_url[:80]})")
                    return "network", req_url, d
            
            await page.wait_for_timeout(250)  # Проверяем каждые 250ms
        
        return None, None, None
    
    async def fill_if_empty(self, locator, value: str, field_name: str = "") -> bool:
        """
        Заполняет поле, если оно пустое
        Returns: True если поле было заполнено, False если уже заполнено или не найдено
        """
        from playwright.async_api import TimeoutError as PWTimeout
        
        if await locator.count() == 0:
            return False
        
        try:
            el = locator.first
            await el.wait_for(state="visible", timeout=5000)
            current = (await el.input_value() or "").strip()
            if current:
                return False  # Уже заполнено
            
            # Важно: некоторые формы реагируют только на "type" + blur/tab
            await el.click(force=True)
            await el.fill("")  # На всякий случай очищаем
            await el.type(value, delay=30)
            await el.press("Tab")
            print(f"  ✓ Заполнено поле {field_name}: {value}")
            return True
        except PWTimeout:
            return False
        except Exception:
            return False
    
    async def fill_modal_fields_if_needed(self, frame, config: dict):
        """
        Заполняет пустые поля в модалке (все доступные поля: UPI ID, Phone, Email, First name, Surname, Address, City, Postcode, Province, Aadhaar)
        Заполняет только пустые поля, даже если другие уже заполнены
        """
        provider_form_data = config.get("provider_form_data", {})
        upi_id = provider_form_data.get("upi_id", "")
        phone = provider_form_data.get("phone_number", "")
        email = provider_form_data.get("email", "")
        first_name = provider_form_data.get("first_name", "")
        surname = provider_form_data.get("surname", "")
        fullname = provider_form_data.get("fullname", "")
        address = provider_form_data.get("address", "")
        city = provider_form_data.get("city", "")
        postcode = provider_form_data.get("postcode", "")
        province = provider_form_data.get("province", "")
        aadhaar = provider_form_data.get("aadhaar", "")
        
        filled_count = 0
        
        # First name
        if first_name:
            first_name_selectors = [
                "xpath=//*[normalize-space()='First name:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'First name')]/following::input[1]",
                "input[name*='firstname' i]",
                "input[name*='first_name' i]",
                "input[placeholder*='first name' i]",
            ]
            for sel in first_name_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, first_name, "First name"):
                    filled_count += 1
                    break
        
        # Surname
        if surname:
            surname_selectors = [
                "xpath=//*[normalize-space()='Surname:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'Surname')]/following::input[1]",
                "input[name*='surname' i]",
                "input[name*='lastname' i]",
                "input[name*='last_name' i]",
                "input[placeholder*='surname' i]",
            ]
            for sel in surname_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, surname, "Surname"):
                    filled_count += 1
                    break
        
        # Full Name (если first_name и surname не заполнили, пробуем fullname)
        if fullname and not first_name and not surname:
            name_selectors = [
                "xpath=//*[normalize-space()='First name and surname:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'First name and surname')]/following::input[1]",
                "xpath=//*[normalize-space()='Full name:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'Full name')]/following::input[1]",
            ]
            for sel in name_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, fullname, "Full Name"):
                    filled_count += 1
                    break
        
        # Email
        if email:
            email_selectors = [
                "xpath=//*[normalize-space()='Email:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'Email')]/following::input[1]",
                "input[type='email']",
                "input[name*='email' i]",
                "input[placeholder*='email' i]",
            ]
            for sel in email_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, email, "Email"):
                    filled_count += 1
                    break
        
        # Phone Number
        if phone:
            phone_selectors = [
                "xpath=//*[normalize-space()='Phone number:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'Phone number')]/following::input[1]",
                "input[type='tel']",
                "input[name*='phone' i]",
                "input[placeholder*='phone' i]",
            ]
            for sel in phone_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, phone, "Phone"):
                    filled_count += 1
                    break
        
        # Address
        if address:
            address_selectors = [
                "xpath=//*[normalize-space()='Address:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'Address')]/following::input[1]",
                "input[name*='address' i]",
                "textarea[name*='address' i]",
                "input[placeholder*='address' i]",
            ]
            for sel in address_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, address, "Address"):
                    filled_count += 1
                    break
        
        # City
        if city:
            city_selectors = [
                "xpath=//*[normalize-space()='City:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'City')]/following::input[1]",
                "input[name*='city' i]",
                "input[placeholder*='city' i]",
            ]
            for sel in city_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, city, "City"):
                    filled_count += 1
                    break
        
        # Postcode
        if postcode:
            postcode_selectors = [
                "xpath=//*[normalize-space()='Postcode:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'Postcode')]/following::input[1]",
                "xpath=//*[normalize-space()='Postal code:']/following::input[1]",
                "input[name*='postcode' i]",
                "input[name*='postal' i]",
                "input[name*='zip' i]",
                "input[placeholder*='postcode' i]",
            ]
            for sel in postcode_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, postcode, "Postcode"):
                    filled_count += 1
                    break
        
        # Province (select/dropdown)
        if province:
            try:
                province_selectors = [
                    "xpath=//*[normalize-space()='Province:']/following::select[1]",
                    "xpath=//*[contains(normalize-space(),'Province')]/following::select[1]",
                    "select[name*='province' i]",
                    "select[name*='state' i]",
                ]
                for sel in province_selectors:
                    try:
                        select_loc = frame.locator(sel).first
                        if await select_loc.count() > 0:
                            current = await select_loc.input_value()
                            if not current.strip():
                                await select_loc.select_option(label=province, timeout=2000)
                                print(f"  ✓ Заполнено поле Province: {province}")
                                filled_count += 1
                                break
                    except:
                        continue
            except:
                pass
        
        # UPI ID - приоритетное поле (если есть)
        if upi_id:
            upi_selectors = [
                "xpath=//*[normalize-space()='UPI ID:']/following::input[1]",
                "xpath=//*[contains(normalize-space(),'UPI ID')]/following::input[1]",
                "input[name*='upi' i]",
                "input[placeholder*='upi' i]",
                "xpath=//label[contains(., 'UPI') or contains(., 'upi')]/following::input[1]",
                "xpath=//div[contains(., 'UPI ID')]/following::input[1]",
            ]
            for sel in upi_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, upi_id, "UPI ID"):
                    filled_count += 1
                    break
        
        # Aadhaar
        if aadhaar:
            aadhaar_selectors = [
                "input[name*='aadhaar' i]",
                "input[placeholder*='aadhaar' i]",
            ]
            for sel in aadhaar_selectors:
                input_loc = frame.locator(sel).first
                if await self.fill_if_empty(input_loc, aadhaar, "Aadhaar"):
                    filled_count += 1
                    break
        
        if filled_count > 0:
            print(f"  ✓ Заполнено пустых полей: {filled_count}")
        else:
            print("  → Все поля уже заполнены или не найдены")
    
    async def detect_step(self, deposit_frame) -> int:
        """
        Определяет текущий шаг модалки:
        1 - форма с полями (amount, UPI, phone, etc.)
        2 - модалка с реквизитами/QR кодом
        3 - финальный шаг или внешний редирект
        """
        try:
            # Проверяем наличие реквизитов/QR кода (шаг 2)
            qr_code = deposit_frame.locator("img[src*='qr'], canvas, svg[class*='qr'], [class*='qr-code'], [id*='qr']")
            if await qr_code.count() > 0:
                return 2
            
            # Проверяем наличие текста с реквизитами
            account_text = deposit_frame.locator("text=/account|upi|vpa|virtual|payment/i")
            if await account_text.count() > 0:
                return 2
            
            # По умолчанию считаем шагом 1 (форма с полями)
            return 1
        except Exception:
            return 1
    
    async def click_primary_action(self, deposit_frame) -> bool:
        """
        Находит и нажимает основную action-кнопку (Confirm/Continue/Deposit/Pay)
        Returns: True если кнопка была найдена и нажата, False иначе
        """
        try:
            # Используем существующий метод click_deposit_action
            return await self.click_deposit_action(deposit_frame)
        except Exception as e:
            print(f"  ⚠️  Ошибка в click_primary_action: {e}")
            return False
    
    async def handle_modal_steps(self, page: Page, deposit_frame, merchant_domain: str, config: dict, network_requests: List[str] = None):
        """
        Мульти-шаговый обработчик модалки: обрабатывает внутренний 2-шаговый сценарий или внешний редирект
        Returns: (provider_domain, provider_url, detected_in, payment_details) или (None, None, None, None)
        payment_details: dict с upi_id, name, code для внутреннего сценария
        """
        merchant_etld1 = self.etld1(merchant_domain if merchant_domain.startswith(("http://", "https://")) else f"https://{merchant_domain}")
        
        if network_requests is None:
            network_requests = []
        
        payment_details = None
        
        # До 3 шагов: DEPOSIT/CONFIRM -> CONFIRM -> ...
        for step in range(1, 4):
            try:
                # Пересобираем deposit_frame перед каждым шагом (избегаем Frame detached)
                deposit_frame = await self.get_deposit_frame(page)
                if not deposit_frame:
                    print(f"  ⚠️  Deposit frame не найден на шаге {step}")
                    break
                
                # Определяем текущий шаг
                current_step = await self.detect_step(deposit_frame)
                print(f"  → Текущий шаг: {current_step} (итерация {step})")
                
                # (A) Заполняем пустые поля (все доступные: First name, Surname, Email, Phone, Address, City, Postcode, Province, UPI ID, Aadhaar)
                # Заполняем только пустые поля, даже если другие уже заполнены
                await self.fill_modal_fields_if_needed(deposit_frame, config)
                
                # (B) Проверяем чекбоксы "I agree"
                try:
                    checkboxes = deposit_frame.locator("input[type='checkbox']")
                    checkbox_count = await checkboxes.count()
                    for i in range(checkbox_count):
                        try:
                            cb = checkboxes.nth(i)
                            parent = cb.locator("xpath=ancestor::*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]")
                            if await parent.count() > 0:
                                await cb.check()
                                print(f"  ✓ Чекбокс 'I agree' установлен (шаг {step})")
                                break
                        except:
                            continue
                except:
                    pass
                
                # (C) Нажимаем action-кнопку (с проверкой enabled)
                action_clicked = await self.click_primary_action(deposit_frame)
                if not action_clicked:
                    print(f"  ⚠️  Action-кнопка не найдена или disabled на шаге {step}")
                    # Если на шаге 2 и кнопка не найдена - возможно уже показываются реквизиты
                    if current_step == 2:
                        break
                    break
                
                # (D) Если это шаг 2 (модалка с реквизитами) - сразу нажимаем CONFIRM
                await page.wait_for_timeout(1000)  # Даём UI обновиться
                
                # Проверяем, появились ли реквизиты (шаг 2)
                updated_step = await self.detect_step(deposit_frame)
                if updated_step == 2:
                    # При такой модалке сразу нажимаем CONFIRM без извлечения реквизитов
                    print(f"  → Обнаружена модалка с реквизитами (шаг 2), нажимаем CONFIRM")
                    await page.wait_for_timeout(500)
                    confirm_clicked = await self.click_primary_action(deposit_frame)
                    if confirm_clicked:
                        print(f"  ✓ Нажат CONFIRM на шаге 2")
                        # Для внутреннего сценария возвращаем internal_or_delayed
                        return "internal_or_delayed", page.url, "internal_flow", None
                
                # (E) Ждём внешний сигнал (редирект) до 10 секунд после CONFIRM
                sig = await self.wait_external_signal(page, merchant_etld1, timeout_ms=10000, network_requests=network_requests)
                if sig:
                    detected_in, url, domain = sig
                    return domain, url, detected_in, None
                
                # Если внешнего домена нет - даём UI обновиться и идём на следующий шаг
                await page.wait_for_timeout(500)
                
            except Exception as e:
                print(f"  ⚠️  Ошибка на шаге {step}: {e}")
                if "Frame was detached" in str(e):
                    # Пытаемся восстановить frame
                    deposit_frame = await self.get_deposit_frame(page)
                    if not deposit_frame:
                        break
                    continue
                break
        
        # Если дошли до конца и не нашли внешний домен, но есть реквизиты - возвращаем их
        if payment_details:
            return "internal_or_delayed", page.url, "internal_flow", payment_details
        
        return None, None, None, None
    
    async def click_action_buttons_until_external(
        self, 
        page: Page, 
        deposit_frame, 
        merchant_host: str, 
        network_requests: List[str] = None,
        timeout_total_ms: int = 15000
    ) -> tuple:
        """
        Нажимает кнопки confirm/continue/deposit/pay до 2 раз, каждый раз проверяя внешний домен
        Returns: (provider_domain, provider_url, detected_in) или (None, None, None)
        """
        if network_requests is None:
            network_requests = []
        
        # Две попытки нажать action (continue/confirm/deposit/pay)
        for attempt in range(2):
            # Находим кнопку confirm/continue/deposit/pay
            confirm_btn = await self.find_confirm_clickable(deposit_frame)
            if confirm_btn:
                try:
                    await confirm_btn.click(force=True, timeout=8000)
                    print(f"  ✓ Нажата кнопка Confirm/Continue/Deposit/Pay (попытка {attempt + 1})")
                except Exception as e:
                    print(f"  ⚠️  Ошибка при нажатии кнопки (попытка {attempt + 1}): {e}")
            
            # Подождать появление внешнего домена чуть-чуть (6 секунд)
            dom, url, detected_in = await self.wait_external_after_confirm(page, merchant_host, timeout_ms=6000, network_requests=network_requests)
            if dom:
                return dom, url, detected_in
            
            # Фрейм мог обновиться — переинициализируем deposit_frame
            deposit_frame = await self.get_deposit_frame(page)
            if not deposit_frame:
                break
        
        return None, None, None
    
    def pick_provider_domain(self, urls, merchant_host: str) -> Optional[str]:
        """Выбрать домен провайдера из списка URL, отфильтровав трекинг"""
        TRACKING = ("google.", "gstatic.", "doubleclick.", "googlesyndication.",
                    "googletagmanager.", "google-analytics.", "facebook.", "fbcdn.",
                    "hotjar.", "yandex.", "tiktok.", "cedexis.", "fonts.googleapis.com")
        
        def is_noise(host: str) -> bool:
            h = host.lower()
            return any(x in h for x in TRACKING)
        
        for u in reversed(urls):
            host = urlparse(u).netloc.lower()
            if not host:
                        continue
            if merchant_host in host:
                continue
            if "suphelper" in host:
                continue
            if is_noise(host):
                continue
            return host
        return None
    
    async def wait_external_after_confirm(self, page: Page, merchant_host: str, timeout_ms: int = 12000, network_requests: List[str] = None) -> tuple:
        """
        Ожидание внешнего домена провайдера после confirm (wait-loop с проверкой каждые 500ms)
        Проверяет: iframes, navigation, network requests
        Returns: (provider_domain, provider_url, detected_in) или (None, None, None)
        """
        from urllib.parse import urlparse
        
        TRACKING = ("google.", "gstatic.", "doubleclick.", "googlesyndication.",
                    "googletagmanager.", "google-analytics.", "facebook.", "fbcdn.",
                    "hotjar.", "yandex.", "tiktok.", "cedexis.", "fonts.googleapis.com", "suphelper.")
        
        def is_noise_domain(host: str) -> bool:
            h = host.lower()
            return any(x in h for x in TRACKING)
        
        if network_requests is None:
            network_requests = []
        
        seen = set()
        start_time = time.time()
        timeout_seconds = timeout_ms / 1000.0
        
        print(f"  → Ожидание внешнего домена провайдера (timeout: {timeout_seconds}s)...")
        
        while time.time() - start_time < timeout_seconds:
            # 1) Проверяем iframe (приоритет)
            for fr in page.frames:
                url = fr.url or ""
                if not url.startswith(("http://", "https://")):
                        continue
                    
                host = urlparse(url).netloc.lower()
                if not host:
                    continue
                
                # Пропускаем домен мерчанта и шум
                if merchant_host in host or "1xbet" in host or "dafabet" in host:
                    continue
                
                if is_noise_domain(host):
                    continue
                
                # Нашли внешний домен провайдера
                domain = self.get_domain(url)
                if domain and domain not in seen:
                    seen.add(domain)
                    print(f"  ✓ Найден внешний домен провайдера (iframe): {domain} ({url[:80]})")
                    return domain, url, "frame"
            
            # 2) Проверяем navigation (page.url)
            current_url = page.url
            current_domain = self.get_domain(current_url)
            if current_domain and current_domain != merchant_host:
                if not is_noise_domain(current_domain):
                    if current_domain not in seen:
                        seen.add(current_domain)
                        print(f"  ✓ Найден внешний домен провайдера (navigation): {current_domain}")
                        return current_domain, current_url, "navigation"
            
            # 3) Проверяем network requests (если переданы)
            for req_url in network_requests:
                if not req_url or not req_url.startswith(("http://", "https://")):
                    continue
                
                host = urlparse(req_url).netloc.lower()
                if not host:
                    continue
                
                # Пропускаем домен мерчанта и шум
                if merchant_host in host or "1xbet" in host or "dafabet" in host:
                    continue
                
                if is_noise_domain(host):
                    continue
                
                # Нашли внешний домен провайдера
                domain = self.get_domain(req_url)
                if domain and domain not in seen:
                    seen.add(domain)
                    print(f"  ✓ Найден внешний домен провайдера (network): {domain} ({req_url[:80]})")
                    return domain, req_url, "network"
            
            await page.wait_for_timeout(500)  # Проверяем каждые 500ms
        
        print(f"  ⚠️  Внешний домен провайдера не найден за {timeout_seconds}s")
        return None, None, None
    
    async def find_ewallets_providers(self, page: Page, config: dict) -> List[Dict]:
        """Поиск всех провайдеров в секции E-WALLETS с правильным поиском по изображениям и тексту"""
        providers = []
        
        try:
            # Находим контекст (page или frame), где находится E-WALLETS
            ctx = await self.find_wallets_context(page)
            if not ctx:
                print("⚠️  E-WALLETS не найден. Ищем все провайдеры на странице.")
                return await self.find_all_providers(page, config)
            
            # Дожидаемся загрузки контента
            await ctx.wait_for_load_state("domcontentloaded", timeout=10000)
            
            # Ищем заголовок E-WALLETS
            header = ctx.locator("text=E-WALLETS").first
            if not await header.is_visible(timeout=3000):
                print("⚠️  Заголовок E-WALLETS не виден. Ищем все провайдеры на странице.")
                return await self.find_all_providers(page, config)
            
            print("  ✓ Заголовок E-WALLETS найден")
            
            # Скроллим к секции и даём UI догрузиться
            await header.scroll_into_view_if_needed()
            await page.wait_for_timeout(800)  # Пауза на отрисовку плиток
            
            # Диагностика: проверяем наличие изображений Paytm/UPI
            try:
                imgs = await ctx.evaluate("""
                    () => Array.from(document.querySelectorAll('img'))
                      .map(i => ({alt: i.alt || '', src: i.src || ''}))
                      .filter(x => {
                        const alt = (x.alt || '').toLowerCase();
                        const src = (x.src || '').toLowerCase();
                        return alt.includes('paytm') || src.includes('paytm') ||
                               alt.includes('upi') || src.includes('upi');
                      })
                """)
                if imgs:
                    print(f"  → Найдено изображений провайдеров: {len(imgs)}")
                    for img in imgs[:3]:  # Показываем первые 3
                        print(f"    - alt: {img.get('alt', '')[:50]}, src: {img.get('src', '')[:80]}")
            except:
                pass
            
            # Ищем карточки по изображениям (приоритетный метод)
            # Если обе карточки имеют одинаковое изображение (например, upi.png), различаем их по тексту
            target_providers = [
                ("paytm", "paytm", ["paytm"]),
                ("upi fast", "upi", ["upi", "fast", "upi fast"]),
            ]
            
            for target_name, search_term, text_keywords in target_providers:
                found = False
                
                # Метод 1: Поиск по изображениям (alt/src)
                try:
                    # Ищем все изображения с search_term
                    img_locators = ctx.locator(f"img[alt*='{search_term}' i], img[src*='{search_term}' i]")
                    img_count = await img_locators.count()
                    
                    if img_count > 0:
                        print(f"  → Найдено изображений для '{target_name}': {img_count}")
                        
                        # Если несколько изображений (например, обе карточки с upi.png), различаем по тексту
                        for i in range(img_count):
                            img_locator = img_locators.nth(i)
                            # Находим кликабельную карточку от изображения
                            card = self.tile_clickable_from(img_locator)
                            if await card.count() == 0:
                                # Запасной вариант: ближайший div
                                card = img_locator.locator("xpath=ancestor::div[1]")
                            
                            if await card.count() > 0:
                                # Получаем текст карточки для проверки
                                try:
                                    card_text = (await card.inner_text()).strip().lower()[:200]
                                except:
                                    card_text = ""
                                
                                # Проверяем, соответствует ли карточка target_name по тексту
                                if target_name == "paytm":
                                    # Для Paytm ищем "paytm" в тексте
                                    if "paytm" not in card_text:
                                        continue
                                elif target_name == "upi fast":
                                    # Для UPI Fast ищем "upi" и "fast" в тексте, но не "paytm"
                                    if "paytm" in card_text or ("upi" not in card_text and "fast" not in card_text):
                                        continue
                                
                                if await card.is_visible(timeout=2000):
                                    await card.scroll_into_view_if_needed()
                                    await page.wait_for_timeout(300)
                    
                                    providers.append({
                                        "key": target_name,
                                        "name": target_name,
                                        "img_hint": search_term,
                                        "button_text": card_text[:100] or target_name,
                                    })
                                    print(f"  ✓ Найден провайдер по изображению: {target_name} (текст: {card_text[:50]})")
                                    found = True
                                    break
                except Exception as e:
                    print(f"  ⚠️  Ошибка при поиске по изображению '{target_name}': {e}")
                
                # Метод 2: Поиск по тексту (если не нашли по изображению)
                if not found:
                    try:
                        import re
                        # Используем regex для поиска текста
                        if target_name == "paytm":
                            text_pattern = re.compile(r"\bpaytm\b", re.I)
                        else:
                            text_pattern = re.compile(r"\bupi\s*fast\b", re.I)
                        
                        text_locator = ctx.get_by_text(text_pattern).first
                        if await text_locator.count() > 0:
                            # Ждём, пока элемент будет attached
                            await text_locator.wait_for(state="attached", timeout=5000)
                            await text_locator.scroll_into_view_if_needed()
                            await page.wait_for_timeout(300)
                            
                            # Находим кликабельную карточку от текста
                            card = self.tile_clickable_from(text_locator)
                            if await card.count() == 0:
                                # Запасной вариант: ближайший div
                                card = text_locator.locator("xpath=ancestor::div[1]")
                            
                            if await card.count() > 0 and await card.is_visible(timeout=2000):
                                try:
                                    elem_text = (await card.inner_text()).strip().lower()[:100] or target_name
                                except:
                                    elem_text = target_name
                                
                                providers.append({
                                    "key": target_name,
                                    "name": target_name,
                                    "img_hint": search_term,
                        "button_text": elem_text,
                    })
                                print(f"  ✓ Найден провайдер по тексту: {target_name}")
                                found = True
                    except Exception as e:
                        print(f"  ⚠️  Ошибка при поиске по тексту '{target_name}': {e}")
                    
                if not found:
                    print(f"  ⚠️  Провайдер '{target_name}' не найден")
            
            print(f"✓ Найдено провайдеров в E-WALLETS: {len(providers)}")
            return providers
            
        except Exception as e:
            print(f"❌ Ошибка при поиске провайдеров в E-WALLETS: {e}")
            import traceback
            traceback.print_exc()
            return await self.find_all_providers(page, config)
    
    async def find_all_providers(self, page: Page, config: dict) -> List[Dict]:
        """Поиск всех провайдеров на странице (fallback)"""
        providers = []
        selectors = config.get("selectors", {})
        
        # Список известных провайдеров для поиска (приоритетные в начале)
        known_providers = [
            "upi fast", "paytm",  # Приоритетные провайдеры
            "upi", "phonepe", "gpay", "google pay",
            "skrill", "neteller", "jetonbank", "moneygo", "airtm", "icash",
            "tron", "tether", "bitcoin", "ethereum", "litecoin", "dogecoin",
            "razorpay", "payu", "ccavenue", "instamojo", "cashfree"
        ]
        
        # Сначала пробуем селекторы из конфига
        provider_button_selectors = selectors.get("provider_buttons", "").split(", ")
        provider_link_selectors = selectors.get("provider_links", "").split(", ")
        
        all_selectors = provider_button_selectors + provider_link_selectors
        seen_elements = set()
        
        for selector in all_selectors:
            if not selector.strip():
                continue
            try:
                elements = await page.locator(selector).all()
                for elem in elements:
                    try:
                        elem_text = (await elem.inner_text()).strip()[:100].lower()
                        if elem_text and elem not in seen_elements:
                            seen_elements.add(elem)
                            providers.append({
                                "element": elem,
                                "name": elem_text,
                                "button_text": elem_text,
                            })
                    except:
                        pass
            except:
                continue
        
        # Если не нашли через селекторы, ищем по тексту провайдеров
        if len(providers) == 0:
            print("  Поиск провайдеров по тексту...")
            
            # Сначала ищем все кликабельные элементы на странице
            print("  → Поиск всех кликабельных элементов...")
            all_clickable = []
            clickable_selectors = [
                "button",
                "a",
                "div[role='button']",
                "div[onclick]",
                "[class*='payment']",
                "[class*='provider']",
                "[class*='method']",
                "[class*='wallet']",
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for elem in elements:
                        try:
                            if await elem.is_visible(timeout=500):
                                all_clickable.append(elem)
                        except:
                            pass
                except:
                    continue
            
            print(f"  → Найдено кликабельных элементов: {len(all_clickable)}")
            
            # Проверяем каждый элемент на наличие текста провайдеров
            for elem in all_clickable:
                try:
                    elem_text = (await elem.inner_text()).strip().lower()[:200]
                    if not elem_text:
                        continue
                    
                    # Ищем совпадения с известными провайдерами
                    for provider_name in known_providers:
                        if provider_name in elem_text and elem not in seen_elements:
                            seen_elements.add(elem)
                            providers.append({
                                "element": elem,
                                "name": provider_name,
                                "button_text": elem_text[:100],
                            })
                            print(f"  ✓ Найден провайдер: {provider_name} (текст: {elem_text[:50]})")
                            break  # Нашли провайдера для этого элемента
                except:
                    continue
            
            # Если всё ещё не нашли, используем XPath поиск
            if len(providers) == 0:
                print("  → XPath поиск провайдеров...")
                for provider_name in known_providers:
                    try:
                        # Для "UPI Fast" и "Paytm" используем более точный поиск
                        search_text = provider_name
                        if provider_name == "upi fast":
                            search_text = "upi fast"
                        elif provider_name == "paytm":
                            search_text = "paytm"
                        
                        # Ищем элементы, содержащие название провайдера (точное совпадение или частичное)
                        xpath_variants = [
                        f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_text}')]",
                        f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_text}')]",
                        f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_text}')]",
                        f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_text}')]",
                        f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_text}')]",
                        f"//*[@aria-label and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_text}')]",
                        ]
                        
                        for xpath in xpath_variants:
                            try:
                                elements = await page.locator(f"xpath={xpath}").all()
                                
                                for elem in elements:
                                    try:
                                        # Проверяем, что это кликабельный элемент
                                        tag = await elem.evaluate("el => el.tagName.toLowerCase()")
                                        if tag in ["button", "a", "div", "span"]:
                                            # Находим ближайший кликабельный родитель
                                            clickable = elem
                                            try:
                                                parent = elem.locator("xpath=./ancestor::button[1] | ./ancestor::a[1] | ./ancestor::div[@onclick][1] | ./ancestor::div[contains(@class, 'payment')][1] | ./ancestor::div[@role='button'][1]").first
                                                if await parent.is_visible(timeout=500):
                                                    clickable = parent
                                            except:
                                                pass
                                            
                                            if clickable not in seen_elements:
                                                seen_elements.add(clickable)
                                                try:
                                                    elem_text = (await clickable.inner_text()).strip()[:100].lower()
                                                    # Проверяем, содержит ли текст название провайдера
                                                    if elem_text and (search_text in elem_text or provider_name in elem_text):
                                                        providers.append({
                                                            "element": clickable,
                                                            "name": provider_name,
                                                            "button_text": elem_text,
                                                        })
                                                        print(f"  ✓ Найден провайдер: {provider_name} (текст: {elem_text[:50]})")
                                                        break  # Нашли один элемент для этого провайдера, переходим к следующему
                                                except:
                                                    # Если не можем получить текст, но элемент кликабельный, добавляем его
                                                    if provider_name in ["upi fast", "paytm"]:
                                                        providers.append({
                                                            "element": clickable,
                                                            "name": provider_name,
                                                            "button_text": provider_name,
                                                        })
                                                        print(f"  ✓ Найден кликабельный элемент для: {provider_name}")
                                                        break
                                    except:
                                        continue
                            except:
                                continue
                    except:
                        continue
        
        # Также ищем все кликабельные элементы с изображениями провайдеров
        try:
            all_images = await page.locator("img").all()
            for img in all_images:
                try:
                    alt_text = (await img.get_attribute("alt") or "").lower()
                    src = (await img.get_attribute("src") or "").lower()
                    
                    # Проверяем, не является ли это логотипом провайдера
                    is_provider = any(prov in alt_text or prov in src for prov in known_providers)
                    
                    if is_provider:
                        # Находим родительский кликабельный элемент
                        try:
                            parent = img.locator("xpath=./ancestor::button[1] | ./ancestor::a[1] | ./ancestor::div[@onclick][1] | ./ancestor::div[contains(@class, 'payment')][1] | ./parent::div[1]").first
                            if await parent.is_visible(timeout=500) and parent not in seen_elements:
                                seen_elements.add(parent)
                                elem_text = (await parent.inner_text()).strip()[:100].lower() or alt_text
                                providers.append({
                                    "element": parent,
                                    "name": alt_text if alt_text else "unknown",
                                    "button_text": elem_text,
                                })
                        except:
                            pass
                except:
                    continue
        except:
            pass
        
        print(f"  Всего найдено провайдеров: {len(providers)}")
        return providers
    
    async def process_provider_button(
        self, 
        page: Page, 
        provider_info: Dict, 
        merchant_domain: str,
        cashier_url: str,
        idx: int,
        total: int,
        config: dict = None,
        retry: bool = False
    ) -> Optional[Dict]:
        """Обработка одной кнопки провайдера с перехватом popup, iframe, network (attempt loop с пересозданием locator'ов)"""
        provider_key = provider_info.get("key") or provider_info.get("name", "unknown")
        provider_name = provider_info.get("name", "unknown")
        button_text = provider_info.get("button_text", "")
        
        print(f"\n[{idx+1}/{total}] Обработка провайдера: {provider_name}")
        
        # Переменные для перехвата
        popup_page = None
        provider_frame = None
        entry_url = ""
        final_url = ""
        detected_in = "button_text"
        is_iframe = False
        network_requests = []
        modal_element = None  # Инициализируем в начале
        use_before_confirm_screenshot = False  # Инициализируем в начале
        provider_domain_after_confirm = None  # Инициализируем в начале
        screenshot_path_before = None  # Инициализируем в начале
        
        # Обработчики событий
        async def on_popup(popup: Page):
            nonlocal popup_page
            popup_page = popup
            print(f"  → Открыт popup: {popup.url}")
        
        # Фильтр трекинг доменов
        TRACKING = ("google.", "gstatic.", "doubleclick.", "googlesyndication.",
                    "googletagmanager.", "google-analytics.", "facebook.", "fbcdn.",
                    "hotjar.", "yandex.", "tiktok.", "suphelper.")
        
        def is_noise(host: str) -> bool:
            h = host.lower()
            return any(x in h for x in TRACKING)
        
        async def on_request(request):
            url = request.url
            if url.startswith(("http://", "https://")):
                from urllib.parse import urlparse
                host = urlparse(url).netloc.lower()
                if not host:
                    return
                # Пропускаем домен мерчанта
                merchant_domain_check = self.get_domain(page.url)
                if host == merchant_domain_check or "1xbet.com" in host or "dafabet.com" in host:
                    return
                # Пропускаем трекинг домены
                if is_noise(host):
                    return
                # Пропускаем suphelper
                if "suphelper" in host:
                    return
                # Проверяем, является ли это платёжным endpoint
                url_lower = url.lower()
                payment_keywords = ["deposit", "pay", "upi", "checkout", "payment", "gateway", "merchant"]
                if any(kw in url_lower for kw in payment_keywords) or self.is_external_provider_domain(host, merchant_domain_check):
                    network_requests.append(url)
                    print(f"  → Network request провайдера: {url[:100]}")
        
        async def on_framenavigated(frame: Frame):
            nonlocal provider_frame, entry_url, is_iframe
            if frame != page.main_frame and frame.url.startswith(("http://", "https://")):
                frame_domain = self.get_domain(frame.url)
                merchant_domain_check = self.get_domain(page.url)
                # Пропускаем suphelper и проверяем, является ли это внешним доменом провайдера
                if frame_domain and "suphelper" not in frame_domain.lower() and self.is_external_provider_domain(frame_domain, merchant_domain_check):
                    provider_frame = frame
                    entry_url = frame.url
                    is_iframe = True
                    detected_in = "iframe src"
                    print(f"  → Найден iframe провайдера: {frame.url}")
        
        # Подписываемся на события
        page.once("popup", on_popup)
        page.on("request", on_request)
        page.on("framenavigated", on_framenavigated)
        
        deposit_frame = None  # Будет установлен в attempt loop
        
        # Attempt loop (2 попытки) для клика провайдера
        for attempt in range(2):
            try:
                if attempt > 0:
                    print(f"  🔁 Retry попытка {attempt + 1}/2")
                
                # Каждый attempt — чистый контекст
                deposit_frame = await self.prepare_cashier_context(page, cashier_url, config)
                if not deposit_frame:
                    if attempt == 0:
                        print("  ⚠️  Не удалось восстановить deposit iframe, пробуем ещё раз")
                        continue
                    print("  ⚠️  Не удалось восстановить deposit iframe после 2 попыток, пропускаем провайдера")
                    page.remove_listener("request", on_request)
                    page.remove_listener("framenavigated", on_framenavigated)
                    return None
                
                # Пересоздаём locator на базе provider_key
                locator = await self.build_provider_locator(deposit_frame, provider_key)
                
                # Скроллим к элементу (используем новый locator)
                try:
                    await locator.scroll_into_view_if_needed(timeout=5000)
                    await page.wait_for_timeout(1000)  # Пауза на отрисовку
                except PWError as e:
                    if "Frame was detached" in str(e) and attempt == 0:
                        print("  ⚠️  Frame detached при скролле, повторяем попытку")
                        continue
                    raise
                
                # Проверяем видимость перед кликом
                is_visible = await locator.is_visible(timeout=2000)
                box = await locator.bounding_box()
                
                print(f"  → Диагностика перед кликом: visible={is_visible}, box={box}")
                
                if not is_visible or not box:
                    print(f"  ⚠️  Элемент не виден или не найден, пробуем force click")
                    try:
                        await locator.click(force=True, timeout=5000)
                        print(f"  ✓ Force click выполнен")
                    except PWError as e:
                        if "Frame was detached" in str(e) and attempt == 0:
                            print("  ⚠️  Frame detached при клике, повторяем попытку")
                            continue
                        raise
                else:
                    # Обычный клик с force=True
                    try:
                        await locator.click(force=True, timeout=8000)
                        print(f"  ✓ Клик по провайдеру: {provider_name}")
                    except PWError as e:
                        if "Frame was detached" in str(e) and attempt == 0:
                            print("  ⚠️  Frame detached при клике, повторяем попытку")
                            continue
                        raise
                
                # Успешный клик - выходим из attempt loop
                break
                
            except PWError as e:
                if "Frame was detached" in str(e) and attempt == 0:
                    print("  ⚠️  Frame detached, повторяем попытку")
                    continue
                # Другие ошибки или вторая попытка не удалась
                print(f"  ❌ Ошибка при обработке провайдера (попытка {attempt + 1}/2): {e}")
                if attempt == 1:
                    page.remove_listener("request", on_request)
                    page.remove_listener("framenavigated", on_framenavigated)
                    return None
            except Exception as e:
                print(f"  ❌ Неожиданная ошибка при обработке провайдера (попытка {attempt + 1}/2): {e}")
                if attempt == 1:
                    page.remove_listener("request", on_request)
                    page.remove_listener("framenavigated", on_framenavigated)
                    return None
        
        # После успешного клика продолжаем с остальной логикой
        try:
            
            # Снимаем снимок iframe до клика
            frames_before = self.frame_urls(page)
            print(f"  → Фреймы до клика: {len(frames_before)}")
            
            # deposit_frame уже восстановлен через prepare_cashier_context
            
            # Ждём появления popup, модального окна, iframe или навигации
            await page.wait_for_timeout(1500)
            
            # Детектор изменений: A) UI изменения внутри deposit iframe
            ui_change_detected = False
            ui_selector = None
            if deposit_frame:
                try:
                    ui_selector = await self.wait_payment_ui(deposit_frame, timeout=8000)
                    if ui_selector:
                        ui_change_detected = True
                        print(f"  ✓ После клика появился UI: {ui_selector}")
                except:
                    pass
            
            # Если UI не найден, продолжаем (возможен авто-переход)
            if not ui_change_detected:
                print("  ⚠️  UI изменения не обнаружены после клика, продолжаем (возможен авто-переход)")
            
            # 1) КРИТИЧНО: Устанавливаем валидный amount (>= 300 INR) СРАЗУ после обнаружения UI
            amount_input = None
            if deposit_frame and ui_change_detected:
                default_amount = config.get("default_amount", "300")
                amount_input = await self.ensure_valid_amount(deposit_frame, default_amount=default_amount)
                if not amount_input:
                    print("  ⚠️  Amount не установлен - редирект может не произойти")
            
            # 2) Заполняем остальные поля (если есть) - UPI, Phone, Aadhaar, FullName
            if deposit_frame:
                filled_fields, did_click_confirm = await self.fill_popup_and_confirm(deposit_frame, config)
            else:
                filled_fields = []
                did_click_confirm = False
            
            # 3) КРИТИЧНО: Мульти-шаговый обработчик модалки (кликает action-кнопку до 3 раз)
            merchant_host = self.get_domain(cashier_url)
            provider_domain_after_confirm, provider_url_after_confirm, detected_in_after_confirm = None, None, None
            
            if deposit_frame:
                # Мульти-шаговый обработчик: обрабатывает внутренний 2-шаговый сценарий или внешний редирект
                handle_result = await self.handle_modal_steps(
                    page, deposit_frame, cashier_url, config, network_requests=network_requests
                )
                provider_domain_after_confirm, provider_url_after_confirm, detected_in_after_confirm, payment_details = handle_result if len(handle_result) == 4 else (*handle_result, None)
            
            # Если внешний домен не найден после всех шагов - ждём ещё немного
            if not provider_domain_after_confirm:
                provider_domain_after_confirm, provider_url_after_confirm, detected_in_after_confirm = await self.wait_external_after_confirm(
                    page, merchant_host, timeout_ms=6000, network_requests=network_requests
                )
            
            # Не пропускаем, если внешний домен не найден - сохраняем как internal_or_delayed
            if not provider_domain_after_confirm:
                print("  ⚠️  Внешний домен провайдера не обнаружен после confirm - сохраняем как internal_or_delayed")
                provider_domain_after_confirm = "internal_or_delayed"
                provider_url_after_confirm = None
                detected_in_after_confirm = "internal_or_delayed"
            
            # Провайдером считается только домен, который появился после confirm
            final_url = None
            entry_url = None
            
            # Ищем полный URL провайдера в iframe
            for fr in page.frames:
                fr_domain = self.get_domain(fr.url)
                if fr_domain == provider_domain_after_confirm:
                    final_url = fr.url
                    entry_url = fr.url
                    provider_frame = fr
                    is_iframe = True
                    detected_in = detected_in_after_confirm
                    print(f"  ✓ Найден провайдер после confirm (iframe): {provider_domain_after_confirm} ({detected_in_after_confirm})")
                    break
            
            # Если не нашли в iframe, проверяем navigation
            if not final_url:
                current_url = page.url
                current_domain = self.get_domain(current_url)
                if current_domain == provider_domain_after_confirm:
                    final_url = current_url
                    entry_url = current_url
                    detected_in = "navigation_after_confirm"
                    print(f"  ✓ Найден провайдер после confirm (navigation): {provider_domain_after_confirm}")
            
            # Если всё ещё не нашли, используем первый network request с нужным доменом
            if not final_url:
                for req_url in network_requests:
                    req_domain = self.get_domain(req_url)
                    if req_domain == provider_domain_after_confirm:
                        final_url = req_url
                        entry_url = req_url
                        detected_in = "network_after_confirm"
                        print(f"  ✓ Найден провайдер после confirm (network): {provider_domain_after_confirm}")
                        break
            
            # Если полный URL не найден, используем текущий URL страницы или deposit_frame
            if not final_url:
                if deposit_frame:
                    final_url = deposit_frame.url
                    entry_url = deposit_frame.url
                else:
                    final_url = page.url
                    entry_url = page.url
                detected_in = "internal_or_delayed"
                print(f"  → Полный URL не найден, используем текущий URL: {final_url}")
            
            # Домен провайдера
            provider_domain = provider_domain_after_confirm
            merchant_domain_check = self.get_domain(cashier_url)
            
            # Проверяем, что это действительно внешний домен провайдера (но не пропускаем, если internal)
            is_external = provider_domain != "internal_or_delayed" and self.is_external_provider_domain(provider_domain, merchant_domain_check)
            
            if provider_domain == "internal_or_delayed":
                print(f"  → Провайдер сохранён как internal_or_delayed (внешний домен может появиться позже)")
            elif is_external:
                print(f"  ✓ Провайдер определён: {provider_domain} (внешний домен после confirm)")
            else:
                print(f"  → Провайдер определён: {provider_domain} (не внешний, но сохраняем)")
            
            # Проверяем на дубликаты (НЕ дедуплицируем по internal_or_delayed)
            if provider_domain != "internal_or_delayed" and self.storage.provider_exists(merchant_domain, provider_domain):
                print(f"  ⏭️  Провайдер {provider_domain} уже в БД, пропускаем")
                return None
            
            # Небольшая задержка перед скриншотом (чтобы форма успела обновиться после заполнения)
            await page.wait_for_timeout(1000)
            
            # Делаем скриншот страницы после confirm (страницы провайдера)
            screenshot_filename = f"{merchant_domain}_{provider_domain}_{int(time.time())}.png"
            screenshot_path = os.path.join(self.screenshot_dir, screenshot_filename)
            
            try:
                # Приоритет скриншота: iframe провайдера > popup > страница после редиректа
                if provider_frame:
                    # Скриншот iframe провайдера (страница после confirm)
                    await page.wait_for_timeout(2000)  # Ждём загрузки iframe
                    await provider_frame.locator("body").screenshot(path=screenshot_path, timeout=10000)
                    print(f"  ✓ Скриншот iframe провайдера (после confirm) сохранён")
                elif popup_page:
                    # Скриншот popup провайдера (страница после confirm)
                    await popup_page.wait_for_load_state("domcontentloaded", timeout=10000)
                    await page.wait_for_timeout(2000)
                    await popup_page.screenshot(path=screenshot_path, full_page=True, timeout=10000)
                    print(f"  ✓ Скриншот popup провайдера (после confirm) сохранён")
                else:
                    # Скриншот страницы после редиректа на домен провайдера
                    current_url = page.url
                    current_domain = self.get_domain(current_url)
                    cashier_domain = self.get_domain(cashier_url)
                    
                    if current_domain and current_domain != cashier_domain and is_external:
                        # Редирект на домен провайдера - делаем скриншот страницы провайдера
                        print(f"  → Редирект на домен провайдера обнаружен, делаем скриншот страницы")
                        await page.wait_for_load_state("domcontentloaded", timeout=10000)
                        await page.wait_for_timeout(2000)  # Дополнительная пауза для загрузки
                        await page.screenshot(path=screenshot_path, full_page=True, timeout=10000)
                        print(f"  ✓ Скриншот страницы провайдера (после confirm) сохранён")
                    else:
                        # Если редирект не произошёл, делаем скриншот текущей страницы
                        await page.wait_for_load_state("domcontentloaded", timeout=10000)
                        await page.wait_for_timeout(2000)
                        await page.screenshot(path=screenshot_path, full_page=True, timeout=10000)
                        print(f"  ✓ Скриншот текущей страницы (после confirm) сохранён")
                
                print(f"  ✓ Скриншот сохранён: {screenshot_path}")
            except Exception as e:
                print(f"  ⚠️  Ошибка при создании скриншота: {e}")
                screenshot_path = ""
            
            # Определяем payment method
            payment_method = None
            provider_name_lower = provider_name.lower()
            if any(x in provider_name_lower for x in ["upi", "phonepe", "paytm", "gpay"]):
                payment_method = "UPI"
            elif any(x in provider_name_lower for x in ["card", "visa", "mastercard"]):
                payment_method = "Card"
            elif any(x in provider_name_lower for x in ["netbanking", "bank"]):
                payment_method = "NetBanking"
            elif any(x in provider_name_lower for x in ["wallet", "skrill", "neteller"]):
                payment_method = "Wallet"
            
            result = {
                "merchant_domain": merchant_domain,
                "provider_domain": provider_domain,
                "provider_name": provider_name,
                "provider_entry_url": entry_url,
                "final_url": final_url,
                "cashier_url": cashier_url,
                "screenshot_path": screenshot_path,
                "detected_in": detected_in,
                "payment_method": payment_method,
                "is_iframe": is_iframe,
                "button_text": button_text,
            }
            
            return result
            
        except Exception as e:
            print(f"  ❌ Ошибка при обработке провайдера: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Закрываем модальное окно если открыто
            if modal_element:
                try:
                    # Ищем кнопку закрытия модального окна
                    close_buttons = [
                        "button[aria-label*='close']",
                        "button[class*='close']",
                        ".close",
                        "[class*='close-button']",
                        "button:has-text('×')",
                        "button:has-text('✕')",
                    ]
                    for close_selector in close_buttons:
                        try:
                            close_btn = page.locator(close_selector).first
                            if await close_btn.is_visible(timeout=1000):
                                await close_btn.click()
                                await page.wait_for_timeout(1000)
                                print(f"  ✓ Модальное окно закрыто")
                                break
                        except:
                            continue
                    # Если кнопка закрытия не найдена, пробуем ESC
                    try:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(1000)
                    except:
                        pass
                except Exception as e:
                    print(f"  ⚠️  Ошибка при закрытии модального окна: {e}")
            
            # Закрываем popup если открыт
            if popup_page:
                try:
                    await popup_page.close()
                    print(f"  ✓ Popup закрыт")
                except:
                    pass
            
            # Возвращаемся на страницу депозита после обработки провайдера
            try:
                current_url = page.url
                current_domain = self.get_domain(current_url)
                cashier_domain = self.get_domain(cashier_url)
                
                # Если мы на другом домене или на другой странице, возвращаемся на кэшир
                if current_domain != cashier_domain or (current_url != cashier_url and not modal_element):
                    print(f"  → Возврат на страницу кэшира: {cashier_url}")
                    await page.goto(cashier_url, wait_until="domcontentloaded", timeout=10000)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        await page.wait_for_load_state("load", timeout=5000)
                    await page.wait_for_timeout(3000)  # Дополнительная пауза для загрузки
                    
                    # Снова нажимаем на "Make Deposit" если нужно
                    try:
                        await self.click_make_deposit(page, config)
                        await page.wait_for_timeout(2000)
                    except:
                        pass
                    
                    print(f"  ✓ Возврат на кэшир выполнен: {page.url}")
            except Exception as e:
                print(f"  ⚠️  Ошибка при возврате на кэшир: {e}")
    
    async def parse_providers(self, merchant_id: str, merchant_url: str, config: dict) -> List[Dict]:
        """Основной метод парсинга провайдеров"""
        results = []
        merchant_domain = self.get_domain(merchant_url)
        account_type = config.get("account_type") or "player"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            # Пробуем загрузить сохранённый storageState
            storage_state_path = self.get_storage_state_path(merchant_id)
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            if os.path.exists(storage_state_path):
                try:
                    context_options["storage_state"] = storage_state_path
                    print(f"✓ Загружен сохранённый storageState: {storage_state_path}")
                except Exception as e:
                    print(f"⚠️  Не удалось загрузить storageState: {e}")
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            try:
                # Шаг 1: Логин
                print("\n=== Шаг 1: Вход в систему ===")
                current_url = page.url
                if not current_url or current_url == "about:blank":
                    try:
                        await page.goto(merchant_url, wait_until="domcontentloaded", timeout=60000)
                        try:
                            await page.wait_for_load_state("load", timeout=15000)
                        except:
                            await page.wait_for_timeout(3000)
                    except Exception as goto_error:
                        print(f"⚠️  Ошибка при загрузке страницы: {goto_error}")
                        print(f"  → Пробую загрузить страницу с networkidle...")
                        try:
                            await page.goto(merchant_url, wait_until="networkidle", timeout=90000)
                        except:
                            print(f"  → Пробую загрузить страницу без wait_until...")
                            try:
                                await page.goto(merchant_url, timeout=60000)
                                await page.wait_for_timeout(5000)
                            except:
                                print(f"  ⚠️  Не удалось загрузить страницу, продолжаем с текущим URL: {page.url}")
                else:
                    print(f"  → Страница уже открыта: {current_url}")
                    await page.wait_for_timeout(2000)
                
                login_result = await self.login(page, merchant_id, config)
                
                # Обработка капчи - human-in-the-loop
                if login_result == "captcha" or not login_result:
                    # Проверяем, действительно ли есть капча или просто не удалось залогиниться
                    captcha_detected = await self.detect_captcha(page)
                    if captcha_detected or not login_result:
                        # Запускаем human-in-the-loop
                        manual_login_success = await self.wait_for_manual_login(page, merchant_id, context)
                        if manual_login_success:
                            # Сохраняем storageState после успешного логина
                            await context.storage_state(path=storage_state_path)
                            print(f"✓ StorageState сохранён: {storage_state_path}")
                
                # Если логин успешен, сохраняем storageState
                if login_result is True:
                    await context.storage_state(path=storage_state_path)
                    print(f"✓ StorageState сохранён: {storage_state_path}")
                
                await page.wait_for_timeout(3000)
                
                # Шаг 2: Переход на кэшир
                print("\n=== Шаг 2: Переход на страницу депозита ===")
                cashier_url = await self.navigate_to_cashier(page, config)
                await page.wait_for_timeout(3000)
                
                # Шаг 3: Поиск провайдеров в секции E-WALLETS
                print("\n=== Шаг 4: Поиск провайдеров в секции E-WALLETS ===")
                provider_elements = await self.find_ewallets_providers(page, config)
                print(f"Найдено провайдеров в E-WALLETS: {len(provider_elements)}")
                
                # Фильтруем только "UPI Fast" и "Paytm"
                target_providers = ["upi fast", "paytm"]
                filtered_providers = []
                for provider in provider_elements:
                    provider_name = provider.get("name", "").lower()
                    button_text = provider.get("button_text", "").lower()
                    if any(target in provider_name or target in button_text for target in target_providers):
                        filtered_providers.append(provider)
                
                if filtered_providers:
                    provider_elements = filtered_providers
                    print(f"✓ Отфильтровано провайдеров (только UPI Fast и Paytm): {len(provider_elements)}")
                
                # Если не нашли в E-WALLETS, ищем по всей странице
                if not provider_elements:
                    print("  → Провайдеры не найдены в E-WALLETS, ищем по всей странице...")
                    provider_elements = await self.find_all_providers(page, config)
                    # Фильтруем только "UPI Fast" и "Paytm"
                    filtered_providers = []
                    for provider in provider_elements:
                        provider_name = provider.get("name", "").lower()
                        button_text = provider.get("button_text", "").lower()
                        if any(target in provider_name or target in button_text for target in target_providers):
                            filtered_providers.append(provider)
                    if filtered_providers:
                        provider_elements = filtered_providers
                        print(f"Найдено провайдеров на странице (отфильтровано): {len(provider_elements)}")
                
                if not provider_elements:
                    print("⚠️  Провайдеры 'UPI Fast' и 'Paytm' не найдены")
                    # Делаем скриншот страницы для отладки
                    try:
                        debug_screenshot = os.path.join(self.screenshot_dir, f"debug_{int(time.time())}.png")
                        await page.screenshot(path=debug_screenshot, full_page=True)
                        print(f"  → Скриншот страницы сохранён для отладки: {debug_screenshot}")
                    except:
                        pass
                    return results
                
                # Шаг 5: Обработка каждого провайдера
                print(f"\n=== Шаг 5: Обработка {len(provider_elements)} провайдеров ===")
                
                for idx, provider_info in enumerate(provider_elements):
                    result = await self.process_provider_button(
                        page, provider_info, merchant_domain, cashier_url, idx + 1, len(provider_elements), config
                    )
                    
                    if result:
                        # Сохраняем в БД
                        saved = self.storage.save_provider(
                            merchant=merchant_id,
                            merchant_domain=merchant_domain,
                            provider_domain=result["provider_domain"],
                            account_type=account_type,
                            provider_name=result["provider_name"],
                            provider_entry_url=result["provider_entry_url"],
                            final_url=result["final_url"],
                            cashier_url=result["cashier_url"],
                            screenshot_path=result["screenshot_path"],
                            detected_in=result["detected_in"],
                            payment_method=result["payment_method"],
                            is_iframe=result["is_iframe"],
                        )
                        
                        if saved:
                            print(f"  ✓ Провайдер {result['provider_domain']} сохранён в БД")
                            results.append(result)
                    
                            # Экспортируем в Google Sheets после каждого провайдера
                            try:
                                self.storage.export_to_xlsx()
                                print(f"  ✓ Данные экспортированы в Google Sheets")
                            except Exception as e:
                                print(f"  ⚠️  Ошибка при экспорте в Google Sheets: {e}")
                    
                    # Пауза между провайдерами
                    await page.wait_for_timeout(2000)
                    
                    # После обработки каждого провайдера (кроме последнего) возвращаемся на кэшир
                    if idx < len(provider_elements) - 1:  # Не последний провайдер
                        print(f"\n  → Возврат на кэшир перед обработкой следующего провайдера...")
                        try:
                            await page.goto(cashier_url, wait_until="domcontentloaded", timeout=10000)
                            try:
                                await page.wait_for_load_state("networkidle", timeout=10000)
                            except:
                                await page.wait_for_load_state("load", timeout=5000)
                            await page.wait_for_timeout(3000)
                            
                            # Снова нажимаем на "Make Deposit" если нужно
                            try:
                                await self.click_make_deposit(page, config)
                                await page.wait_for_timeout(2000)
                            except:
                                pass
                            
                            print(f"  ✓ Возврат на кэшир выполнен: {page.url}\n")
                        except Exception as e:
                            print(f"  ⚠️  Ошибка при возврате на кэшир: {e}\n")
                
            finally:
                await browser.close()
        
        return results
    
    async def parse_olymptrade(self, merchant_id: str, merchant_url: str, config: dict):
        """Полный end-to-end флоу для Olymptrade: Login → Payments → Deposit → Next → форма → Proceed → скриншот"""
        results = []
        merchant_domain = self.get_domain(merchant_url)
        account_type = config.get("account_type") or "trader"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            # Пробуем загрузить сохранённый storageState
            storage_state_path = self.get_storage_state_path(merchant_id)
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            if os.path.exists(storage_state_path):
                try:
                    context_options["storage_state"] = storage_state_path
                    print(f"✓ Загружен сохранённый storageState: {storage_state_path}")
                except Exception as e:
                    print(f"⚠️  Не удалось загрузить storageState: {e}")
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            try:
                # Шаг 1: Переход на платформу
                print("\n=== Шаг 1: Переход на платформу ===")
                await page.goto(merchant_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_load_state("load", timeout=15000)
                print(f"✓ Загружена страница: {page.url}")
                
                # Закрываем cookie banners / overlays (best-effort)
                try:
                    accept_btn = page.get_by_role("button", name=re.compile(r"accept|agree", re.I)).first
                    if await accept_btn.is_visible(timeout=3000):
                        await accept_btn.click()
                        print("✓ Закрыт cookie banner")
                        await page.wait_for_timeout(1000)
                except Exception:
                    pass
                
                # Стандартизированная проверка "уже залогинены"
                current_url = page.url
                on_login_page = "/login" in current_url
                
                # Проверяем наличие Payments (признак залогиненности)
                has_payments = False
                try:
                    payments_check = page.locator("text=/Payments|Платеж/i").first
                    has_payments = await payments_check.is_visible(timeout=2000)
                except:
                    pass
                
                # Если не на /login и есть Payments - уже залогинены
                if not on_login_page and has_payments:
                    print("  → Уже залогинены (storageState валиден, Payments виден)")
                    # Сохраняем/обновляем storageState
                    try:
                        await context.storage_state(path=storage_state_path)
                        print(f"✓ Обновлён storageState: {storage_state_path}")
                    except Exception as e:
                        print(f"⚠️  Ошибка при сохранении storageState: {e}")
                    # Продолжаем deposit flow (не возвращаемся)
                elif on_login_page:
                    print("  → Обнаружен редирект на /login, требуется логин")
                else:
                    # Если не на /login, но нет Payments - насильно открываем /login
                    print("  → Payments не найден, открываем /login принудительно")
                    login_url = "https://olymptrade.com/login?redirect_url=https%3A%2F%2Folymptrade.com%2Fplatform"
                    await page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_load_state("load", timeout=15000)
                
                # Шаг 2: Логин (улучшенная версия с поддержкой iframe)
                print("\n=== Шаг 2: Вход в систему ===")
                
                # Вспомогательная функция для поиска контекста логина (page или frame)
                async def get_login_context(page):
                    """Находит контекст (page или frame), где есть поля логина"""
                    # Попытка 1: на странице через get_by_label (более надёжно)
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=10000)
                        # Проверяем наличие поля email через label
                        email_field = page.get_by_label(re.compile(r"почта|email", re.I)).first
                        if await email_field.count() > 0:
                            print(f"  → Логин-форма найдена на странице (через label)")
                            return page
                        # Fallback: проверяем input
                        input_count = await page.locator("input[type='email'], input[type='text'], input[type='password']").count()
                        if input_count > 0:
                            print(f"  → Логин-форма найдена на странице (input полей: {input_count})")
                            return page
                    except:
                        pass
                    
                    # Попытка 2: в iframe'ах
                    try:
                        frames = page.frames
                        print(f"  → Проверка iframe'ов (найдено: {len(frames)})")
                        for frame in frames:
                            try:
                                await frame.wait_for_load_state("domcontentloaded", timeout=5000)
                                # Проверяем через label
                                email_field = frame.get_by_label(re.compile(r"почта|email", re.I)).first
                                if await email_field.count() > 0:
                                    print(f"  → Логин-форма найдена в iframe: {frame.url} (через label)")
                                    return frame
                                # Fallback: проверяем input
                                input_count = await frame.locator("input[type='email'], input[type='text'], input[type='password']").count()
                                if input_count > 0:
                                    print(f"  → Логин-форма найдена в iframe: {frame.url} (input полей: {input_count})")
                                    return frame
                            except:
                                continue
                    except:
                        pass
                    
                    return None
                
                # Флаг для ручного логина
                manual_login_performed = False
                
                # Находим контекст логина
                login_ctx = await get_login_context(page)
                if not login_ctx:
                    # Если не нашли - насильно открываем /login
                    print("  → Логин-форма не найдена, открываем /login принудительно")
                    login_url = "https://olymptrade.com/login?redirect_url=https%3A%2F%2Folymptrade.com%2Fplatform"
                    await page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_load_state("load", timeout=15000)
                    await page.wait_for_timeout(3000)  # Дополнительное ожидание для загрузки формы
                    login_ctx = await get_login_context(page)
                    
                    # Если всё ещё не нашли - пробуем кликнуть на кнопку "LogIn" (форма может открываться по клику)
                    if not login_ctx:
                        print("  → Пробуем кликнуть на кнопку 'LogIn' для открытия формы...")
                        try:
                            login_btn = page.locator("button:has-text('LogIn'), button:has-text('Log in'), button:has-text('Login'), a:has-text('LogIn')").first
                            if await login_btn.is_visible(timeout=5000):
                                await login_btn.click()
                                await page.wait_for_timeout(2000)
                                login_ctx = await get_login_context(page)
                        except:
                            pass
                    
                    if not login_ctx:
                        # Если не нашли форму - используем human-in-the-loop
                        print("  ⚠️  Автоматический логин не удался, переходим к ручному логину...")
                        manual_login_success = await self.wait_for_manual_login(page, merchant_id, context)
                        if manual_login_success:
                            manual_login_performed = True
                            # Проверяем, что мы не на /login
                            if "/login" in page.url:
                                raise Exception("Ручной логин выполнен, но всё ещё на /login")
                            # Сохраняем storageState после успешного логина
                            await context.storage_state(path=storage_state_path)
                            print(f"✓ StorageState сохранён: {storage_state_path}")
                        else:
                            raise Exception("Ручной логин не выполнен")
                        # После успешного ручного логина НЕ выполняем автологин-шаги
                        login_ctx = None  # Уже залогинены, форма не нужна
                
                # Если login_ctx найден И НЕ был ручной логин - выполняем автоматический логин
                if login_ctx and not manual_login_performed:
                    # Принудительно переключаемся на вкладку "Вход"
                    print("  → Проверка и переключение на вкладку 'Вход'...")
                    try:
                        is_reg = await login_ctx.locator('button:has-text("Зарегистрироваться")').is_visible(timeout=3000)
                        if is_reg:
                            print("  → Обнаружена вкладка 'Регистрация', переключаемся на 'Вход'")
                            login_tab = login_ctx.locator("text=Вход").first
                            if await login_tab.is_visible(timeout=3000):
                                await login_tab.click()
                                print("✓ Переключено на вкладку 'Вход'")
                                await page.wait_for_timeout(1000)
                    except:
                        pass
                    
                    # Заполняем email и password в найденном контексте
                    try:
                        email_locator = login_ctx.get_by_label(re.compile(r"почта|email", re.I)).first
                        if await email_locator.count() == 0:
                            email_locator = login_ctx.locator("input[type='email']").first
                        await email_locator.fill(config["credentials"]["username"], timeout=20000)
                        print("✓ Заполнен email")
                        await page.wait_for_timeout(500)
                    except Exception as e:
                        print(f"⚠️  Ошибка при заполнении email: {e}")
                    
                    try:
                        password_locator = login_ctx.get_by_label(re.compile(r"пароль|password", re.I)).first
                        if await password_locator.count() == 0:
                            password_locator = login_ctx.locator("input[type='password']").first
                        await password_locator.fill(config["credentials"]["password"], timeout=20000)
                        print("✓ Заполнен password")
                        await page.wait_for_timeout(500)
                    except Exception as e:
                        print(f"⚠️  Ошибка при заполнении password: {e}")
                    
                    # Нажимаем кнопку "Войти" в найденном контексте
                    print("  → Поиск и нажатие кнопки 'Войти'...")
                    
                    login_btn_clicked = False
                    # Попытка 1: кнопка "Войти"
                    try:
                        login_btn = login_ctx.locator('button:has-text("Войти"), button[type="submit"]').first
                        if await login_btn.count() > 0:
                            await login_btn.scroll_into_view_if_needed()
                            if await login_btn.is_visible(timeout=5000):
                                await login_btn.click(timeout=15000)
                                print("✓ Нажата кнопка 'Войти'")
                                login_btn_clicked = True
                    except:
                        pass
                    
                    # Попытка 2: Enter на поле пароля
                    if not login_btn_clicked:
                        try:
                            password_field = login_ctx.locator("input[type='password']").first
                            if await password_field.count() > 0:
                                await password_field.press("Enter")
                                print("✓ Нажата кнопка входа (через Enter)")
                                login_btn_clicked = True
                        except:
                            pass
                    
                    # Диагностика сразу после клика
                    if login_btn_clicked:
                        await page.wait_for_timeout(1500)
                        try:
                            debug_after_click = os.path.join(self.screenshot_dir, f"debug_after_click_{int(time.time())}.png")
                            await page.screenshot(path=debug_after_click, full_page=True)
                            print(f"  ✓ Скриншот после клика: {debug_after_click}")
                        except Exception as e:
                            print(f"  ⚠️  Ошибка при создании скриншота: {e}")
                        
                        try:
                            cookies_count = len(await context.cookies())
                            print(f"  → Cookies после клика: {cookies_count}")
                            print(f"  → URL после клика: {page.url}")
                        except Exception as e:
                            print(f"  ⚠️  Ошибка при проверке cookies: {e}")
                    
                    # Если всё ещё не нашли - делаем диагностику
                    if not login_btn_clicked:
                        print("❌ Не удалось найти и нажать кнопку входа")
                        print("  → Диагностика: делаю скриншот и собираю информацию о кнопках...")
                        
                        # Скриншот для отладки
                        try:
                            debug_screenshot = os.path.join(self.screenshot_dir, f"debug_login_page_{int(time.time())}.png")
                            await page.screenshot(path=debug_screenshot, full_page=True)
                            print(f"  ✓ Скриншот сохранён: {debug_screenshot}")
                        except Exception as e:
                            print(f"  ⚠️  Ошибка при создании скриншота: {e}")
                        
                        # Собираем тексты всех кликабельных элементов
                        try:
                            buttons_locator = page.locator("button, [role='button'], a, div[onclick]")
                            buttons_count = await buttons_locator.count()
                            buttons_text = []
                            for i in range(min(buttons_count, 50)):
                                try:
                                    btn = buttons_locator.nth(i)
                                    text = await btn.inner_text()
                                    if text and text.strip():
                                        buttons_text.append(text.strip())
                                except:
                                    continue
                            print(f"  → Найдено кликабельных элементов с текстом: {len(buttons_text)}")
                            if buttons_text:
                                print(f"  → Примеры текстов: {', '.join(buttons_text[:10])}")
                        except Exception as e:
                            print(f"  ⚠️  Ошибка при сборе информации о кнопках: {e}")
                        
                        # Используем human-in-the-loop
                        print("  → Переходим к ручному логину...")
                        manual_login_success = await self.wait_for_manual_login(page, merchant_id, context)
                        if manual_login_success:
                            await context.storage_state(path=storage_state_path)
                            print(f"✓ StorageState сохранён: {storage_state_path}")
                        else:
                            return {"status": "ERROR", "error": "Login button not found and manual login failed", "providers": []}
                    
                    # Подтверждаем успешный логин через URL (не через navigation load)
                    print("  → Ожидание подтверждения логина...")
                    
                    # Быстрая проверка ошибок логина
                    try:
                        error_loc = page.get_by_text(re.compile(r"неверн|ошибк|invalid|wrong|incorrect|неправильн", re.I)).first
                        if await error_loc.count() > 0 and await error_loc.is_visible():
                            try:
                                error_text = await error_loc.inner_text()
                                print(f"  ❌ Обнаружена ошибка логина: {error_text}")
                            except:
                                print("  ❌ Обнаружена ошибка логина (текст не получен)")
                            # Скриншот при ошибке
                            try:
                                error_screenshot = os.path.join(self.screenshot_dir, f"debug_login_failed_{int(time.time())}.png")
                                await page.screenshot(path=error_screenshot, full_page=True)
                                print(f"  ✓ Скриншот ошибки сохранён: {error_screenshot}")
                            except:
                                pass
                            return {"status": "ERROR", "error": "Login failed", "providers": []}
                    except:
                        pass
                    
                    # Ждём, пока URL не будет содержать /login (до 45 секунд)
                    try:
                        await page.wait_for_url(lambda url: "/login" not in url, timeout=45000)
                        final_url = page.url
                        print(f"✓ Логин успешен - URL изменился: {final_url}")
                    except Exception as e:
                        print(f"⚠️  Не удалось подтвердить успешный логин через URL: {e}")
                        current_url = page.url
                        print(f"  Текущий URL: {current_url}")
                        if "/login" in current_url:
                            # Скриншот для диагностики
                            try:
                                debug_screenshot = os.path.join(self.screenshot_dir, f"debug_login_uncertain_{int(time.time())}.png")
                                await page.screenshot(path=debug_screenshot, full_page=True)
                                print(f"  ✓ Скриншот для диагностики: {debug_screenshot}")
                            except:
                                pass
                            return {"status": "ERROR", "error": "Login confirmation failed - still on /login", "providers": []}
                        else:
                            # Если URL изменился, но wait_for_url не сработал - считаем успехом
                            final_url = current_url
                            print(f"✓ Логин успешен (URL: {final_url})")
                    
                    # Сохраняем storage state после успешного логина
                    try:
                        await context.storage_state(path=storage_state_path)
                        print(f"✓ Сохранён storageState: {storage_state_path}")
                    except Exception as e:
                        print(f"⚠️  Ошибка при сохранении storageState: {e}")
                
                # Если был ручной логин - пропускаем автологин и сразу переходим к Payments
                if manual_login_performed:
                    print("  → Ручной логин выполнен, пропускаем автологин-шаги")
                
                # Продолжаем полный флоу: Payments → Deposit → Next → форма → Proceed
                # Ждём загрузки страницы после логина
                print("\n=== Шаг 3: Ожидание загрузки платформы ===")
                try:
                    await page.wait_for_load_state("load", timeout=15000)
                    await page.wait_for_timeout(2000)  # Дополнительное ожидание для загрузки UI
                except:
                    pass
                
                # Вспомогательная функция для поиска контекста кассы (page или frame)
                async def find_cashier_context(page):
                    """Находит контекст (page или frame), где находится касса/депозит"""
                    cashier_hints = [
                        re.compile(r"\bdeposit\b", re.I),
                        re.compile(r"\bpayments\b", re.I),
                        re.compile(r"\bnext\b", re.I),
                        re.compile(r"\bcontinue\b", re.I),
                        re.compile(r"далее", re.I),
                        re.compile(r"продолж", re.I),
                        re.compile(r"first\s*name", re.I),
                        re.compile(r"last\s*name", re.I),
                        re.compile(r"\bupi\b", re.I),
                        re.compile(r"пополн", re.I),
                    ]
                    
                    # Попытка 1: на странице
                    try:
                        for pat in cashier_hints:
                            try:
                                # Проверяем наличие текста в body
                                body_loc = page.locator("body")
                                count = await body_loc.filter(has_text=pat).count()
                                if count > 0:
                                    print(f"  → Касса найдена на странице (паттерн: {pat.pattern})")
                                    return page
                            except:
                                continue
                    except:
                        pass
                    
                    # Попытка 2: в iframe'ах
                    try:
                        frames = page.frames
                        print(f"  → Проверка iframe'ов для кассы (найдено: {len(frames)})")
                        for frame in frames:
                            try:
                                for pat in cashier_hints:
                                    try:
                                        body_loc = frame.locator("body")
                                        count = await body_loc.filter(has_text=pat).count()
                                        if count > 0:
                                            print(f"  → Касса найдена в iframe: {frame.url} (паттерн: {pat.pattern})")
                                            return frame
                                    except:
                                        continue
                            except:
                                continue
                    except:
                        pass
                    
                    return None
                
                # Вспомогательная функция для клика в page или frames
                async def click_in_any_context(page, name_patterns, step_name, timeout=30000):
                    """Клик в page или в любом frame"""
                    # Попытка 1: на странице через role
                    for pattern in name_patterns:
                        try:
                            btn = page.get_by_role("button", name=pattern).first
                            if await btn.count() > 0:
                                await btn.scroll_into_view_if_needed()
                                if await btn.is_visible(timeout=5000):
                                    await btn.click(timeout=timeout)
                                    print(f"✓ {step_name} clicked (через role на page)")
                                    return True
                        except:
                            continue
                    
                    # Попытка 2: на странице через text (более точный поиск)
                    for pattern in name_patterns:
                        try:
                            # Сначала пробуем через filter(has_text) - более надёжно
                            try:
                                pattern_str = pattern.pattern if hasattr(pattern, 'pattern') else str(pattern)
                                # Упрощаем паттерн для has_text (убираем якоря и флаги)
                                pattern_str = pattern_str.replace('^', '').replace('$', '').replace('(?i)', '').replace('(?-i)', '')
                                loc = page.locator("button, [role='button'], a, div, span").filter(has_text=re.compile(pattern_str, re.I)).first
                                if await loc.count() > 0:
                                    await loc.scroll_into_view_if_needed()
                                    if await loc.is_visible(timeout=5000):
                                        await loc.click(timeout=timeout)
                                        print(f"✓ {step_name} clicked (через filter has_text на page)")
                                        return True
                            except:
                                pass
                            
                            # Fallback: итерация по элементам
                            locs = page.locator("button, [role='button'], a, div, span")
                            count = await locs.count()
                            for i in range(min(count, 100)):
                                try:
                                    elem = locs.nth(i)
                                    text = await elem.inner_text()
                                    if text and re.search(pattern, text, re.I):
                                        await elem.scroll_into_view_if_needed()
                                        # Пробуем кликнуть даже если не видим (может быть перекрыт)
                                        try:
                                            # Сначала обычный клик
                                            if await elem.is_visible(timeout=2000):
                                                is_enabled = await elem.evaluate("el => !el.disabled && el.getAttribute('aria-disabled') !== 'true'")
                                                if is_enabled:
                                                    await elem.click(timeout=timeout)
                                                    print(f"✓ {step_name} clicked (через text на page)")
                                                    return True
                                            # Если не видим, пробуем force click
                                            await elem.click(timeout=timeout, force=True)
                                            print(f"✓ {step_name} clicked (через text на page, force)")
                                            return True
                                        except Exception as e:
                                            # Если клик не сработал, пробуем через координаты
                                            try:
                                                box = await elem.bounding_box()
                                                if box:
                                                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                                    print(f"✓ {step_name} clicked (через координаты на page)")
                                                    return True
                                            except:
                                                pass
                                except:
                                    continue
                        except:
                            continue
                    
                    # Попытка 3: в frames
                    frames = page.frames
                    for frame in frames:
                        for pattern in name_patterns:
                            # Через role в frame
                            try:
                                btn = frame.get_by_role("button", name=pattern).first
                                if await btn.count() > 0:
                                    await btn.scroll_into_view_if_needed()
                                    if await btn.is_visible(timeout=5000):
                                        await btn.click(timeout=timeout)
                                        print(f"✓ {step_name} clicked (через role в frame)")
                                        return True
                            except:
                                pass
                            
                            # Через text в frame (более точный поиск)
                            try:
                                # Сначала пробуем через filter(has_text)
                                try:
                                    pattern_str = pattern.pattern if hasattr(pattern, 'pattern') else str(pattern)
                                    pattern_str = pattern_str.replace('^', '').replace('$', '').replace('(?i)', '').replace('(?-i)', '')
                                    loc = frame.locator("button, [role='button'], a, div, span").filter(has_text=re.compile(pattern_str, re.I)).first
                                    if await loc.count() > 0:
                                        await loc.scroll_into_view_if_needed()
                                        if await loc.is_visible(timeout=5000):
                                            await loc.click(timeout=timeout)
                                            print(f"✓ {step_name} clicked (через filter has_text в frame)")
                                            return True
                                except:
                                    pass
                                
                                # Fallback: итерация по элементам
                                locs = frame.locator("button, [role='button'], a, div, span")
                                count = await locs.count()
                                for i in range(min(count, 100)):
                                    try:
                                        elem = locs.nth(i)
                                        text = await elem.inner_text()
                                        if text and re.search(pattern, text, re.I):
                                            await elem.scroll_into_view_if_needed()
                                        # Пробуем кликнуть даже если не видим (может быть перекрыт)
                                        try:
                                            # Сначала обычный клик
                                            if await elem.is_visible(timeout=2000):
                                                is_enabled = await elem.evaluate("el => !el.disabled && el.getAttribute('aria-disabled') !== 'true'")
                                                if is_enabled:
                                                    await elem.click(timeout=timeout)
                                                    print(f"✓ {step_name} clicked (через text в frame)")
                                                    return True
                                            # Если не видим, пробуем force click
                                            await elem.click(timeout=timeout, force=True)
                                            print(f"✓ {step_name} clicked (через text в frame, force)")
                                            return True
                                        except Exception as e:
                                            # Если клик не сработал, пробуем через координаты
                                            try:
                                                box = await elem.bounding_box()
                                                if box:
                                                    await frame.evaluate(f"document.elementFromPoint({box['x'] + box['width']/2}, {box['y'] + box['height']/2})?.click()")
                                                    print(f"✓ {step_name} clicked (через координаты в frame)")
                                                    return True
                                            except:
                                                pass
                                    except:
                                        continue
                            except:
                                continue
                    
                    # Диагностика: собираем все кликабельные тексты
                    try:
                        debug_screenshot = os.path.join(self.screenshot_dir, f"debug_{step_name.lower().replace(' ', '_')}_{int(time.time())}.png")
                        await page.screenshot(path=debug_screenshot, full_page=True)
                        print(f"  → Скриншот для диагностики: {debug_screenshot}")
                    except:
                        pass
                    
                    try:
                        clickable_texts = []
                        clickable_locator = page.locator("button, [role='button'], a")
                        count = await clickable_locator.count()
                        for i in range(min(count, 50)):
                            try:
                                elem = clickable_locator.nth(i)
                                text = await elem.inner_text()
                                if text and text.strip():
                                    clickable_texts.append(text.strip())
                            except:
                                continue
                        if clickable_texts:
                            print(f"  → Найдено кликабельных элементов: {len(clickable_texts)}")
                            print(f"  → Примеры: {', '.join(clickable_texts[:10])}")
                    except:
                        pass
                    
                    return False
                
                # Шаг 4: Нажатие на кнопку "Payments" (в page или frames)
                print("\n=== Шаг 4: Нажатие на кнопку 'Payments' ===")
                # Даём больше времени для загрузки UI после логина
                await page.wait_for_timeout(5000)
                
                # Ждём загрузки страницы
                try:
                    await page.wait_for_load_state("load", timeout=15000)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    pass
                
                # Дополнительное ожидание для загрузки UI
                await page.wait_for_timeout(2000)
                
                payments_clicked = await click_in_any_context(
                    page,
                    [re.compile(r"payments", re.I), re.compile(r"плат[её]жи", re.I), re.compile(r"платеж", re.I), re.compile(r"payment", re.I)],
                    "Payments",
                    30000
                )
                
                if not payments_clicked:
                    # Диагностика: скриншот и информация
                    try:
                        debug_screenshot = os.path.join(self.screenshot_dir, f"debug_payments_not_found_{int(time.time())}.png")
                        await page.screenshot(path=debug_screenshot, full_page=True)
                        print(f"  → Скриншот для диагностики: {debug_screenshot}")
                        print(f"  → Текущий URL: {page.url}")
                        print(f"  → Количество iframe'ов: {len(page.frames)}")
                        
                        # Собираем все кликабельные тексты для диагностики (page)
                        try:
                            clickable_texts = []
                            clickable_locator = page.locator("button, [role='button'], a, div, span")
                            count = await clickable_locator.count()
                            for i in range(min(count, 100)):
                                try:
                                    elem = clickable_locator.nth(i)
                                    text = await elem.inner_text()
                                    if text and text.strip() and len(text.strip()) < 50:
                                        clickable_texts.append(text.strip())
                                except:
                                    continue
                            if clickable_texts:
                                print(f"  → Найдено кликабельных элементов на page: {len(clickable_texts)}")
                                print(f"  → Примеры текстов (page): {', '.join(clickable_texts[:30])}")
                        except:
                            pass
                        
                        # Собираем все кликабельные тексты для диагностики (frames)
                        try:
                            for fr_idx, fr in enumerate(page.frames):
                                try:
                                    clickable_texts_frame = []
                                    clickable_locator_frame = fr.locator("button, [role='button'], a, div, span")
                                    count_frame = await clickable_locator_frame.count()
                                    for i in range(min(count_frame, 100)):
                                        try:
                                            elem = clickable_locator_frame.nth(i)
                                            text = await elem.inner_text()
                                            if text and text.strip() and len(text.strip()) < 50:
                                                clickable_texts_frame.append(text.strip())
                                        except:
                                            continue
                                    if clickable_texts_frame:
                                        print(f"  → Найдено кликабельных элементов в frame {fr_idx}: {len(clickable_texts_frame)}")
                                        print(f"  → Примеры текстов (frame {fr_idx}): {', '.join(clickable_texts_frame[:30])}")
                                except:
                                    pass
                        except:
                            pass
                    except:
                        pass
                    raise Exception("Не найдена кнопка/пункт 'Payments'")
                
                await page.wait_for_timeout(800)  # Ждём открытия панели
                
                # Шаг 5: Нажатие на кнопку "Deposit" (в page или frames)
                print("\n=== Шаг 5: Нажатие на кнопку 'Deposit' ===")
                deposit_clicked = await click_in_any_context(
                    page,
                    [re.compile(r"deposit", re.I), re.compile(r"пополн", re.I), re.compile(r"внести", re.I)],
                    "Deposit",
                    30000
                )
                
                if not deposit_clicked:
                    raise Exception("Не найдена кнопка 'Deposit'")
                
                # Увеличиваем время ожидания после Deposit - панель может открываться с задержкой
                print("  → Ожидание открытия панели депозита...")
                await page.wait_for_timeout(3000)
                
                # Проверяем, появились ли элементы депозита (Amount, Payment method и т.д.)
                deposit_panel_visible = False
                for attempt in range(15):  # Ждём до 7.5 секунд
                    try:
                        # Ищем признаки панели депозита
                        amount_loc = page.locator("text=/amount|сумма/i").first
                        if await amount_loc.count() > 0 and await amount_loc.is_visible(timeout=1000):
                            deposit_panel_visible = True
                            print("  → Панель депозита обнаружена")
                            break
                    except:
                        pass
                    await page.wait_for_timeout(500)
                
                if not deposit_panel_visible:
                    print("  ⚠️  Панель депозита не обнаружена, продолжаем поиск Next...")
                
                # Дополнительное ожидание для стабилизации UI
                await page.wait_for_timeout(1000)
                
                # Шаг 5.5: Поиск и клик по элементам депозита/оплаты (если открылась торговая панель)
                print("\n=== Шаг 5.5: Поиск элементов депозита/оплаты ===")
                deposit_elements_clicked = False
                
                # Паттерны для поиска элементов депозита/оплаты
                deposit_patterns = [
                    re.compile(r"deposit|пополн|внести|fund", re.I),
                    re.compile(r"payment\s*method|метод\s*оплат", re.I),
                    re.compile(r"upi|e-wallet|ewallet", re.I),
                    re.compile(r"cashier|касса", re.I),
                    re.compile(r"make\s*deposit|сделать\s*депозит", re.I),
                ]
                
                # Ищем элементы депозита на page и в frames (исключаем уже кликнутый "Deposit")
                for pattern in deposit_patterns:
                    try:
                        # На page
                        locs = page.locator("button, [role='button'], a, div, span").filter(has_text=pattern)
                        count = await locs.count()
                        for i in range(min(count, 10)):
                            try:
                                elem = locs.nth(i)
                                text = await elem.inner_text()
                                # Пропускаем уже кликнутый "Deposit"
                                if text and re.search(r"^deposit$|^пополн$", text, re.I):
                                    continue
                                if await elem.is_visible(timeout=1000):
                                    await elem.scroll_into_view_if_needed()
                                    await elem.click(timeout=5000)
                                    print(f"✓ Элемент депозита кликнут (на page): {text.strip()[:50]}")
                                    deposit_elements_clicked = True
                                    await page.wait_for_timeout(1500)
                                    break
                            except:
                                continue
                        if deposit_elements_clicked:
                            break
                    except:
                        pass
                    
                    # Во фреймах
                    for fr in page.frames:
                        try:
                            locs = fr.locator("button, [role='button'], a, div, span").filter(has_text=pattern)
                            count = await locs.count()
                            for i in range(min(count, 10)):
                                try:
                                    elem = locs.nth(i)
                                    text = await elem.inner_text()
                                    # Пропускаем уже кликнутый "Deposit"
                                    if text and re.search(r"^deposit$|^пополн$", text, re.I):
                                        continue
                                    if await elem.is_visible(timeout=1000):
                                        await elem.scroll_into_view_if_needed()
                                        await elem.click(timeout=5000)
                                        print(f"✓ Элемент депозита кликнут (в frame): {text.strip()[:50]}")
                                        deposit_elements_clicked = True
                                        await page.wait_for_timeout(1500)
                                        break
                                except:
                                    continue
                            if deposit_elements_clicked:
                                break
                        except:
                            continue
                    if deposit_elements_clicked:
                        break
                
                if not deposit_elements_clicked:
                    print("  ⚠️  Дополнительные элементы депозита не найдены, продолжаем поиск 'Next'...")
                else:
                    await page.wait_for_timeout(1500)
                
                # Шаг 6: Нажатие на кнопку "Next" (в page или frames)
                print("\n=== Шаг 6: Нажатие на кнопку 'Next' ===")
                
                # Дополнительное ожидание для стабилизации UI
                await page.wait_for_timeout(1000)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=5000)
                except:
                    pass  # Игнорируем таймаут, продолжаем
                
                # Функция для клика Next в page или любом frame
                async def click_next_anywhere(page):
                    """Ищет и кликает кнопку Next на page или в любом frame"""
                    next_re = re.compile(r"^(next|далее|continue|продолж|submit|go|вперёд)$", re.I)
                    next_text_re = re.compile(r"\b(next|далее|continue|продолж|submit|go|вперёд)\b", re.I)
                    
                    # Попытка 1: на странице через role
                    try:
                        loc = page.get_by_role("button", name=next_re).first
                        if await loc.count() > 0:
                            await loc.scroll_into_view_if_needed()
                            if await loc.is_visible(timeout=5000):
                                await loc.click(timeout=30000)
                                print("✓ 'Next' clicked (через role на page)")
                                return True
                    except:
                        pass
                    
                    # Попытка 2: на странице через text (filter)
                    try:
                        loc = page.locator("button, [role='button'], a, div, span").filter(has_text=next_text_re).first
                        if await loc.count() > 0:
                            await loc.scroll_into_view_if_needed()
                            if await loc.is_visible(timeout=5000):
                                await loc.click(timeout=30000)
                                print("✓ 'Next' clicked (через text на page)")
                                return True
                    except:
                        pass
                    
                    # Попытка 2b: на странице через итерацию по элементам
                    try:
                        locs = page.locator("button, [role='button'], a, div, span")
                        count = await locs.count()
                        for i in range(min(count, 100)):
                            try:
                                elem = locs.nth(i)
                                text = await elem.inner_text()
                                if text and re.search(next_text_re, text, re.I):
                                    await elem.scroll_into_view_if_needed()
                                    try:
                                        if await elem.is_visible(timeout=2000):
                                            is_enabled = await elem.evaluate("el => !el.disabled && el.getAttribute('aria-disabled') !== 'true'")
                                            if is_enabled:
                                                await elem.click(timeout=30000)
                                                print("✓ 'Next' clicked (через итерацию на page)")
                                                return True
                                        await elem.click(timeout=30000, force=True)
                                        print("✓ 'Next' clicked (через итерацию на page, force)")
                                        return True
                                    except:
                                        try:
                                            box = await elem.bounding_box()
                                            if box:
                                                await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                                print("✓ 'Next' clicked (через координаты на page)")
                                                return True
                                        except:
                                            pass
                            except:
                                continue
                    except:
                        pass
                    
                    # Попытка 3: во всех фреймах через role
                    for fr in page.frames:
                        try:
                            loc = fr.get_by_role("button", name=next_re).first
                            if await loc.count() > 0:
                                await loc.scroll_into_view_if_needed()
                                if await loc.is_visible(timeout=5000):
                                    await loc.click(timeout=30000)
                                    print(f"✓ 'Next' clicked (через role в frame: {fr.url})")
                                    return True
                        except:
                            pass
                        
                        # Попытка 4: во всех фреймах через text (filter)
                        try:
                            loc = fr.locator("button, [role='button'], a, div, span").filter(has_text=next_text_re).first
                            if await loc.count() > 0:
                                await loc.scroll_into_view_if_needed()
                                if await loc.is_visible(timeout=5000):
                                    await loc.click(timeout=30000)
                                    print(f"✓ 'Next' clicked (через text в frame: {fr.url})")
                                    return True
                        except:
                            pass
                        
                        # Попытка 4b: во всех фреймах через итерацию по элементам
                        try:
                            locs = fr.locator("button, [role='button'], a, div, span")
                            count = await locs.count()
                            for i in range(min(count, 100)):
                                try:
                                    elem = locs.nth(i)
                                    text = await elem.inner_text()
                                    if text and re.search(next_text_re, text, re.I):
                                        await elem.scroll_into_view_if_needed()
                                        try:
                                            if await elem.is_visible(timeout=2000):
                                                is_enabled = await elem.evaluate("el => !el.disabled && el.getAttribute('aria-disabled') !== 'true'")
                                                if is_enabled:
                                                    await elem.click(timeout=30000)
                                                    print(f"✓ 'Next' clicked (через итерацию в frame: {fr.url})")
                                                    return True
                                            await elem.click(timeout=30000, force=True)
                                            print(f"✓ 'Next' clicked (через итерацию в frame, force: {fr.url})")
                                            return True
                                        except:
                                            try:
                                                box = await elem.bounding_box()
                                                if box:
                                                    await fr.evaluate(f"document.elementFromPoint({box['x'] + box['width']/2}, {box['y'] + box['height']/2})?.click()")
                                                    print(f"✓ 'Next' clicked (через координаты в frame: {fr.url})")
                                                    return True
                                            except:
                                                pass
                                except:
                                    continue
                        except:
                            pass
                    
                    return False
                
                # Диагностика перед поиском Next
                print("  → Диагностика: поиск всех кликабельных элементов...")
                try:
                    all_clickable = []
                    # На странице
                    locs_page = page.locator("button, [role='button'], a, div, span")
                    count_page = await locs_page.count()
                    for i in range(min(count_page, 50)):
                        try:
                            text = await locs_page.nth(i).inner_text()
                            if text and len(text.strip()) < 50:
                                all_clickable.append(f"page: {text.strip()}")
                        except:
                            pass
                    # Во фреймах
                    for fr_idx, fr in enumerate(page.frames):
                        try:
                            locs_frame = fr.locator("button, [role='button'], a, div, span")
                            count_frame = await locs_frame.count()
                            for i in range(min(count_frame, 50)):
                                try:
                                    text = await locs_frame.nth(i).inner_text()
                                    if text and len(text.strip()) < 50:
                                        all_clickable.append(f"frame{fr_idx}: {text.strip()}")
                                except:
                                    pass
                        except:
                            pass
                    if all_clickable:
                        print(f"  → Найдено кликабельных элементов: {len(all_clickable)}")
                        print(f"  → Примеры: {', '.join(all_clickable[:30])}")
                except:
                    pass
                
                # Ожидаем появления кнопки Next (может появиться с задержкой)
                print("  → Ожидание появления кнопки 'Next'...")
                next_found = False
                for attempt in range(20):  # Ждём до 10 секунд
                    try:
                        # Проверяем на page
                        next_re = re.compile(r"^(next|далее|continue|продолж|submit|go|вперёд)$", re.I)
                        next_text_re = re.compile(r"\b(next|далее|continue|продолж|submit|go|вперёд)\b", re.I)
                        
                        # Быстрая проверка через role
                        try:
                            loc = page.get_by_role("button", name=next_re).first
                            if await loc.count() > 0 and await loc.is_visible(timeout=1000):
                                next_found = True
                                break
                        except:
                            pass
                        
                        # Проверка через text
                        try:
                            loc = page.locator("button, [role='button'], a, div, span").filter(has_text=next_text_re).first
                            if await loc.count() > 0 and await loc.is_visible(timeout=1000):
                                next_found = True
                                break
                        except:
                            pass
                        
                        # Проверка во фреймах
                        for fr in page.frames:
                            try:
                                loc = fr.get_by_role("button", name=next_re).first
                                if await loc.count() > 0 and await loc.is_visible(timeout=1000):
                                    next_found = True
                                    break
                            except:
                                pass
                            try:
                                loc = fr.locator("button, [role='button'], a, div, span").filter(has_text=next_text_re).first
                                if await loc.count() > 0 and await loc.is_visible(timeout=1000):
                                    next_found = True
                                    break
                            except:
                                pass
                        if next_found:
                            break
                    except:
                        pass
                    await page.wait_for_timeout(500)
                
                if not next_found:
                    print("  ⚠️  Кнопка 'Next' не появилась, продолжаем поиск...")
                
                # Кликаем Next
                next_clicked = await click_next_anywhere(page)
                
                if not next_clicked:
                    # Скриншот для диагностики
                    try:
                        debug_screenshot = os.path.join(self.screenshot_dir, f"debug_next_not_found_{int(time.time())}.png")
                        await page.screenshot(path=debug_screenshot, full_page=True)
                        print(f"  → Скриншот для диагностики: {debug_screenshot}")
                    except:
                        pass
                    raise Exception("Не найдена кнопка 'Next' (ни на page, ни во фреймах)")
                
                await page.wait_for_timeout(800)
                
                # Шаг 6b: Нажатие на кнопку "Confirm" (если требуется)
                print("\n=== Шаг 6b: Нажатие на кнопку 'Confirm' (если требуется) ===")
                await page.wait_for_timeout(800)
                
                # Функция для клика Confirm в page или любом frame
                async def click_confirm_anywhere(page):
                    """Ищет и кликает кнопку Confirm на page или в любом frame"""
                    confirm_re = re.compile(r"^confirm$|подтверд|подтвержд", re.I)
                    
                    # Попытка 1: на странице через role
                    try:
                        loc = page.get_by_role("button", name=confirm_re).first
                        if await loc.count() > 0:
                            await loc.scroll_into_view_if_needed()
                            if await loc.is_visible(timeout=5000):
                                await loc.click(timeout=30000)
                                print("✓ 'Confirm' clicked (через role на page)")
                                return True
                    except:
                        pass
                    
                    # Попытка 2: на странице через text
                    try:
                        loc = page.locator("button, [role='button'], a, div").filter(has_text=confirm_re).first
                        if await loc.count() > 0:
                            await loc.scroll_into_view_if_needed()
                            if await loc.is_visible(timeout=5000):
                                await loc.click(timeout=30000)
                                print("✓ 'Confirm' clicked (через text на page)")
                                return True
                    except:
                        pass
                    
                    # Попытка 3: во всех фреймах через role
                    for fr in page.frames:
                        try:
                            loc = fr.get_by_role("button", name=confirm_re).first
                            if await loc.count() > 0:
                                await loc.scroll_into_view_if_needed()
                                if await loc.is_visible(timeout=5000):
                                    await loc.click(timeout=30000)
                                    print(f"✓ 'Confirm' clicked (через role в frame: {fr.url})")
                                    return True
                        except:
                            pass
                        
                        # Попытка 4: во всех фреймах через text
                        try:
                            loc = fr.locator("button, [role='button'], a, div").filter(has_text=confirm_re).first
                            if await loc.count() > 0:
                                await loc.scroll_into_view_if_needed()
                                if await loc.is_visible(timeout=5000):
                                    await loc.click(timeout=30000)
                                    print(f"✓ 'Confirm' clicked (через text в frame: {fr.url})")
                                    return True
                        except:
                            pass
                    
                    return False
                
                clicked_confirm = await click_confirm_anywhere(page)
                if clicked_confirm:
                    print("✓ 'Confirm' clicked")
                    await page.wait_for_timeout(1200)
                else:
                    print("ℹ️  Кнопка 'Confirm' не найдена — возможно сразу будет форма или редирект")
                
                # Шаг 7: Поиск формы / заполнение / Proceed
                print("\n=== Шаг 7: Поиск формы / заполнение / Proceed ===")
                
                # Инициализируем form_data до ветвления (чтобы избежать UnboundLocalError)
                form_data = config.get("provider_form_data", {})
                if not form_data:
                    form_data = {
                        "first_name": "kapil",
                        "last_name": "Sharma",
                        "phone": "8925242020",
                        "upi_id": "kapil.ss17@icici",
                    }
                
                # Функция для проверки наличия UPI формы (по placeholder)
                async def is_upi_form_visible(page):
                    """Проверяет наличие UPI формы по placeholder'ам"""
                    patterns = [
                        re.compile(r"first\s*name", re.I),
                        re.compile(r"last\s*name", re.I),
                        re.compile(r"phone", re.I),
                        re.compile(r"upi\s*id|\bupi\b", re.I),
                    ]
                    # Если нашли хотя бы 2 поля из 4 — считаем, что форма есть
                    found = 0
                    for pat in patterns:
                        try:
                            # Проверяем на page
                            if await page.get_by_placeholder(pat).count() > 0:
                                found += 1
                                continue
                            # Проверяем в frames
                            for fr in page.frames:
                                try:
                                    if await fr.get_by_placeholder(pat).count() > 0:
                                        found += 1
                                        break
                                except:
                                    continue
                        except:
                            pass
                    return found >= 2
                
                # Функция для заполнения UPI формы (через placeholder)
                async def fill_upi_form(page):
                    """Заполняет UPI форму через placeholder'ы"""
                    contexts = [page] + list(page.frames)
                    
                    first_name = form_data.get("first_name", "kapil")
                    last_name = form_data.get("last_name", "Sharma")
                    phone = form_data.get("phone_number", form_data.get("phone", "8925242020"))
                    upi_id = form_data.get("upi_id", "kapil.ss17@icici")
                    
                    for ctx in contexts:
                        try:
                            await ctx.get_by_placeholder(re.compile(r"first\s*name", re.I)).first.fill(first_name)
                            print(f"✓ Заполнено First Name: {first_name}")
                            break
                        except:
                            continue
                    
                    for ctx in contexts:
                        try:
                            await ctx.get_by_placeholder(re.compile(r"last\s*name", re.I)).first.fill(last_name)
                            print(f"✓ Заполнено Last Name: {last_name}")
                            break
                        except:
                            continue
                    
                    for ctx in contexts:
                        try:
                            await ctx.get_by_placeholder(re.compile(r"phone", re.I)).first.fill(phone)
                            print(f"✓ Заполнено Phone: {phone}")
                            break
                        except:
                            continue
                    
                    for ctx in contexts:
                        try:
                            await ctx.get_by_placeholder(re.compile(r"upi\s*id|\bupi\b", re.I)).first.fill(upi_id)
                            print(f"✓ Заполнено UPI ID: {upi_id}")
                            break
                        except:
                            continue
                
                # Функция для клика "Proceed to payment" с разблокировкой
                async def click_proceed(page):
                    """Кликает кнопку 'Proceed to payment' с разблокировкой"""
                    # Попытка 1: через role
                    try:
                        btn = page.get_by_role("button", name=re.compile(r"proceed\s*to\s*payment", re.I)).first
                        if await btn.count() > 0:
                            await btn.wait_for(state="visible", timeout=5000)
                            # Ждём, пока станет enabled
                            try:
                                await btn.wait_for(state="attached", timeout=2000)
                                is_disabled = await btn.evaluate("el => el.disabled || el.getAttribute('aria-disabled')==='true'")
                                if not is_disabled:
                                    await btn.click(timeout=30000)
                                    print("✓ 'Proceed to payment' clicked (через role)")
                                    return True
                            except:
                                pass
                    except:
                        pass
                    
                    # Попытка 2: через text locator
                    try:
                        loc = page.locator("button, [role='button'], a, div").filter(has_text=re.compile(r"proceed\s*to\s*payment", re.I)).first
                        if await loc.count() > 0:
                            await loc.scroll_into_view_if_needed()
                            if await loc.is_visible(timeout=5000):
                                await loc.click(timeout=30000)
                                print("✓ 'Proceed to payment' clicked (через text)")
                                return True
                    except:
                        pass
                    
                    # Попытка 3: в frames
                    for fr in page.frames:
                        try:
                            btn = fr.get_by_role("button", name=re.compile(r"proceed\s*to\s*payment", re.I)).first
                            if await btn.count() > 0:
                                await btn.wait_for(state="visible", timeout=5000)
                                await btn.click(timeout=30000)
                                print(f"✓ 'Proceed to payment' clicked (в frame: {fr.url})")
                                return True
                        except:
                            try:
                                loc = fr.locator("button, [role='button'], a, div").filter(has_text=re.compile(r"proceed\s*to\s*payment", re.I)).first
                                if await loc.count() > 0:
                                    await loc.scroll_into_view_if_needed()
                                    if await loc.is_visible(timeout=5000):
                                        await loc.click(timeout=30000)
                                        print(f"✓ 'Proceed to payment' clicked (в frame через text: {fr.url})")
                                        return True
                            except:
                                pass
                    
                    return False
                
                # После Confirm может появиться форма
                await page.wait_for_timeout(800)
                
                if await is_upi_form_visible(page):
                    print("✓ UPI форма найдена — заполняем поля")
                    await fill_upi_form(page)
                    
                    # Триггер валидации
                    await page.keyboard.press("Tab")
                    await page.wait_for_timeout(500)
                    
                    # Проверяем чекбоксы (согласие/terms)
                    try:
                        checkbox = page.locator("input[type='checkbox']").first
                        if await checkbox.count() > 0 and await checkbox.is_visible(timeout=2000):
                            await checkbox.check()
                            print("✓ Отмечен чекбокс согласия")
                            await page.wait_for_timeout(300)
                    except:
                        pass
                    
                    print("→ Нажимаем 'Proceed to payment'")
                    proceed_clicked = await click_proceed(page)
                    if not proceed_clicked:
                        # Диагностика
                        try:
                            debug_screenshot = os.path.join(self.screenshot_dir, f"debug_proceed_{int(time.time())}.png")
                            await page.screenshot(path=debug_screenshot, full_page=True)
                            print(f"  → Скриншот для диагностики: {debug_screenshot}")
                        except:
                            pass
                        raise Exception("Не удалось нажать 'Proceed to payment' (возможно кнопка disabled из-за валидации)")
                    
                    form_found = True
                else:
                    print("ℹ️  UPI форма не найдена — возможно уже редирект/следующий шаг у провайдера")
                    form_found = False
                
                # Шаг 8: Обработка popup / редирект → заполнение формы провайдера → финальный URL + скриншот
                print("\n=== Шаг 8: Обработка popup / редирект ===")
                
                # Ждём редирект или popup
                start_url = page.url
                print(f"  → Начальный URL: {start_url}")
                
                # Сначала проверяем уже открытые страницы (popup мог открыться до подписки на событие)
                all_pages_before = context.pages
                print(f"  → Открытых страниц до ожидания: {len(all_pages_before)}")
                
                # Ожидаем возможный popup (новая вкладка) - но не ждём его, просто создаём promise для фолбэка
                try:
                    popup_promise = asyncio.create_task(context.wait_for_event("page", timeout=20000))
                except:
                    popup_promise = None
                
                # Даём время для открытия popup после Confirm
                await page.wait_for_timeout(3000)
                
                # Проверяем popup и редирект одновременно
                provider_page = None
                provider_url = None
                
                # Сначала проверяем уже открытые страницы
                all_pages_now = context.pages
                print(f"  → Открытых страниц после ожидания: {len(all_pages_now)}")
                
                # Ищем новую страницу или страницу с 4fb5.com
                for p in all_pages_now:
                    try:
                        p_url = p.url
                        print(f"  → Проверяем страницу: {p_url}")
                        # Если это не основная страница и содержит признаки провайдера
                        if p != page and ("4fb5.com" in p_url or "payment" in p_url.lower() or p_url != start_url):
                            print(f"  → Найдена страница провайдера: {p_url}")
                            provider_page = p
                            provider_url = p_url
                            await p.wait_for_load_state("domcontentloaded", timeout=15000)
                            break
                    except Exception as e:
                        print(f"  → Ошибка при проверке страницы: {e}")
                        continue
                
                # Если не нашли в уже открытых, ждём новую страницу через событие
                if not provider_page and popup_promise:
                    try:
                        provider_page = await asyncio.wait_for(popup_promise, timeout=5.0)
                        print("  → Обнаружен popup через wait_for_event (новая вкладка)")
                        # Ждём загрузки popup
                        await provider_page.wait_for_load_state("domcontentloaded", timeout=15000)
                        provider_url = provider_page.url
                        print(f"  → Provider page URL: {provider_url}")
                    except (asyncio.TimeoutError, AttributeError):
                        print("  → Popup не открылся через wait_for_event, проверяем редирект в той же вкладке")
                        provider_page = page
                        # Ждём смену URL (до 45 секунд)
                        for i in range(90):
                            await page.wait_for_timeout(500)
                            current_url = page.url
                            if current_url != start_url:
                                print(f"✓ Редирект обнаружен: {current_url}")
                                provider_url = current_url
                                break
                        else:
                            provider_url = page.url
                            print(f"⚠️  Редирект не произошёл, используем текущий URL: {provider_url}")
                
                # Функция для заполнения формы провайдера (4fb5.com) с проверкой
                # Правильная реализация: placeholder-first, page+frames, fallback через near-text
                async def fill_4fb5_form(provider_page):
                    """Заполняет UPI форму провайдера через placeholder'ы с проверкой значений"""
                    # Дождёмся, что хотя бы один input появился
                    await provider_page.wait_for_load_state("domcontentloaded")
                    await provider_page.locator("input, textarea").first.wait_for(timeout=20000)
                    
                    # Получаем все контексты (page + frames)
                    async def _all_contexts(page):
                        return [page] + [fr for fr in page.frames]
                    
                    contexts = await _all_contexts(provider_page)
                    
                    # Спецификация полей
                    FIELD_SPECS = [
                        ("first_name", [re.compile(r"first\s*name", re.I)], form_data.get("first_name", "kapil")),
                        ("last_name", [re.compile(r"last\s*name", re.I)], form_data.get("last_name", "Sharma")),
                        ("phone", [re.compile(r"phone", re.I)], form_data.get("phone_number", form_data.get("phone", "8925242020"))),
                        ("upi_id", [re.compile(r"upi\s*id", re.I), re.compile(r"\bupi\b", re.I)], form_data.get("upi_id", "kapil.ss17@icici")),
                    ]
                    
                    # Поиск по placeholder
                    async def _find_by_placeholder(ctx, patterns):
                        for pat in patterns:
                            try:
                                loc = ctx.get_by_placeholder(pat).first
                                if await loc.count():
                                    return loc
                            except:
                                pass
                        return None
                    
                    # Fallback: поиск input рядом с текстом
                    async def _find_by_near_text(ctx, patterns):
                        """Fallback: find an element that has the label text and then find an input below it."""
                        for pat in patterns:
                            try:
                                block = ctx.locator("div").filter(has_text=pat).first
                                if await block.count():
                                    inp = block.locator("input, textarea").first
                                    if await inp.count():
                                        return inp
                            except:
                                pass
                        return None
                    
                    # Заполняем каждое поле
                    for field_key, patterns, value in FIELD_SPECS:
                        target = None
                        
                        # 1) placeholder (page+frames)
                        for ctx in contexts:
                            target = await _find_by_placeholder(ctx, patterns)
                            if target:
                                break
                        
                        # 2) fallback: рядом с текстом (page+frames)
                        if not target:
                            for ctx in contexts:
                                target = await _find_by_near_text(ctx, patterns)
                                if target:
                                    break
                        
                        if not target:
                            raise Exception(f"Поле {field_key} не найдено (placeholder/near-text)")
                        
                        await target.scroll_into_view_if_needed()
                        await target.click()
                        await target.fill(value)
                        
                        # verify
                        try:
                            current = (await target.input_value()).strip()
                            if current != value:
                                raise Exception(f"Поле {field_key} не заполнилось: '{current}' != '{value}'")
                            print(f"✓ Заполнено {field_key}: {value} (проверено)")
                        except Exception as e:
                            if "не заполнилось" in str(e):
                                raise
                            # иногда input_value не доступен (редко) — тогда хотя бы blur
                            pass
                    
                    # Триггер валидации
                    await provider_page.keyboard.press("Tab")
                    await provider_page.wait_for_timeout(300)
                
                # Функция для клика Proceed в popup провайдера (с ожиданием enabled)
                async def click_proceed_4fb5(provider_page):
                    """Кликает Proceed to payment в popup провайдера, дожидаясь enabled состояния"""
                    proceed_re = re.compile(r"proceed\s*to\s*payment", re.I)
                    
                    btn = provider_page.get_by_role("button", name=proceed_re).first
                    await btn.wait_for(timeout=20000)
                    
                    # Подождём, пока станет enabled
                    for _ in range(30):  # ~15 секунд
                        try:
                            if await btn.is_enabled():
                                await btn.click()
                                print("✓ 'Proceed to payment' clicked (enabled)")
                                return True
                        except:
                            pass
                        await provider_page.wait_for_timeout(500)
                    
                    # Если так и не стала enabled — делаем скрин и падаем
                    ts = int(time.time())
                    debug_screenshot = os.path.join(self.screenshot_dir, f"debug_4fb5_proceed_disabled_{ts}.png")
                    await provider_page.screenshot(path=debug_screenshot, full_page=True)
                    print(f"  → Скриншот для диагностики: {debug_screenshot}")
                    raise Exception("Proceed to payment осталась disabled после заполнения полей")
                
                # Функция для захвата финального редиректа после Proceed (параллельное ожидание popup и смены URL)
                async def capture_after_proceed(ctx, provider_page):
                    """Ждёт финальный редирект после Proceed (popup или смена URL) и делает скриншот"""
                    start_url = provider_page.url
                    print(f"  → Начальный URL перед Proceed: {start_url}")
                    
                    async def wait_popup():
                        """Ожидает открытие нового popup"""
                        try:
                            new_page = await ctx.wait_for_event("page", timeout=20000)
                            await new_page.wait_for_load_state("domcontentloaded", timeout=45000)
                            print(f"  → Обнаружен новый popup: {new_page.url}")
                            return new_page
                        except:
                            return None
                    
                    async def wait_url_change():
                        """Ожидает смену URL в текущей странице провайдера"""
                        for i in range(120):  # ~60 сек
                            await provider_page.wait_for_timeout(500)
                            current_url = provider_page.url
                            if current_url != start_url:
                                print(f"  → Редирект в текущей вкладке: {current_url}")
                                return provider_page
                        # Если URL не изменился, возвращаем страницу как есть
                        return provider_page
                    
                    # Параллельно ждём popup и смену URL
                    popup_task = asyncio.create_task(wait_popup())
                    url_task = asyncio.create_task(wait_url_change())
                    
                    done, pending = await asyncio.wait(
                        {popup_task, url_task},
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=60
                    )
                    
                    # Отменяем оставшиеся задачи
                    for t in pending:
                        t.cancel()
                    
                    # Определяем целевую страницу
                    target = None
                    for task in done:
                        try:
                            result = task.result()
                            if result:
                                target = result
                                break
                        except:
                            pass
                    
                    # Если ничего не получилось, используем provider_page
                    if not target:
                        target = provider_page
                    
                    # Ждём загрузки страницы
                    try:
                        await target.wait_for_load_state("domcontentloaded", timeout=10000)
                    except:
                        pass
                    
                    # Дополнительное ожидание для стабилизации
                    await target.wait_for_timeout(2000)
                    
                    final_url = target.url
                    print(f"  → Финальный URL: {final_url}")
                    
                    ts = int(time.time())
                    screenshot = os.path.join(self.screenshot_dir, f"olymptrade_final_{ts}.png")
                    await target.screenshot(path=screenshot, full_page=True)
                    
                    return final_url, screenshot
                
                # Проверяем, если это форма провайдера (4fb5.com/payment)
                if provider_page and "4fb5.com" in provider_url and "/payment" in provider_url:
                    print("\n=== Шаг 9: Заполнение формы провайдера (4fb5) ===")
                    await fill_4fb5_form(provider_page)
                    print("✓ Поля заполнены и проверены")
                    
                    print("\n=== Шаг 10: Нажатие 'Proceed to payment' ===")
                    await click_proceed_4fb5(provider_page)
                    print("✓ Proceed clicked")
                    
                    print("\n=== Шаг 11: Финальный редирект + скрин + URL ===")
                    final_url, screenshot_path = await capture_after_proceed(context, provider_page)
                else:
                    # Если это уже финальная страница (редко), тогда просто скрин
                    print("ℹ️  Это не форма провайдера, делаем скриншот текущей страницы")
                    final_url = provider_url
                    ts = int(time.time())
                    screenshot_path = os.path.join(self.screenshot_dir, f"olymptrade_provider_final_{ts}.png")
                    await provider_page.screenshot(path=screenshot_path, full_page=True)
                
                print(f"✓ Final URL: {final_url}")
                print(f"✓ Screenshot: {screenshot_path}")
                
                # Определяем домен провайдера
                provider_domain = self.get_domain(final_url)
                if not provider_domain or provider_domain == merchant_domain:
                    provider_domain = "internal_or_delayed"
                
                # Сохраняем в БД
                result = {
                    "provider_domain": provider_domain,
                    "provider_name": "olymptrade_payment",
                    "provider_entry_url": final_url,
                    "final_url": final_url,
                    "cashier_url": merchant_url,
                    "screenshot_path": screenshot_path,
                    "detected_in": "navigation_after_proceed",
                    "payment_method": "UPI",
                    "is_iframe": False,
                }
                
                saved = self.storage.save_provider(
                    merchant=merchant_id,
                    merchant_domain=merchant_domain,
                    provider_domain=result["provider_domain"],
                    account_type=account_type,
                    provider_name=result["provider_name"],
                    provider_entry_url=result["provider_entry_url"],
                    final_url=result["final_url"],
                    cashier_url=result["cashier_url"],
                    screenshot_path=result["screenshot_path"],
                    detected_in=result["detected_in"],
                    payment_method=result["payment_method"],
                    is_iframe=result["is_iframe"],
                )
                
                if saved:
                    print(f"✓ Данные сохранены в БД")
                    results.append(result)
                
                # Записываем deposit result в Google Sheets (отдельный метод)
                try:
                    from datetime import datetime, timezone
                    timestamp_iso = datetime.now(timezone.utc).isoformat()
                    self.storage.append_deposit_result(
                        merchant="olymptrade",
                        timestamp=timestamp_iso,
                        final_url=final_url,
                        screenshot_path=os.path.basename(screenshot_path)  # Только имя файла
                    )
                    print(f"✅ Redirect URL: {final_url}")
                    print(f"✅ Screenshot: {screenshot_path}")
                except Exception as e:
                    print(f"⚠️  Ошибка при добавлении deposit result в Google Sheets: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Возвращаем результат
                return {
                    "status": "OK",
                    "providers": results,
                    "meta": {
                        "final_url": final_url,
                        "screenshot_path": screenshot_path
                    }
                }
                
            except Exception as e:
                print(f"❌ Ошибка при парсинге Olymptrade: {e}")
                import traceback
                traceback.print_exc()
                return {"status": "ERROR", "error": str(e), "providers": []}
            finally:
                await browser.close()
        
        # Fallback (не должно сюда попасть)
        return {"status": "ERROR", "error": "Unexpected end of parse_olymptrade", "providers": []}
    
