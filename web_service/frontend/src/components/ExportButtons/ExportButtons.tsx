/**
 * Компонент кнопок экспорта
 */
import { Button, Box, Tooltip } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import { exportXLSX, exportCSV, exportJSON } from '../../services/api';
import type { ProvidersQueryParams } from '../../services/api';

interface ExportButtonsProps {
  filters: ProvidersQueryParams;
}

export function ExportButtons({ filters }: ExportButtonsProps) {
  const handleExport = async (format: 'xlsx' | 'csv' | 'json') => {
    if (format === 'xlsx') {
      // XLSX - просто открываем ссылку
      window.open(exportXLSX(), '_blank');
    } else if (format === 'csv') {
      // CSV - открываем ссылку с фильтрами
      window.open(exportCSV(filters), '_blank');
    } else if (format === 'json') {
      // JSON - загружаем и скачиваем как файл
      try {
        const data = await exportJSON(filters);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `providers_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Ошибка при экспорте JSON:', error);
      }
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
      <Tooltip title="Экспорт в Excel">
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('xlsx')}
          size="small"
          sx={{
            borderRadius: 2,
            borderColor: 'rgba(144, 202, 249, 0.5)',
            color: '#90caf9',
            '&:hover': {
              borderColor: '#90caf9',
              background: 'rgba(144, 202, 249, 0.1)',
            },
          }}
        >
          XLSX
        </Button>
      </Tooltip>
      <Tooltip title="Экспорт в CSV">
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('csv')}
          size="small"
          sx={{
            borderRadius: 2,
            borderColor: 'rgba(144, 202, 249, 0.5)',
            color: '#90caf9',
            '&:hover': {
              borderColor: '#90caf9',
              background: 'rgba(144, 202, 249, 0.1)',
            },
          }}
        >
          CSV
        </Button>
      </Tooltip>
      <Tooltip title="Экспорт в JSON">
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('json')}
          size="small"
          sx={{
            borderRadius: 2,
            borderColor: 'rgba(144, 202, 249, 0.5)',
            color: '#90caf9',
            '&:hover': {
              borderColor: '#90caf9',
              background: 'rgba(144, 202, 249, 0.1)',
            },
          }}
        >
          JSON
        </Button>
      </Tooltip>
    </Box>
  );
}
