/**
 * Dashboard с ключевыми метриками и аналитикой
 */
import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import axios from 'axios';
import { useQuery } from '@tanstack/react-query';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import PeopleIcon from '@mui/icons-material/People';
import BusinessIcon from '@mui/icons-material/Business';
import PaymentIcon from '@mui/icons-material/Payment';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface DashboardMetrics {
  total_providers: number;
  new_today: number;
  new_last_7_days: number;
  active_merchants: number;
  top_merchants: Array<{ name: string; count: number }>;
  top_providers: Array<{ name: string; count: number }>;
  trends: Array<{ date: string; count: number }>;
  account_types_distribution: Record<string, number>;
  payment_methods_distribution: Record<string, number>;
}

// interface TrendData {
//   period: string;
//   group_by: string;
//   trends: Array<{
//     period: string;
//     total: number;
//     by_merchant: Record<string, number>;
//     by_account_type: Record<string, number>;
//     by_payment_method: Record<string, number>;
//   }>;
// }

export function Dashboard() {
  // const [period, setPeriod] = useState('7d');
  const [days, setDays] = useState(7);

  // Загрузка метрик dashboard
  const { data: metrics, isLoading: metricsLoading } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard-metrics', days],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/analytics/dashboard`, {
        params: { days },
      });
      return response.data;
    },
    refetchInterval: 30000, // Обновление каждые 30 секунд
  });

  // Загрузка трендов (для будущего использования)
  // const { data: trends, isLoading: trendsLoading } = useQuery<TrendData>({
  //   queryKey: ['analytics-trends', period],
  //   queryFn: async () => {
  //     const response = await axios.get(`${API_URL}/analytics/trends`, {
  //       params: { period, group_by: 'day' },
  //     });
  //     return response.data;
  //   },
  //   refetchInterval: 60000,
  // });

  if (metricsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!metrics) {
    return <Alert severity="warning">Не удалось загрузить данные</Alert>;
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography 
        variant="h4" 
        gutterBottom
        sx={{
          fontWeight: 700,
          mb: 3,
          background: 'linear-gradient(135deg, #90caf9 0%, #ce93d8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}
      >
        📊 Dashboard Analytics
      </Typography>

      {/* Ключевые метрики */}
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
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                  Всего провайдеров
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#90caf9' }}>
                  {metrics.total_providers}
                </Typography>
              </Box>
              <PeopleIcon sx={{ fontSize: 48, color: '#90caf9', opacity: 0.8 }} />
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ 
          background: 'linear-gradient(135deg, rgba(102, 187, 106, 0.15) 0%, rgba(56, 142, 60, 0.1) 100%)',
          border: '1px solid rgba(102, 187, 106, 0.2)',
        }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                  Новых сегодня
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#66bb6a' }}>
                  {metrics.new_today}
                </Typography>
              </Box>
              <TrendingUpIcon sx={{ fontSize: 48, color: '#66bb6a', opacity: 0.8 }} />
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ 
          background: 'linear-gradient(135deg, rgba(66, 165, 245, 0.15) 0%, rgba(25, 118, 210, 0.1) 100%)',
          border: '1px solid rgba(66, 165, 245, 0.2)',
        }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                  За 7 дней
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#42a5f5' }}>
                  {metrics.new_last_7_days}
                </Typography>
              </Box>
              <BusinessIcon sx={{ fontSize: 48, color: '#42a5f5', opacity: 0.8 }} />
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ 
          background: 'linear-gradient(135deg, rgba(255, 167, 38, 0.15) 0%, rgba(245, 124, 0, 0.1) 100%)',
          border: '1px solid rgba(255, 167, 38, 0.2)',
        }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                  Активных merchants
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#ffa726' }}>
                  {metrics.active_merchants}
                </Typography>
              </Box>
              <PaymentIcon sx={{ fontSize: 48, color: '#ffa726', opacity: 0.8 }} />
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Настройки периода */}
      <Paper sx={{ 
        p: 2, 
        mb: 3,
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 2,
      }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontWeight: 500 }}>
            Настройки периода:
          </Typography>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>Дней для метрик</InputLabel>
            <Select 
              value={days} 
              onChange={(e) => setDays(Number(e.target.value))} 
              label="Дней для метрик"
              sx={{
                color: 'rgba(255, 255, 255, 0.9)',
                borderRadius: 2,
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(144, 202, 249, 0.5)',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#90caf9',
                },
                '& .MuiSvgIcon-root': {
                  color: 'rgba(255, 255, 255, 0.7)',
                },
              }}
              MenuProps={{
                PaperProps: {
                  sx: {
                    backgroundColor: '#1e1e1e',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    '& .MuiMenuItem-root': {
                      color: 'rgba(255, 255, 255, 0.9)',
                      '&:hover': {
                        backgroundColor: 'rgba(144, 202, 249, 0.1)',
                      },
                      '&.Mui-selected': {
                        backgroundColor: 'rgba(144, 202, 249, 0.2)',
                        color: '#90caf9',
                      },
                    },
                  },
                },
              }}
            >
              <MenuItem value={7}>7 дней</MenuItem>
              <MenuItem value={30}>30 дней</MenuItem>
              <MenuItem value={90}>90 дней</MenuItem>
              <MenuItem value={365}>Год</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
        gap: 2 
      }}>
        {/* График трендов */}
        <Box sx={{ gridColumn: { xs: '1', md: '1 / 3' } }}>
          <Paper sx={{ 
            p: 3,
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#90caf9' }}>
              📈 Тренды добавления провайдеров
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics.trends}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#90caf9" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#90caf9" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.7)" />
                <YAxis stroke="rgba(255, 255, 255, 0.7)" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e1e1e', 
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: 8,
                  }}
                />
                <Legend wrapperStyle={{ color: 'rgba(255, 255, 255, 0.7)' }} />
                <Area 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#90caf9" 
                  fillOpacity={1}
                  fill="url(#colorCount)" 
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Box>

        {/* Распределение по типам аккаунтов */}
        <Paper sx={{ 
          p: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 2,
        }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#ce93d8' }}>
            Типы аккаунтов
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={Object.entries(metrics.account_types_distribution).map(([name, value]) => ({
                name,
                value,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
              <XAxis dataKey="name" stroke="rgba(255, 255, 255, 0.7)" />
              <YAxis stroke="rgba(255, 255, 255, 0.7)" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e1e1e', 
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="value" fill="#ce93d8" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        {/* Топ merchants */}
        <Paper sx={{ 
          p: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 2,
        }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#90caf9' }}>
            🏆 Топ Merchants
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics.top_merchants}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
              <XAxis dataKey="name" stroke="rgba(255, 255, 255, 0.7)" />
              <YAxis stroke="rgba(255, 255, 255, 0.7)" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e1e1e', 
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 8,
                }}
              />
              <Legend wrapperStyle={{ color: 'rgba(255, 255, 255, 0.7)' }} />
              <Bar dataKey="count" fill="#90caf9" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        {/* Топ провайдеров */}
        <Paper sx={{ 
          p: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 2,
        }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#ffa726' }}>
            ⭐ Топ провайдеров
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics.top_providers}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
              <XAxis dataKey="name" stroke="rgba(255, 255, 255, 0.7)" />
              <YAxis stroke="rgba(255, 255, 255, 0.7)" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e1e1e', 
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 8,
                }}
              />
              <Legend wrapperStyle={{ color: 'rgba(255, 255, 255, 0.7)' }} />
              <Bar dataKey="count" fill="#ffa726" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        {/* Распределение по методам оплаты */}
        <Box sx={{ gridColumn: { xs: '1', md: '1 / 3' } }}>
          <Paper sx={{ 
            p: 3,
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#66bb6a' }}>
              💳 Методы оплаты
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart
                data={Object.entries(metrics.payment_methods_distribution).map(([name, value]) => ({
                  name,
                  value,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                <XAxis dataKey="name" stroke="rgba(255, 255, 255, 0.7)" />
                <YAxis stroke="rgba(255, 255, 255, 0.7)" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e1e1e', 
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="value" fill="#66bb6a" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}
