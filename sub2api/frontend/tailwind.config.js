/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 主色调 - 科技蓝紫色系: 深蓝 → 电光蓝 → 霓虹紫
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a5f',
          950: '#0f1d3d'
        },
        // 辅助色 - 霓虹紫渐变
        accent: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
          950: '#2e1065'
        },
        // 深色模式 - 纯粹深色
        dark: {
          50: '#e5e7eb',
          100: '#d1d5db',
          200: '#9ca3af',
          300: '#6b7280',
          400: '#4b5563',
          500: '#374361',
          600: '#2d3a54',
          700: '#243047',
          800: '#1a1f36',
          900: '#111827',
          950: '#0a0e1a'
        }
      },
      fontFamily: {
        sans: [
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'PingFang SC',
          'Hiragino Sans GB',
          'Microsoft YaHei',
          'sans-serif'
        ],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace']
      },
      boxShadow: {
        glass: '0 8px 32px rgba(59, 130, 246, 0.08)',
        'glass-sm': '0 4px 16px rgba(59, 130, 246, 0.06)',
        glow: '0 0 20px rgba(59, 130, 246, 0.35), 0 0 40px rgba(139, 92, 246, 0.15)',
        'glow-lg': '0 0 40px rgba(59, 130, 246, 0.45), 0 0 80px rgba(139, 92, 246, 0.2)',
        card: '0 1px 3px rgba(0, 0, 0, 0.08), 0 0 1px rgba(59, 130, 246, 0.1)',
        'card-hover': '0 10px 40px rgba(0, 0, 0, 0.15), 0 0 20px rgba(59, 130, 246, 0.12)',
        'inner-glow': 'inset 0 1px 0 rgba(139, 92, 246, 0.12)',
        'border-glow': '0 0 6px rgba(59, 130, 246, 0.3)'
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-primary': 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
        'gradient-dark': 'linear-gradient(135deg, #0a0e1a 0%, #111827 100%)',
        'gradient-glass':
          'linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(139,92,246,0.05) 100%)',
        'mesh-gradient':
          'radial-gradient(at 40% 20%, rgba(59, 130, 246, 0.1) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(139, 92, 246, 0.08) 0px, transparent 50%), radial-gradient(at 0% 50%, rgba(59, 130, 246, 0.06) 0px, transparent 50%)',
        'grid-pattern':
          'linear-gradient(rgba(59,130,246,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.04) 1px, transparent 1px)'
      },
      backgroundSize: {
        'grid-sm': '40px 40px',
        'grid-md': '64px 64px'
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        shimmer: 'shimmer 2s linear infinite',
        glow: 'glow 2s ease-in-out infinite alternate',
        'scanline': 'scanline 8s linear infinite',
        'border-flow': 'borderFlow 3s linear infinite',
        'pulse-breath': 'pulseBreath 4s ease-in-out infinite'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' }
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.35)' },
          '100%': { boxShadow: '0 0 40px rgba(139, 92, 246, 0.45)' }
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' }
        },
        borderFlow: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' }
        },
        pulseBreath: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' }
        }
      },
      backdropBlur: {
        xs: '2px'
      },
      borderRadius: {
        '4xl': '2rem'
      }
    }
  },
  plugins: []
}
