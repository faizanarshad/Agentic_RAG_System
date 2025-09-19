# 🎨 RAG System Frontend

A clean, modern React frontend for the Agentic RAG System.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── App.tsx          # Main application component
│   ├── main.tsx         # Application entry point
│   ├── index.css        # Global styles
│   └── assets/          # Static assets
├── public/              # Public assets
├── package.json         # Dependencies and scripts
└── README.md           # This file
```

## 🎯 Features

- **Clean Interface**: Simple, professional design
- **Responsive Layout**: Works on all device sizes
- **Real-time Chat**: Interactive conversation interface
- **File Upload**: Drag-and-drop PDF upload
- **Status Monitoring**: System health dashboard
- **TypeScript**: Type-safe development

## 🛠️ Development

The frontend is built with:
- **React 19** - Modern React with latest features
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **Custom CSS** - Clean, maintainable styles

## 🔗 API Integration

The frontend connects to the backend API at `http://localhost:8000`:

- **Chat**: `POST /chat/` - Send queries and get responses
- **File Upload**: `POST /files/add_file` - Upload PDF documents
- **Health Check**: `GET /health` - Check system status

## 📱 Responsive Design

The interface adapts to different screen sizes:
- **Desktop**: Full-featured layout with sidebar
- **Tablet**: Optimized for touch interaction
- **Mobile**: Compact, mobile-friendly design

## 🎨 Styling

Uses custom CSS with:
- Clean, modern design
- Consistent color scheme
- Smooth animations
- Accessible contrast ratios

## 🚀 Deployment

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

The built files will be in the `dist/` directory, ready for deployment to any static hosting service.
