"""API endpoints для экспорта данных"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, Response
import pandas as pd
from io import StringIO
import os
from app.services.storage_adapter import StorageAdapter
from app.config import BASE_DIR, XLSX_PATH

router = APIRouter(prefix="/export", tags=["export"])
storage_adapter = StorageAdapter()


@router.get("/xlsx")
async def export_xlsx(
    background_tasks: BackgroundTasks,
    formatted: bool = Query(False, description="Форматированный Excel с цветами")
):
    """
    Экспорт данных в XLSX формат
    
    Args:
        formatted: Если True, создается форматированный Excel с цветами и автошириной
    """
    try:
        if formatted:
            # Используем форматированный экспорт
            from app.services.report_generator import get_report_generator
            import tempfile
            
            providers = storage_adapter.storage.get_all_providers()
            
            report_generator = get_report_generator()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            temp_file.close()
            
            output_path = report_generator.generate_excel_report_formatted(
                data=providers,
                output_path=temp_file.name,
                title="Providers Report"
            )
            
            if output_path:
                # Удалим файл после отправки
                def cleanup_file(path: str):
                    try:
                        if os.path.exists(path):
                            os.unlink(path)
                    except OSError as e:
                        logger.warning(f"Failed to cleanup temp file {path}: {e}")
                
                background_tasks.add_task(cleanup_file, output_path)
                
                return FileResponse(
                    path=output_path,
                    filename="providers_data_formatted.xlsx",
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                # Fallback к обычному экспорту
                output_path = storage_adapter.export_to_xlsx()
                if not output_path or not BASE_DIR.joinpath(output_path).exists():
                    raise HTTPException(status_code=500, detail="Не удалось создать XLSX файл")
                return FileResponse(
                    path=str(BASE_DIR / output_path),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename="providers_data.xlsx"
                )
        else:
            # Обычный экспорт
            output_path = storage_adapter.export_to_xlsx()
            if not output_path or not BASE_DIR.joinpath(output_path).exists():
                raise HTTPException(status_code=500, detail="Не удалось создать XLSX файл")
            return FileResponse(
                path=str(BASE_DIR / output_path),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename="providers_data.xlsx"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при экспорте в XLSX: {str(e)}")


@router.get("/csv")
async def export_csv(
    merchant: str = None,
    provider_domain: str = None,
    account_type: str = None,
    payment_method: str = None,
    search: str = None,
):
    """
    Экспорт данных в CSV формат с возможностью фильтрации
    """
    try:
        result = storage_adapter.get_all_providers(
            merchant=merchant,
            provider_domain=provider_domain,
            account_type=account_type,
            payment_method=payment_method,
            search=search,
            skip=0,
            limit=10000  # Максимум для CSV
        )
        
        if not result["items"]:
            raise HTTPException(status_code=404, detail="Нет данных для экспорта")
        
        # Преобразуем в DataFrame
        df = pd.DataFrame(result["items"])
        
        # Удаляем служебные колонки
        df = df.drop(columns=['id'], errors='ignore')
        
        # Создаем CSV в памяти
        output = StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=providers_data.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при экспорте в CSV: {str(e)}")


@router.get("/json")
async def export_json(
    background_tasks: BackgroundTasks,
    merchant: str = None,
    provider_domain: str = None,
    account_type: str = None,
    payment_method: str = None,
    search: str = None,
):
    """
    Экспорт данных в JSON формат с возможностью фильтрации
    """
    try:
        result = storage_adapter.get_all_providers(
            merchant=merchant,
            provider_domain=provider_domain,
            account_type=account_type,
            payment_method=payment_method,
            search=search,
            skip=0,
            limit=10000  # Максимум для JSON
        )
        
        return result  # FastAPI автоматически сериализует в JSON
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при экспорте в JSON: {str(e)}")


@router.get("/pdf")
async def export_pdf(background_tasks: BackgroundTasks):
    """
    Экспорт данных в PDF отчет
    
    Возвращает форматированный PDF отчет с таблицей провайдеров
    """
    try:
        from app.services.report_generator import get_report_generator
        import tempfile
        
        providers = storage_adapter.storage.get_all_providers()
        
        report_generator = get_report_generator()
        
        if not report_generator.pdf_available:
            raise HTTPException(
                status_code=503,
                detail="PDF generation not available. Install reportlab: pip install reportlab"
            )
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        output_path = report_generator.generate_pdf_report(
            data=providers,
            output_path=temp_file.name,
            title="Providers Report",
            include_statistics=True
        )
        
        if not output_path:
            raise HTTPException(status_code=500, detail="Failed to generate PDF report")
        
        # Удалить файл после отправки
        def cleanup_file(path: str):
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except OSError as e:
                logger.warning(f"Failed to cleanup temp PDF file {path}: {e}")
        
        background_tasks.add_task(cleanup_file, output_path)
        
        return FileResponse(
            path=output_path,
            filename="providers_report.pdf",
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при экспорте в PDF: {str(e)}")
