import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Leesburg brand colors (kept for reference)
        'leesburg-yellow': '#f5d224',
        'leesburg-brown': '#3d332a',
        'leesburg-beige': '#f4f2ef',
        'leesburg-orange': '#f29021',
        'leesburg-blue': '#76b9db',

        // Chat redesign - African Zoo / Warm Vibrant palette
        'chat': {
          'canvas': '#FFFAF5',
          'surface': '#FFF3E8',
          'elevated': '#FFFFFF',
        },
        'bubble': {
          'user': '#E07A2F',
          'user-text': '#FFFFFF',
          'assistant': '#FFF3E8',
          'assistant-text': '#2D1810',
        },
        'accent': {
          'primary': '#E07A2F',
          'primary-hover': '#C96821',
          'secondary': '#F5B731',
          'teal': '#2A9D8F',
          'teal-hover': '#238578',
          'error': '#E85D4A',
          'success': '#2A9D8F',
        },
        'text': {
          'primary': '#2D1810',
          'secondary': '#7A5C4F',
          'muted': '#B49A8C',
        },
        'voice': {
          'idle': '#2A9D8F',
          'recording': '#E85D4A',
          'processing': '#F5B731',
          'playing': '#76B9DB',
        },
      },
      fontFamily: {
        'heading': ['"Baloo 2"', 'system-ui', 'sans-serif'],
        'body': ['"Comic Neue"', 'system-ui', 'sans-serif'],
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
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.3s ease-out',
        shimmer: 'shimmer 2s linear infinite',
        'pulse-ring': 'pulse-ring 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'typing-dot': 'typing-dot 1.4s infinite ease-in-out',
        'message-in': 'message-in 200ms ease-out',
        'float': 'float 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
} satisfies Config
