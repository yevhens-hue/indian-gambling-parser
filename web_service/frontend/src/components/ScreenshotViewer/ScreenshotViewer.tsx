/**
 * Компонент для просмотра скриншотов
 */
import { Dialog, DialogTitle, DialogContent, IconButton, Box } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { getScreenshotUrl } from '../../services/api';

interface ScreenshotViewerProps {
  open: boolean;
  onClose: () => void;
  screenshotPath: string | null | undefined;
  providerName?: string;
}

export function ScreenshotViewer({ open, onClose, screenshotPath, providerName }: ScreenshotViewerProps) {
  const screenshotUrl = getScreenshotUrl(screenshotPath);

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>📷 Скриншот {providerName ? `- ${providerName}` : ''}</span>
          <IconButton 
            onClick={onClose} 
            size="small"
            sx={{
              color: 'rgba(255, 255, 255, 0.7)',
              '&:hover': {
                backgroundColor: 'rgba(239, 83, 80, 0.2)',
                color: '#ef5350',
              },
            }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent sx={{ mt: 2, backgroundColor: 'rgba(255, 255, 255, 0.02)' }}>
        {screenshotUrl ? (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            minHeight: 400,
            borderRadius: 2,
            overflow: 'hidden',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}>
            <img
              src={screenshotUrl}
              alt="Screenshot"
              style={{ 
                maxWidth: '100%', 
                height: 'auto',
                borderRadius: 8,
              }}
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzFlMWUxZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC43KSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIGltYWdlPC90ZXh0Pjwvc3ZnPg==';
              }}
            />
          </Box>
        ) : (
          <Box sx={{ 
            textAlign: 'center', 
            py: 4,
            color: 'rgba(255, 255, 255, 0.7)',
          }}>
            ⚠️ Скриншот не доступен
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
}
