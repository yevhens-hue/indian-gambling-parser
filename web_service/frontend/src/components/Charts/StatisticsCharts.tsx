/**
 * Компонент для отображения графиков статистики
 */
import { Box, Paper, Typography } from '@mui/material';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { Statistics } from '../../services/api';

interface StatisticsChartsProps {
  statistics: Statistics;
}

// Цвета для темной темы
const COLORS = ['#90caf9', '#ce93d8', '#66bb6a', '#ffa726', '#ef5350', '#42a5f5', '#ab47bc', '#26a69a'];

export function StatisticsCharts({ statistics }: StatisticsChartsProps) {
  // Подготовка данных для графиков
  const merchantsData = Object.entries(statistics.merchants).map(([name, value]) => ({
    name,
    value,
  }));

  const accountTypesData = Object.entries(statistics.account_types).map(([name, value]) => ({
    name,
    value,
  }));

  const paymentMethodsData = Object.entries(statistics.payment_methods).map(([name, value]) => ({
    name,
    value,
  }));

  // Топ 10 провайдеров
  const topProviders = Object.entries(statistics.providers)
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 10)
    .map(([name, value]) => ({
      name: name.length > 20 ? `${name.substring(0, 20)}...` : name,
      fullName: name,
      value,
    }));

  return (
    <Box sx={{ mb: 3 }}>
      <Typography 
        variant="h6" 
        gutterBottom
        sx={{ 
          fontWeight: 600,
          mb: 3,
          background: 'linear-gradient(135deg, #90caf9 0%, #ce93d8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}
      >
        📊 Визуализация статистики
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
        {/* График по мерчантам */}
        <Paper sx={{ 
          p: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 2,
        }}>
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#90caf9' }}>
            Распределение по мерчантам
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={merchantsData}>
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
              <Bar dataKey="value" fill="#90caf9" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        {/* Круговая диаграмма по типам аккаунтов */}
        <Paper sx={{ 
          p: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 2,
        }}>
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#ce93d8' }}>
            Распределение по типам аккаунтов
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={accountTypesData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#ce93d8"
                dataKey="value"
              >
                {accountTypesData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e1e1e', 
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 8,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Paper>

        {/* График по методам оплаты */}
        <Paper sx={{ 
          p: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 2,
        }}>
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#66bb6a' }}>
            Методы оплаты
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={paymentMethodsData}>
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
              <Bar dataKey="value" fill="#66bb6a" radius={[8, 8, 0, 0]} />
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
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2, color: '#ffa726' }}>
            Топ 10 провайдеров
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topProviders} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
              <XAxis type="number" stroke="rgba(255, 255, 255, 0.7)" />
              <YAxis dataKey="name" type="category" width={100} stroke="rgba(255, 255, 255, 0.7)" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e1e1e', 
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="value" fill="#ffa726" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Box>
    </Box>
  );
}
