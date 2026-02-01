import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Existing Leesburg brand colors
        'leesburg-yellow': '#f5d224',
        'leesburg-brown': '#3d332a',
        'leesburg-beige': '#f4f2ef',
        'leesburg-orange': '#f29021',
        'leesburg-blue': '#76b9db',

        // Chat redesign - semantic tokens
        'chat': {
          'canvas': '#FDFCFA',
          'surface': '#F7F5F2',
          'elevated': '#FFFFFF',
        },
        'bubble': {
          'user': '#4A6741',
          'user-text': '#FFFFFF',
          'assistant': '#F4F2EF',
          'assistant-text': '#3D332A',
        },
        'accent': {
          'primary': '#4A6741',
          'primary-hover': '#3D5636',
          'secondary': '#F5D224',
          'error': '#C45C4A',
          'success': '#5D8A5A',
        },
        'text': {
          'primary': '#2D2620',
          'secondary': '#6B635B',
          'muted': '#9C948B',
        },
        'voice': {
          'idle': '#4A6741',
          'recording': '#E85D4A',
          'processing': '#F5D224',
          'playing': '#76B9DB',
        },
      },
      fontFamily: {
        'heading': ['Nunito', 'system-ui', 'sans-serif'],
        'body': ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'bubble': '20px',
        'bubble-tail': '4px',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
        'pulse-ring': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.5', transform: 'scale(1.1)' },
        },
        'typing-dot': {
          '0%, 80%, 100%': { transform: 'translateY(0)' },
          '40%': { transform: 'translateY(-6px)' },
        },
        'message-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.3s ease-out',
        shimmer: 'shimmer 2s linear infinite',
        'pulse-ring': 'pulse-ring 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'typing-dot': 'typing-dot 1.4s infinite ease-in-out',
        'message-in': 'message-in 200ms ease-out',
      },
    },
  },
  plugins: [],
} satisfies Config
