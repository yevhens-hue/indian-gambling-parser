#!/usr/bin/env python3
"""
Streamlit веб-интерфейс для просмотра данных провайдеров
Быстрый прототип таблицы аналогичной Google Sheets
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
from datetime import datetime

# Добавляем текущую директорию в путь для импорта storage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from storage import Storage
except ImportError:
    st.error("❌ Не удалось импортировать storage.py. Убедитесь, что файл существует.")
    st.stop()

# Конфигурация страницы
st.set_page_config(
    page_title="Providers Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация Storage
@st.cache_resource
def init_storage():
    """Инициализация Storage с кешированием"""
    return Storage()

storage = init_storage()

# Загрузка данных с кешированием на 60 секунд
@st.cache_data(ttl=60)
def load_providers():
    """Загрузка всех провайдеров из БД"""
    try:
        providers = storage.get_all_providers()
        if not providers:
            return pd.DataFrame()
        return pd.DataFrame(providers)
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        return pd.DataFrame()

# Заголовок
st.title("📊 Providers Dashboard")
st.markdown("---")

# Загрузка данных
with st.spinner("Загрузка данных..."):
    df = load_providers()

if df.empty:
    st.warning("⚠️ Нет данных для отображения. Запустите парсер сначала.")
    st.stop()

# Sidebar с фильтрами
st.sidebar.header("🔍 Фильтры")

# Фильтр по Merchant
merchants = ["Все"] + sorted(df['merchant'].dropna().unique().tolist())
selected_merchant = st.sidebar.selectbox("Merchant", merchants)

# Фильтр по Account Type
account_types = ["Все"] + sorted(df['account_type'].dropna().unique().tolist())
selected_account_type = st.sidebar.selectbox("Account Type", account_types)

# Фильтр по Payment Method
payment_methods = ["Все"] + sorted(df['payment_method'].dropna().unique().tolist())
selected_payment_method = st.sidebar.selectbox("Payment Method", payment_methods)

# Поиск по тексту
search_text = st.sidebar.text_input("🔎 Поиск", placeholder="Введите текст для поиска...")

# Применение фильтров
filtered_df = df.copy()

if selected_merchant != "Все":
    filtered_df = filtered_df[filtered_df['merchant'] == selected_merchant]

if selected_account_type != "Все":
    filtered_df = filtered_df[filtered_df['account_type'] == selected_account_type]

if selected_payment_method != "Все":
    filtered_df = filtered_df[filtered_df['payment_method'] == selected_payment_method]

if search_text:
    # Поиск по всем текстовым колонкам
    text_columns = ['merchant', 'merchant_domain', 'provider_domain', 'provider_name', 
                    'account_type', 'payment_method', 'detected_in']
    mask = pd.Series([False] * len(filtered_df))
    for col in text_columns:
        if col in filtered_df.columns:
            mask |= filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
    filtered_df = filtered_df[mask]

# Метрики
col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего записей", len(filtered_df))
col2.metric("Уникальных мерчантов", filtered_df['merchant'].nunique() if not filtered_df.empty else 0)
col3.metric("Уникальных провайдеров", filtered_df['provider_domain'].nunique() if not filtered_df.empty else 0)
col4.metric("Типов аккаунтов", filtered_df['account_type'].nunique() if not filtered_df.empty else 0)

st.markdown("---")

# Таблица данных
st.subheader("📋 Таблица провайдеров")

if not filtered_df.empty:
    # Подготовка данных для отображения
    display_df = filtered_df.copy()
    
    # Удаляем служебные колонки для лучшей читаемости
    columns_to_hide = ['id']
    display_columns = [col for col in display_df.columns if col not in columns_to_hide]
    display_df = display_df[display_columns]
    
    # Сортировка по timestamp (новые сверху)
    if 'timestamp_utc' in display_df.columns:
        display_df = display_df.sort_values('timestamp_utc', ascending=False)
    
    # Отображение таблицы с возможностью сортировки
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        column_config={
            "screenshot_path": st.column_config.ImageColumn(
                "Screenshot",
                help="Скриншот платёжной формы",
                width="medium"
            ),
            "provider_entry_url": st.column_config.LinkColumn(
                "Entry URL",
                help="Первый внешний URL"
            ),
            "final_url": st.column_config.LinkColumn(
                "Final URL",
                help="Финальный URL после редиректов"
            ),
            "cashier_url": st.column_config.LinkColumn(
                "Cashier URL",
                help="URL страницы кэшира"
            ),
            "timestamp_utc": st.column_config.DatetimeColumn(
                "Timestamp",
                format="YYYY-MM-DD HH:mm:ss",
                width="medium"
            ),
            "is_iframe": st.column_config.CheckboxColumn(
                "Iframe",
                help="Форма в iframe"
            ),
            "requires_otp": st.column_config.CheckboxColumn(
                "Requires OTP",
                help="Требует OTP"
            ),
            "blocked_by_geo": st.column_config.CheckboxColumn(
                "Blocked",
                help="Заблокирован по гео"
            ),
            "captcha_present": st.column_config.CheckboxColumn(
                "Captcha",
                help="Присутствует капча"
            ),
        },
        hide_index=True
    )
    
    # Информация о результатах
    st.caption(f"Показано {len(filtered_df)} из {len(df)} записей")
else:
    st.info("ℹ️ Нет данных, соответствующих выбранным фильтрам")

# Экспорт данных
st.markdown("---")
st.subheader("📥 Экспорт данных")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Экспорт в XLSX", use_container_width=True):
        try:
            storage.export_to_xlsx()
            st.success("✓ Данные экспортированы в providers_data.xlsx")
        except Exception as e:
            st.error(f"Ошибка при экспорте: {e}")

with col2:
    # CSV экспорт
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Скачать CSV",
        data=csv,
        file_name=f"providers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

with col3:
    # JSON экспорт
    json_str = filtered_df.to_json(orient='records', indent=2)
    st.download_button(
        label="📋 Скачать JSON",
        data=json_str,
        file_name=f"providers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True
    )

# Статистика
st.markdown("---")
st.subheader("📈 Статистика")

if not filtered_df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Распределение по мерчантам:**")
        merchant_counts = filtered_df['merchant'].value_counts()
        st.bar_chart(merchant_counts)
    
    with col2:
        st.write("**Распределение по типам аккаунтов:**")
        account_counts = filtered_df['account_type'].value_counts()
        st.bar_chart(account_counts)
    
    # Таблица топ провайдеров
    st.write("**Топ провайдеров по количеству мерчантов:**")
    provider_counts = filtered_df.groupby('provider_domain')['merchant'].nunique().sort_values(ascending=False).head(10)
    st.dataframe(provider_counts.reset_index(), use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption(f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💡 Совет: Используйте фильтры в боковой панели для уточнения результатов")
