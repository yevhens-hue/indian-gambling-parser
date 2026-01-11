import { useState, useMemo, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { Container, Typography, Box, Paper, Card, CardContent, CircularProgress } from '@mui/material';
import type { GridPaginationModel, GridSortModel } from '@mui/x-data-grid';
import { useProviders, useUpdateProvider, useStatistics } from './hooks/useProviders';
import type { ProvidersQueryParams } from './services/api';
import type { Provider } from './services/api';
import { DataTable } from './components/DataTable/DataTable';
import { Filters } from './components/Filters/Filters';
import { ExportButtons } from './components/ExportButtons/ExportButtons';
import { StatisticsCharts } from './components/Charts/StatisticsCharts';
import { ImportFromSheets } from './components/ImportData/ImportFromSheets';
import { Dashboard } from './components/Analytics/Dashboard';
import { useWebSocket } from './hooks/useWebSocket';
import { Chip, Tabs, Tab } from '@mui/material';
import { useUrlFilters, type FilterState } from './hooks/useUrlFilters';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
      light: '#e3f2fd',
      dark: '#42a5f5',
    },
    secondary: {
      main: '#ce93d8',
      light: '#f3e5f5',
      dark: '#ab47bc',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
    },
    success: {
      main: '#66bb6a',
      light: '#81c784',
      dark: '#388e3c',
    },
    warning: {
      main: '#ffa726',
      light: '#ffb74d',
      dark: '#f57c00',
    },
    error: {
      main: '#ef5350',
      light: '#e57373',
      dark: '#c62828',
    },
    info: {
      main: '#42a5f5',
      light: '#64b5f6',
      dark: '#1976d2',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderRadius: 12,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 6px 25px rgba(0, 0, 0, 0.4)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderRadius: 12,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
  },
});

function AppContent() {
  const [activeTab, setActiveTab] = useState(0);
  
  // Используем URL фильтры
  const {
    filters: urlFilters,
    updateFilters: updateUrlFilters,
  } = useUrlFilters();

  // Конвертируем URL фильтры в ProvidersQueryParams
  const filters = useMemo<ProvidersQueryParams>(() => {
    return {
      merchant: urlFilters.merchant,
      provider_domain: urlFilters.providerDomain,
      account_type: urlFilters.accountType,
      payment_method: urlFilters.paymentMethod,
      search: urlFilters.search,
      skip: urlFilters.page !== undefined && urlFilters.limit !== undefined ? urlFilters.page * urlFilters.limit : 0,
      limit: urlFilters.limit ?? 50,
      sort_by: urlFilters.sortBy ?? 'timestamp_utc',
      sort_order: urlFilters.sortOrder ?? 'desc',
    };
  }, [urlFilters]);

  // Обновляем URL при изменении фильтров (из других источников)
  const setFilters = (newFilters: ProvidersQueryParams | ((prev: ProvidersQueryParams) => ProvidersQueryParams)) => {
    const updatedFilters = typeof newFilters === 'function' ? newFilters(filters) : newFilters;
    
    const urlState: Partial<FilterState> = {
      merchant: updatedFilters.merchant,
      providerDomain: updatedFilters.provider_domain,
      accountType: updatedFilters.account_type,
      paymentMethod: updatedFilters.payment_method,
      search: updatedFilters.search,
      page: updatedFilters.skip !== undefined && updatedFilters.limit !== undefined && updatedFilters.limit > 0
        ? Math.floor(updatedFilters.skip / updatedFilters.limit)
        : undefined,
      limit: updatedFilters.limit,
      sortBy: updatedFilters.sort_by,
      sortOrder: updatedFilters.sort_order,
    };
    
    updateUrlFilters(urlState);
  };

  const [pagination, setPagination] = useState<GridPaginationModel>({
    page: urlFilters.page ?? 0,
    pageSize: urlFilters.limit ?? 50,
  });

  const [sortModel, setSortModel] = useState<GridSortModel>([
    {
      field: urlFilters.sortBy ?? 'timestamp_utc',
      sort: urlFilters.sortOrder ?? 'desc',
    },
  ]);

  // Синхронизируем pagination с URL фильтрами при инициализации
  useEffect(() => {
    if (urlFilters.page !== undefined && urlFilters.limit !== undefined) {
      setPagination({
        page: urlFilters.page,
        pageSize: urlFilters.limit,
      });
    }
  }, [urlFilters.page, urlFilters.limit]);

  // Синхронизируем sortModel с URL фильтрами при инициализации
  useEffect(() => {
    if (urlFilters.sortBy) {
      setSortModel([
        {
          field: urlFilters.sortBy,
          sort: urlFilters.sortOrder ?? 'desc',
        },
      ]);
    }
  }, [urlFilters.sortBy, urlFilters.sortOrder]);

  const { data, isLoading, error } = useProviders(filters);
  const { data: statistics, error: statsError } = useStatistics();
  const updateMutation = useUpdateProvider();

  // WebSocket для real-time обновлений
  const { isConnected, lastUpdate } = useWebSocket();

  // Логирование ошибок
  useEffect(() => {
    if (error) {
      console.error('Error loading providers:', error);
    }
    if (statsError) {
      console.error('Error loading statistics:', statsError);
    }
  }, [error, statsError]);

  // Извлекаем уникальные значения для фильтров из данных
  const merchants = useMemo((): string[] => {
    if (!data?.items) return [];
    return Array.from(new Set(data.items.map((p: Provider) => p.merchant).filter(Boolean))) as string[];
  }, [data]);

  const accountTypes = useMemo((): string[] => {
    if (!data?.items) return [];
    return Array.from(new Set(data.items.map((p: Provider) => p.account_type).filter(Boolean))) as string[];
  }, [data]);

  const paymentMethods = useMemo((): string[] => {
    if (!data?.items) return [];
    return Array.from(new Set(data.items.map((p: Provider) => p.payment_method).filter(Boolean))) as string[];
  }, [data]);

  // Обновляем фильтры при изменении пагинации
  const handlePaginationChange = (model: GridPaginationModel) => {
    setPagination(model);
    updateUrlFilters({
      page: model.page,
      limit: model.pageSize,
    });
  };

  // Обновляем фильтры при изменении сортировки
  const handleSortModelChange = (model: GridSortModel) => {
    setSortModel(model);
    if (model.length > 0) {
      updateUrlFilters({
        sortBy: model[0].field,
        sortOrder: (model[0].sort || 'desc') as 'asc' | 'desc',
        page: 0, // Сбрасываем пагинацию при сортировке
      });
      setPagination((prev) => ({ ...prev, page: 0 }));
    }
  };

  // Обработка обновления ячейки
  const handleRowUpdate = (id: number, field: string, value: any) => {
    updateMutation.mutate({
      id,
      updates: { [field]: value },
    });
  };

  return (
        <Container maxWidth={false} sx={{ py: 3, background: 'transparent' }}>
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography 
                variant="h4" 
                component="h1" 
                gutterBottom
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #90caf9 0%, #ce93d8 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                📊 Providers Dashboard
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Управление данными провайдеров платежных систем
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
              <Chip
                label={isConnected ? '🟢 Real-time' : '🔴 Offline'}
                color={isConnected ? 'success' : 'error'}
                size="small"
                sx={{
                  fontWeight: 600,
                  boxShadow: isConnected 
                    ? '0 2px 8px rgba(102, 187, 106, 0.3)' 
                    : '0 2px 8px rgba(239, 83, 80, 0.3)',
                }}
              />
              {lastUpdate && (
                <Typography variant="caption" color="text.secondary" sx={{ opacity: 0.8 }}>
                  Обновлено: {lastUpdate.toLocaleTimeString()}
                </Typography>
              )}
            </Box>
          </Box>

          {/* Табы для переключения между данными и аналитикой */}
          <Paper sx={{ mb: 3, background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <Tabs 
              value={activeTab} 
              onChange={(_, newValue) => setActiveTab(newValue)}
              sx={{
                '& .MuiTab-root': {
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '0.95rem',
                  minHeight: 64,
                  color: 'rgba(255, 255, 255, 0.6)',
                  '&.Mui-selected': {
                    color: '#90caf9',
                  },
                },
                '& .MuiTabs-indicator': {
                  background: 'linear-gradient(90deg, #90caf9 0%, #ce93d8 100%)',
                  height: 3,
                  borderRadius: '3px 3px 0 0',
                },
              }}
            >
              <Tab label="📋 Данные" />
              <Tab label="📊 Analytics Dashboard" />
            </Tabs>
          </Paper>

          {/* Контент в зависимости от выбранной вкладки */}
          {activeTab === 1 ? (
            <Dashboard />
          ) : (
            <>
          {/* Статистика */}
          {statistics && (
            <>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, 
                gap: 2, 
                mb: 3 
              }}>
                <Card sx={{ 
                  background: 'linear-gradient(135deg, rgba(144, 202, 249, 0.15) 0%, rgba(66, 165, 245, 0.1) 100%)',
                  border: '1px solid rgba(144, 202, 249, 0.2)',
                }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                      Всего записей
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#90caf9' }}>
                      {statistics.total}
                    </Typography>
                  </CardContent>
                </Card>
                <Card sx={{ 
                  background: 'linear-gradient(135deg, rgba(206, 147, 216, 0.15) 0%, rgba(171, 71, 188, 0.1) 100%)',
                  border: '1px solid rgba(206, 147, 216, 0.2)',
                }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                      Мерчантов
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#ce93d8' }}>
                      {Object.keys(statistics.merchants).length}
                    </Typography>
                  </CardContent>
                </Card>
                <Card sx={{ 
                  background: 'linear-gradient(135deg, rgba(102, 187, 106, 0.15) 0%, rgba(56, 142, 60, 0.1) 100%)',
                  border: '1px solid rgba(102, 187, 106, 0.2)',
                }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                      Провайдеров
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#66bb6a' }}>
                      {Object.keys(statistics.providers).length}
                    </Typography>
                  </CardContent>
                </Card>
                <Card sx={{ 
                  background: 'linear-gradient(135deg, rgba(255, 167, 38, 0.15) 0%, rgba(245, 124, 0, 0.1) 100%)',
                  border: '1px solid rgba(255, 167, 38, 0.2)',
                }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                      Типов аккаунтов
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#ffa726' }}>
                      {Object.keys(statistics.account_types).length}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>

              {/* Графики статистики */}
              <StatisticsCharts statistics={statistics} />
            </>
          )}

          {/* Импорт данных из Google Sheets */}
          <ImportFromSheets />

          {/* Фильтры и экспорт */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Filters
                filters={filters}
                onFiltersChange={setFilters}
                merchants={merchants}
                accountTypes={accountTypes}
                paymentMethods={paymentMethods}
              />
            </Box>
            <Box sx={{ mt: 2 }}>
              <ExportButtons filters={filters} />
            </Box>
          </Box>

          {/* Таблица */}
          <Paper sx={{ 
            p: 3,
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}>
            {error && (
              <Box sx={{ 
                p: 3, 
                mb: 2, 
                bgcolor: 'rgba(239, 83, 80, 0.15)', 
                borderRadius: 2,
                border: '1px solid rgba(239, 83, 80, 0.3)',
              }}>
                <Typography variant="h6" sx={{ color: '#ef5350', fontWeight: 600 }} gutterBottom>
                  ❌ Ошибка загрузки данных
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.9)', mb: 1 }}>
                  {error instanceof Error ? error.message : 'Unknown error'}
                </Typography>
                <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'rgba(255, 255, 255, 0.7)' }}>
                  Проверьте, что backend запущен на http://localhost:8000
                </Typography>
              </Box>
            )}

            {!error && isLoading && !data ? (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                justifyContent: 'center', 
                alignItems: 'center', 
                height: 400, 
                gap: 2 
              }}>
                <CircularProgress sx={{ color: '#90caf9' }} />
                <Typography variant="body2" color="text.secondary" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                  Загрузка данных...
                </Typography>
              </Box>
            ) : !error && data && data.items && data.items.length > 0 ? (
              <>
                <DataTable
                  providers={data.items}
                  total={data.total || 0}
                  loading={isLoading}
                  pagination={pagination}
                  onPaginationChange={handlePaginationChange}
                  sortModel={sortModel}
                  onSortModelChange={handleSortModelChange}
                  onRowUpdate={handleRowUpdate}
                />
                <Box sx={{ mt: 2, textAlign: 'right' }}>
                  <Typography variant="caption" color="text.secondary">
                    Показано {data.items.length} из {data.total} записей
                  </Typography>
                </Box>
              </>
            ) : !error && data && data.items && data.items.length === 0 ? (
              <Box sx={{ 
                p: 4, 
                textAlign: 'center',
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                borderRadius: 2,
              }}>
                <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} gutterBottom>
                  📭 Нет данных
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)', mt: 1 }}>
                  В базе данных нет провайдеров. Запустите парсер для сбора данных.
                </Typography>
              </Box>
            ) : !error && !isLoading && !data ? (
              <Box sx={{ 
                p: 4, 
                textAlign: 'center',
                backgroundColor: 'rgba(255, 167, 38, 0.1)',
                borderRadius: 2,
                border: '1px solid rgba(255, 167, 38, 0.3)',
              }}>
                <Typography variant="h6" sx={{ color: '#ffa726', fontWeight: 600 }} gutterBottom>
                  ⚠️ Не удалось загрузить данные
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)', mt: 1 }}>
                  Проверьте подключение к backend API
                </Typography>
              </Box>
            ) : null}
          </Paper>
            </>
          )}
        </Container>
  );
}

function App() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppContent />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
