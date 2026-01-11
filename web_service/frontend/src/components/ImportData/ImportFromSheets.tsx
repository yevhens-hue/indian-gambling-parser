/**
 * Компонент для импорта данных из Google Sheets
 */
import { useState } from 'react';
import { Button, Box, TextField, Paper, Typography, Alert, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface ImportResult {
  status: string;
  message: string;
  imported: number;
  skipped: number;
  errors: number;
  total?: number;
}

interface PreviewResult {
  status: string;
  total_found: number;
  preview_count: number;
  preview: any[];
  columns: string[];
}

export function ImportFromSheets() {
  const [gid, setGid] = useState('396039446'); // GID для 1win IN
  const [sheetName, setSheetName] = useState('');
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const handlePreview = async () => {
    setPreviewLoading(true);
    setPreview(null);
    
    try {
      const params: any = { limit: 10 };
      if (gid) params.gid = gid;
      if (sheetName) params.sheet_name = sheetName;
      
      const response = await axios.get<PreviewResult>(
        `${API_URL}/import/google-sheets/preview`,
        { params }
      );
      setPreview(response.data);
      setPreviewOpen(true);
    } catch (error: any) {
      setResult({
        status: 'error',
        message: error.response?.data?.detail || error.message || 'Ошибка предпросмотра',
        imported: 0,
        skipped: 0,
        errors: 0,
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleImport = async () => {
    setLoading(true);
    setResult(null);
    
    try {
      const params: any = {};
      if (gid) params.gid = gid;
      if (sheetName) params.sheet_name = sheetName;
      
      const response = await axios.post<ImportResult>(
        `${API_URL}/import/google-sheets`,
        null,
        { params }
      );
      setResult(response.data);
      
      // Обновляем страницу через 2 секунды для показа новых данных
      if (response.data.status === 'success' && response.data.imported > 0) {
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      }
    } catch (error: any) {
      setResult({
        status: 'error',
        message: error.response?.data?.detail || error.message || 'Ошибка импорта',
        imported: 0,
        skipped: 0,
        errors: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ 
      p: 3, 
      mb: 3,
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: 2,
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
        <CloudUploadIcon sx={{ fontSize: 28, color: '#90caf9' }} />
        <Typography 
          variant="h6"
          sx={{ 
            fontWeight: 600,
            background: 'linear-gradient(135deg, #90caf9 0%, #ce93d8 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Импорт данных из Google Sheets
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          label="GID листа (из URL)"
          value={gid}
          onChange={(e) => setGid(e.target.value)}
          placeholder="396039446"
          helperText="GID можно найти в URL: .../edit?gid=396039446"
          size="small"
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              '& fieldset': {
                borderColor: 'rgba(255, 255, 255, 0.2)',
              },
              '&:hover fieldset': {
                borderColor: 'rgba(144, 202, 249, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#90caf9',
              },
            },
          }}
        />

        <TextField
          label="Название листа (опционально)"
          value={sheetName}
          onChange={(e) => setSheetName(e.target.value)}
          placeholder="Scraper (PY)"
          helperText="Если не указан GID, можно указать название листа"
          size="small"
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              '& fieldset': {
                borderColor: 'rgba(255, 255, 255, 0.2)',
              },
              '&:hover fieldset': {
                borderColor: 'rgba(144, 202, 249, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#90caf9',
              },
            },
          }}
        />

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            onClick={handlePreview}
            disabled={previewLoading || (!gid && !sheetName)}
            startIcon={previewLoading ? <CircularProgress size={16} /> : null}
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
            {previewLoading ? 'Загрузка...' : 'Предпросмотр'}
          </Button>

          <Button
            variant="contained"
            onClick={handleImport}
            disabled={loading || (!gid && !sheetName)}
            startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <CloudUploadIcon />}
            sx={{
              borderRadius: 2,
              background: 'linear-gradient(135deg, #90caf9 0%, #42a5f5 100%)',
              boxShadow: '0 4px 12px rgba(144, 202, 249, 0.3)',
              '&:hover': {
                background: 'linear-gradient(135deg, #64b5f6 0%, #1976d2 100%)',
                boxShadow: '0 6px 16px rgba(144, 202, 249, 0.4)',
              },
              '&:disabled': {
                background: 'rgba(255, 255, 255, 0.1)',
              },
            }}
          >
            {loading ? 'Импорт...' : 'Импортировать'}
          </Button>
        </Box>

        {result && (
          <Alert 
            severity={result.status === 'success' ? 'success' : 'error'}
            sx={{
              borderRadius: 2,
              backgroundColor: result.status === 'success' 
                ? 'rgba(102, 187, 106, 0.15)' 
                : 'rgba(239, 83, 80, 0.15)',
              border: `1px solid ${result.status === 'success' ? 'rgba(102, 187, 106, 0.3)' : 'rgba(239, 83, 80, 0.3)'}`,
            }}
          >
            <Typography variant="body2" fontWeight="bold" sx={{ mb: 0.5 }}>
              {result.status === 'success' ? '✅ Импорт завершен' : '❌ Ошибка импорта'}
            </Typography>
            <Typography variant="body2" sx={{ mb: result.status === 'success' ? 1 : 0 }}>
              {result.message}
            </Typography>
            {result.status === 'success' && (
              <Typography variant="caption" display="block" sx={{ mt: 1, opacity: 0.9 }}>
                Импортировано: <strong>{result.imported}</strong> | Пропущено: <strong>{result.skipped}</strong> | Ошибок: <strong>{result.errors}</strong>
                {result.total !== undefined && ` | Всего найдено: <strong>${result.total}</strong>`}
              </Typography>
            )}
          </Alert>
        )}

        {preview && (
          <Dialog 
            open={previewOpen} 
            onClose={() => setPreviewOpen(false)} 
            maxWidth="lg" 
            fullWidth
            PaperProps={{
              sx: {
                backgroundColor: '#1e1e1e',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 2,
              },
            }}
          >
            <DialogTitle sx={{ 
              color: '#90caf9',
              fontWeight: 600,
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              pb: 2,
            }}>
              Предпросмотр данных ({preview.total_found} найдено)
            </DialogTitle>
            <DialogContent sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ mb: 2, color: 'rgba(255, 255, 255, 0.7)' }}>
                Показано {preview.preview_count} из {preview.total_found} записей
              </Typography>
              <Box sx={{ maxHeight: 400, overflow: 'auto', borderRadius: 1 }}>
                <table style={{ 
                  width: '100%', 
                  borderCollapse: 'collapse',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                }}>
                  <thead>
                    <tr style={{ 
                      backgroundColor: 'rgba(144, 202, 249, 0.1)', 
                      position: 'sticky', 
                      top: 0,
                    }}>
                      {preview.columns.map((col) => (
                        <th key={col} style={{ 
                          padding: '12px', 
                          border: '1px solid rgba(255, 255, 255, 0.1)', 
                          textAlign: 'left',
                          color: '#90caf9',
                          fontWeight: 600,
                        }}>
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview.map((item, idx) => (
                      <tr 
                        key={idx}
                        style={{
                          backgroundColor: idx % 2 === 0 
                            ? 'rgba(255, 255, 255, 0.02)' 
                            : 'rgba(255, 255, 255, 0.05)',
                        }}
                      >
                        {preview.columns.map((col) => (
                          <td key={col} style={{ 
                            padding: '10px', 
                            border: '1px solid rgba(255, 255, 255, 0.05)',
                            color: 'rgba(255, 255, 255, 0.9)',
                          }}>
                            {item[col] ? String(item[col]).substring(0, 50) : '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            </DialogContent>
            <DialogActions sx={{ 
              p: 2, 
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              gap: 1,
            }}>
              <Button 
                onClick={() => setPreviewOpen(false)}
                sx={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                Закрыть
              </Button>
              <Button 
                onClick={handleImport} 
                variant="contained" 
                disabled={loading}
                sx={{
                  background: 'linear-gradient(135deg, #90caf9 0%, #42a5f5 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #64b5f6 0%, #1976d2 100%)',
                  },
                  '&:disabled': {
                    background: 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                Импортировать все
              </Button>
            </DialogActions>
          </Dialog>
        )}
      </Box>
    </Paper>
  );
}
