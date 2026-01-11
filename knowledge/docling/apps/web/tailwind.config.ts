import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'leesburg-yellow': '#f5d224',
        'leesburg-brown': '#3d332a',
        'leesburg-beige': '#f4f2ef',
        'leesburg-orange': '#f29021',
        'leesburg-blue': '#76b9db',
      },
    },
  },
  plugins: [],
} satisfies Config
