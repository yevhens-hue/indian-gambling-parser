"""
Тесты для модуля report_generator
"""
import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent.parent / "web_service" / "backend"))

from app.services.report_generator import ReportGenerator, get_report_generator


@pytest.fixture
def sample_data():
    """Пример данных провайдеров"""
    return [
        {
            "id": 1,
            "merchant": "1win",
            "provider_domain": "payment.com",
            "account_type": "deposit",
            "payment_method": "card"
        },
        {
            "id": 2,
            "merchant": "1win",
            "provider_domain": "crypto.io",
            "account_type": "withdrawal",
            "payment_method": "crypto"
        },
        {
            "id": 3,
            "merchant": "melbet",
            "provider_domain": "bank.net",
            "account_type": "deposit",
            "payment_method": "upi"
        }
    ]


@pytest.fixture
def large_data():
    """Большой набор данных (больше 100 записей)"""
    return [
        {
            "id": i,
            "merchant": f"merchant_{i % 5}",
            "provider_domain": f"provider{i}.com",
            "account_type": "deposit" if i % 2 == 0 else "withdrawal",
            "payment_method": "card"
        }
        for i in range(150)
    ]


@pytest.fixture
def temp_dir():
    """Временная директория для тестов"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestReportGeneratorInit:
    """Тесты инициализации ReportGenerator"""
    
    def test_init(self):
        """Инициализация report generator"""
        generator = ReportGenerator()
        # pdf_available зависит от наличия reportlab
        assert isinstance(generator.pdf_available, bool)


class TestGeneratePdfReport:
    """Тесты генерации PDF отчетов"""
    
    def test_pdf_not_available(self):
        """Возвращает None если reportlab недоступен"""
        generator = ReportGenerator()
        generator.pdf_available = False
        
        result = generator.generate_pdf_report([], "/tmp/test.pdf")
        assert result is None
    
    @pytest.mark.skipif(
        not ReportGenerator().pdf_available,
        reason="reportlab not installed"
    )
    def test_generate_pdf_success(self, sample_data, temp_dir):
        """Успешная генерация PDF"""
        generator = ReportGenerator()
        output_path = os.path.join(temp_dir, "report.pdf")
        
        result = generator.generate_pdf_report(
            data=sample_data,
            output_path=output_path,
            title="Test Report"
        )
        
        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    @pytest.mark.skipif(
        not ReportGenerator().pdf_available,
        reason="reportlab not installed"
    )
    def test_generate_pdf_empty_data(self, temp_dir):
        """Генерация PDF с пустыми данными"""
        generator = ReportGenerator()
        output_path = os.path.join(temp_dir, "empty_report.pdf")
        
        result = generator.generate_pdf_report(
            data=[],
            output_path=output_path,
            title="Empty Report"
        )
        
        assert result == output_path
        assert os.path.exists(output_path)
    
    @pytest.mark.skipif(
        not ReportGenerator().pdf_available,
        reason="reportlab not installed"
    )
    def test_generate_pdf_without_statistics(self, sample_data, temp_dir):
        """Генерация PDF без статистики"""
        generator = ReportGenerator()
        output_path = os.path.join(temp_dir, "no_stats_report.pdf")
        
        result = generator.generate_pdf_report(
            data=sample_data,
            output_path=output_path,
            include_statistics=False
        )
        
        assert result == output_path
        assert os.path.exists(output_path)
    
    @pytest.mark.skipif(
        not ReportGenerator().pdf_available,
        reason="reportlab not installed"
    )
    def test_generate_pdf_large_data(self, large_data, temp_dir):
        """Генерация PDF с большими данными (показывает первые 100)"""
        generator = ReportGenerator()
        output_path = os.path.join(temp_dir, "large_report.pdf")
        
        result = generator.generate_pdf_report(
            data=large_data,
            output_path=output_path,
            title="Large Report"
        )
        
        assert result == output_path
        assert os.path.exists(output_path)
    
    def test_generate_pdf_error_handling(self, sample_data):
        """Обработка ошибок при генерации PDF"""
        generator = ReportGenerator()
        
        if generator.pdf_available:
            # Невалидный путь
            result = generator.generate_pdf_report(
                data=sample_data,
                output_path="/nonexistent/path/report.pdf"
            )
            assert result is None


class TestGenerateExcelReport:
    """Тесты генерации Excel отчетов"""
    
    def test_generate_excel_success(self, sample_data, temp_dir):
        """Успешная генерация Excel"""
        generator = ReportGenerator()
        output_path = os.path.join(temp_dir, "report.xlsx")
        
        result = generator.generate_excel_report_formatted(
            data=sample_data,
            output_path=output_path,
            title="Test Report"
        )
        
        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    def test_generate_excel_empty_data(self, temp_dir):
        """Генерация Excel с пустыми данными возвращает None"""
        generator = ReportGenerator()
        output_path = os.path.join(temp_dir, "empty_report.xlsx")
        
        result = generator.generate_excel_report_formatted(
            data=[],
            output_path=output_path
        )
        
        assert result is None
    
    def test_generate_excel_verifies_content(self, sample_data, temp_dir):
        """Проверяет содержимое Excel файла"""
        import pandas as pd
        
        generator = ReportGenerator()
        output_path = os.path.join(temp_dir, "content_report.xlsx")
        
        result = generator.generate_excel_report_formatted(
            data=sample_data,
            output_path=output_path
        )
        
        # Читаем файл обратно
        df = pd.read_excel(output_path)
        
        assert len(df) == len(sample_data)
        assert "merchant" in df.columns
        assert "provider_domain" in df.columns
    
    def test_generate_excel_error_handling(self, sample_data):
        """Обработка ошибок при генерации Excel"""
        generator = ReportGenerator()
        
        # Невалидный путь
        result = generator.generate_excel_report_formatted(
            data=sample_data,
            output_path="/nonexistent/path/report.xlsx"
        )
        assert result is None


class TestGetReportGenerator:
    """Тесты получения глобального генератора"""
    
    def test_get_report_generator_singleton(self):
        """Возвращает один и тот же экземпляр"""
        import app.services.report_generator as module
        module._report_generator = None
        
        gen1 = get_report_generator()
        gen2 = get_report_generator()
        
        assert gen1 is gen2
    
    def test_get_report_generator_type(self):
        """Возвращает ReportGenerator"""
        import app.services.report_generator as module
        module._report_generator = None
        
        gen = get_report_generator()
        assert isinstance(gen, ReportGenerator)


class TestDataFormats:
    """Тесты различных форматов данных"""
    
    def test_missing_fields(self, temp_dir):
        """Данные с отсутствующими полями"""
        generator = ReportGenerator()
        
        data = [
            {"id": 1, "merchant": "test"},  # Нет других полей
            {"provider_domain": "domain.com"},  # Нет id и merchant
        ]
        
        output_path = os.path.join(temp_dir, "partial_report.xlsx")
        result = generator.generate_excel_report_formatted(data, output_path)
        
        assert result == output_path
        assert os.path.exists(output_path)
    
    def test_special_characters(self, temp_dir):
        """Данные со специальными символами"""
        generator = ReportGenerator()
        
        data = [
            {
                "id": 1,
                "merchant": "Тест кириллицы",
                "provider_domain": "日本語.jp",
                "account_type": "dépôt",
                "payment_method": "カード"
            }
        ]
        
        output_path = os.path.join(temp_dir, "special_chars_report.xlsx")
        result = generator.generate_excel_report_formatted(data, output_path)
        
        assert result == output_path
    
    def test_long_values(self, temp_dir):
        """Данные с очень длинными значениями"""
        generator = ReportGenerator()
        
        data = [
            {
                "id": 1,
                "merchant": "a" * 1000,  # Очень длинное значение
                "provider_domain": "x" * 500,
                "account_type": "normal",
                "payment_method": "card"
            }
        ]
        
        output_path = os.path.join(temp_dir, "long_values_report.xlsx")
        result = generator.generate_excel_report_formatted(data, output_path)
        
        assert result == output_path
        assert os.path.exists(output_path)
