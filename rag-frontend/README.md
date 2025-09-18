# Agentic RAG System - Frontend

A modern, state-of-the-art React frontend for the Agentic RAG System built with Vite, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Modern Chat Interface**: Real-time chat with the RAG system
- **Drag & Drop File Upload**: Easy PDF document upload with progress indicators
- **System Status Monitoring**: Real-time health checks for all components
- **Responsive Design**: Mobile-first design that works on all devices
- **Beautiful UI**: Built with Tailwind CSS and modern design patterns

## 🛠️ Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Radix UI** for accessible components
- **Class Variance Authority** for component variants

## 🏃‍♂️ Quick Start

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open in browser**:
   Navigate to `http://localhost:5173`

## 📱 Features Overview

### Chat Interface
- Real-time messaging with the RAG system
- Message history with timestamps
- Context source indicators
- Loading states and error handling

### File Upload
- Drag and drop PDF files
- Upload progress tracking
- File validation and error handling
- Chunk count display

### Status Panel
- Real-time system health monitoring
- Component status indicators
- Automatic refresh every 30 seconds
- Manual refresh capability

## 🎨 Design System

The frontend uses a modern design system with:
- **Color Palette**: Carefully selected colors for light and dark themes
- **Typography**: Clean, readable fonts with proper hierarchy
- **Spacing**: Consistent spacing using Tailwind's spacing scale
- **Components**: Reusable UI components with variants
- **Animations**: Smooth transitions and micro-interactions

## 🔧 Development

### Project Structure
```
src/
├── components/          # React components
│   ├── ui/             # Reusable UI components
│   ├── ChatInterface.tsx
│   ├── FileUpload.tsx
│   └── StatusPanel.tsx
├── lib/                # Utilities and API client
│   ├── api.ts          # API client for backend communication
│   └── utils.ts        # Utility functions
├── App.tsx             # Main application component
└── main.tsx            # Application entry point
```

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🌐 API Integration

The frontend communicates with the FastAPI backend running on `http://localhost:8000`:

- **Chat**: `POST /chat/` - Send messages to the RAG system
- **File Upload**: `POST /files/add_file` - Upload PDF documents
- **Health Check**: `GET /health` - Check system status
- **Files Health**: `GET /files/health` - Check component health

## 📱 Responsive Design

The interface is fully responsive and works on:
- Desktop (1024px+)
- Tablet (768px - 1023px)
- Mobile (320px - 767px)

## 🎯 Future Enhancements

- Document management dashboard
- Advanced search and filtering
- User authentication
- Dark/light theme toggle
- Real-time notifications
- Export chat history
- Advanced file management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Agentic RAG System and follows the same license terms.