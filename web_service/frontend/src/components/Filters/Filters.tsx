/**
 * Компонент фильтров
 */
import { useState } from 'react';
import { Box, TextField, MenuItem, Paper, Typography, IconButton } from '@mui/material';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import type { ProvidersQueryParams } from '../../services/api';

interface FiltersProps {
  filters: ProvidersQueryParams;
  onFiltersChange: (filters: ProvidersQueryParams) => void;
  merchants?: string[];
  accountTypes?: string[];
  paymentMethods?: string[];
}

export function Filters({
  filters,
  onFiltersChange,
  merchants = [],
  accountTypes = [],
  paymentMethods = [],
}: FiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (key: keyof ProvidersQueryParams, value: string) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
      skip: 0, // Сбрасываем пагинацию при изменении фильтров
    });
  };

  const handleClearFilters = () => {
    onFiltersChange({
      skip: 0,
      limit: filters.limit || 50,
      sort_by: filters.sort_by || 'timestamp_utc',
      sort_order: filters.sort_order || 'desc',
    });
  };

  const hasActiveFilters =
    !!filters.merchant ||
    !!filters.account_type ||
    !!filters.payment_method ||
    !!filters.provider_domain ||
    !!filters.search;

  return (
    <Paper sx={{ 
      p: 2.5, 
      mb: 2,
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: 2,
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: isExpanded ? 2 : 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <FilterListIcon sx={{ color: '#90caf9' }} />
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#90caf9' }}>
            Фильтры
          </Typography>
          {hasActiveFilters && (
            <Typography variant="caption" sx={{ 
              ml: 1, 
              color: '#66bb6a',
              fontWeight: 600,
              px: 1,
              py: 0.5,
              borderRadius: 1,
              bgcolor: 'rgba(102, 187, 106, 0.1)',
            }}>
              активны
            </Typography>
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {hasActiveFilters && (
            <IconButton 
              size="small" 
              onClick={handleClearFilters} 
              title="Очистить фильтры"
              sx={{
                color: 'rgba(255, 255, 255, 0.7)',
                '&:hover': {
                  backgroundColor: 'rgba(239, 83, 80, 0.2)',
                  color: '#ef5350',
                },
              }}
            >
              <ClearIcon />
            </IconButton>
          )}
          <IconButton 
            size="small" 
            onClick={() => setIsExpanded(!isExpanded)}
            sx={{
              color: 'rgba(255, 255, 255, 0.7)',
              '&:hover': {
                backgroundColor: 'rgba(144, 202, 249, 0.2)',
                color: '#90caf9',
              },
            }}
          >
            {isExpanded ? '▼' : '▶'}
          </IconButton>
        </Box>
      </Box>

      {isExpanded && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 2 }}>
          <TextField
            label="Поиск"
            value={filters.search || ''}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            placeholder="Поиск по всем полям..."
            fullWidth
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
            select
            label="Merchant"
            value={filters.merchant || ''}
            onChange={(e) => handleFilterChange('merchant', e.target.value)}
            fullWidth
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
          >
            <MenuItem value="">Все</MenuItem>
            {merchants.map((merchant) => (
              <MenuItem key={merchant} value={merchant}>
                {merchant}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Account Type"
            value={filters.account_type || ''}
            onChange={(e) => handleFilterChange('account_type', e.target.value)}
            fullWidth
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
          >
            <MenuItem value="">Все</MenuItem>
            {accountTypes.map((type) => (
              <MenuItem key={type} value={type}>
                {type}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Payment Method"
            value={filters.payment_method || ''}
            onChange={(e) => handleFilterChange('payment_method', e.target.value)}
            fullWidth
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
          >
            <MenuItem value="">Все</MenuItem>
            {paymentMethods.map((method) => (
              <MenuItem key={method} value={method}>
                {method}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="Provider Domain"
            value={filters.provider_domain || ''}
            onChange={(e) => handleFilterChange('provider_domain', e.target.value)}
            placeholder="Фильтр по домену..."
            fullWidth
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
        </Box>
      )}
    </Paper>
  );
}
