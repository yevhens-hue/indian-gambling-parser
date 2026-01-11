/**
 * Основной компонент таблицы данных
 */
import { useState, useMemo } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef, GridPaginationModel, GridSortModel } from '@mui/x-data-grid';
import { Box, Chip, IconButton, Tooltip } from '@mui/material';
import ImageIcon from '@mui/icons-material/Image';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import type { Provider } from '../../services/api';
import { ScreenshotViewer } from '../ScreenshotViewer/ScreenshotViewer';

interface DataTableProps {
  providers: Provider[];
  total: number;
  loading: boolean;
  pagination: GridPaginationModel;
  onPaginationChange: (model: GridPaginationModel) => void;
  sortModel: GridSortModel;
  onSortModelChange: (model: GridSortModel) => void;
  onRowUpdate?: (id: number, field: string, value: any) => void;
}

export function DataTable({
  providers,
  total,
  loading,
  pagination,
  onPaginationChange,
  sortModel,
  onSortModelChange,
  onRowUpdate,
}: DataTableProps) {
  const [selectedScreenshot, setSelectedScreenshot] = useState<{
    path: string | null;
    name?: string;
  } | null>(null);

  const columns: GridColDef<Provider>[] = useMemo(
    () => [
      {
        field: 'merchant',
        headerName: 'Merchant',
        width: 120,
        editable: !!onRowUpdate,
      },
      {
        field: 'merchant_domain',
        headerName: 'Merchant Domain',
        width: 200,
      },
      {
        field: 'provider_domain',
        headerName: 'Provider Domain',
        width: 250,
      },
      {
        field: 'provider_name',
        headerName: 'Provider Name',
        width: 200,
        editable: !!onRowUpdate,
      },
      {
        field: 'account_type',
        headerName: 'Account Type',
        width: 130,
        renderCell: (params) => (
          <Chip 
            label={params.value || 'N/A'} 
            size="small" 
            variant="outlined"
            sx={{
              borderColor: 'rgba(144, 202, 249, 0.3)',
              color: '#90caf9',
              fontWeight: 500,
              '&:hover': {
                borderColor: '#90caf9',
                background: 'rgba(144, 202, 249, 0.1)',
              },
            }}
          />
        ),
      },
      {
        field: 'payment_method',
        headerName: 'Payment Method',
        width: 150,
      },
      {
        field: 'screenshot_path',
        headerName: 'Screenshot',
        width: 120,
        sortable: false,
        renderCell: (params) => {
          if (!params.value) return null;
          return (
            <Tooltip title="Просмотр скриншота">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedScreenshot({
                    path: params.value,
                    name: params.row.provider_name || undefined,
                  });
                }}
              >
                <ImageIcon />
              </IconButton>
            </Tooltip>
          );
        },
      },
      {
        field: 'final_url',
        headerName: 'URLs',
        width: 150,
        sortable: false,
        renderCell: (params) => {
          const urls = [
            { label: 'Final', url: params.row.final_url },
            { label: 'Entry', url: params.row.provider_entry_url },
            { label: 'Cashier', url: params.row.cashier_url },
          ].filter((item) => item.url);

          if (urls.length === 0) return null;

          return (
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {urls.map((item) => (
                <Tooltip key={item.label} title={item.url}>
                  <IconButton
                    size="small"
                    href={item.url!}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <OpenInNewIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              ))}
            </Box>
          );
        },
      },
      {
        field: 'is_iframe',
        headerName: 'Iframe',
        width: 80,
        type: 'boolean',
      },
      {
        field: 'requires_otp',
        headerName: 'OTP',
        width: 80,
        type: 'boolean',
      },
      {
        field: 'blocked_by_geo',
        headerName: 'Blocked',
        width: 100,
        type: 'boolean',
      },
      {
        field: 'captcha_present',
        headerName: 'Captcha',
        width: 100,
        type: 'boolean',
      },
      {
        field: 'detected_in',
        headerName: 'Detected In',
        width: 150,
      },
      {
        field: 'timestamp_utc',
        headerName: 'Timestamp',
        width: 180,
        valueGetter: (value) => {
          if (!value) return '';
          try {
            return new Date(value).toLocaleString('ru-RU');
          } catch {
            return value;
          }
        },
      },
    ],
    [onRowUpdate]
  );

  const handleCellEditCommit = (params: any) => {
    if (onRowUpdate) {
      onRowUpdate(params.id, params.field, params.value);
    }
  };

  return (
    <>
      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={providers}
          columns={columns}
          loading={loading}
          paginationMode="server"
          sortingMode="server"
          rowCount={total}
          paginationModel={pagination}
          onPaginationModelChange={onPaginationChange}
          sortModel={sortModel}
          onSortModelChange={onSortModelChange}
          pageSizeOptions={[25, 50, 100, 200]}
          disableRowSelectionOnClick
          onCellEditStop={handleCellEditCommit}
          // Оптимизация производительности
          disableColumnMenu={false}
          disableDensitySelector
          disableVirtualization={false} // Включена виртуализация (по умолчанию)
          rowHeight={52}
          sx={{
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            '& .MuiDataGrid-cell': {
              borderColor: 'rgba(255, 255, 255, 0.05)',
              color: 'rgba(255, 255, 255, 0.9)',
            },
            '& .MuiDataGrid-cell:focus': {
              outline: 'none',
            },
            '& .MuiDataGrid-cell:focus-within': {
              outline: 'none',
            },
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              borderBottom: '2px solid rgba(144, 202, 249, 0.2)',
              color: '#90caf9',
              fontWeight: 600,
            },
            '& .MuiDataGrid-columnHeader:focus': {
              outline: 'none',
            },
            '& .MuiDataGrid-row': {
              '&:hover': {
                backgroundColor: 'rgba(144, 202, 249, 0.08)',
              },
              '&.Mui-selected': {
                backgroundColor: 'rgba(144, 202, 249, 0.15)',
                '&:hover': {
                  backgroundColor: 'rgba(144, 202, 249, 0.2)',
                },
              },
            },
            '& .MuiDataGrid-footerContainer': {
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
            },
            '& .MuiDataGrid-toolbarContainer': {
              padding: '8px',
            },
            '& .MuiDataGrid-virtualScroller': {
              overflowX: 'auto',
            },
            '& .MuiIconButton-root': {
              color: 'rgba(255, 255, 255, 0.7)',
              '&:hover': {
                backgroundColor: 'rgba(144, 202, 249, 0.1)',
                color: '#90caf9',
              },
            },
            '& .MuiDataGrid-menuIconButton': {
              color: 'rgba(255, 255, 255, 0.7)',
            },
            '& .MuiDataGrid-sortIcon': {
              color: 'rgba(255, 255, 255, 0.7)',
            },
          }}
        />
      </Box>

      <ScreenshotViewer
        open={!!selectedScreenshot}
        onClose={() => setSelectedScreenshot(null)}
        screenshotPath={selectedScreenshot?.path || null}
        providerName={selectedScreenshot?.name}
      />
    </>
  );
}
