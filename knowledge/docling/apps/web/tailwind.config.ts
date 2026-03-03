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

        // Chat palette — matched to leesburganimalpark.com
        'chat': {
          'canvas': '#f7f7f7',
          'surface': '#f4f2ef',
          'elevated': '#FFFFFF',
        },
        'bubble': {
          'user': '#5fbf77',
          'user-text': '#FFFFFF',
          'assistant': '#f4f2ef',
          'assistant-text': '#3d332a',
        },
        'accent': {
          'primary': '#5fbf77',
          'primary-hover': '#4da963',
          'secondary': '#f29021',
          'teal': '#5fbf77',
          'teal-hover': '#4da963',
          'error': '#E85D4A',
          'success': '#5fbf77',
        },
        'text': {
          'primary': '#3d332a',
          'secondary': '#5a4d42',
          'muted': '#9b8d82',
        },
        'voice': {
          'idle': '#5fbf77',
          'recording': '#E85D4A',
          'processing': '#f29021',
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
