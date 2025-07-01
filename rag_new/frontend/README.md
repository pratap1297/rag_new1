# AI Force Intelligent Support Agent - Frontend

A modern React-based frontend for the AI Force Intelligent Support Agent, providing an intuitive interface for AI-powered document processing and knowledge management.

## Features

- **Professional UI/UX**: Modern, responsive design with Tailwind CSS
- **Authentication System**: User and admin login with local storage
- **Role-Based Access**: Separate dashboards for users and administrators
- **Document Management**: Upload, process, and search through documents
- **AI-Powered Search**: Intelligent document search and retrieval
- **Real-time Chat**: Interactive conversations with AI agents
- **Analytics Dashboard**: System performance and usage metrics

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Radix UI** for accessible components
- **Lucide React** for icons
- **Axios** for API communication

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Clone the repository
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── ui/             # Radix UI components
├── pages/              # Page components
│   ├── LandingPage.tsx # Landing page
│   ├── LoginPage.tsx   # Authentication page
│   ├── DashboardPage.tsx # User dashboard
│   └── AdminDashboardPage.tsx # Admin dashboard
├── utils/              # Utility functions
│   ├── auth.ts         # Authentication utilities
│   └── cn.ts           # Class name utilities
├── App.tsx             # Main app component
└── main.tsx            # App entry point
```

## Authentication

The app includes a mock authentication system with the following demo credentials:

- **User Account**: `user@example.com` / `user123`
- **Admin Account**: `admin@example.com` / `admin123`

Authentication state is stored in localStorage for development purposes.

## Features Overview

### Landing Page
- Professional marketing page
- Feature showcase
- Call-to-action sections
- Responsive design

### Login System
- User and admin authentication
- Quick login buttons
- Form validation
- Error handling

### User Dashboard
- Quick access to AI features
- Recent activity tracking
- System statistics
- Document management

### Admin Dashboard
- System monitoring
- User management
- Performance metrics
- Administrative tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the AI Force Intelligent Support Agent system.

## Support

For support and questions, please contact the development team.
