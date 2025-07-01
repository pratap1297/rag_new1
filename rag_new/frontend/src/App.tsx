import { Routes, Route, Link } from 'react-router-dom';
import RagPage from './pages/RagPage';
import ConversationPage from './pages/ConversationPage';
import ChatPage from './pages/ChatPage';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AdminDashboardPage from './pages/AdminDashboardPage';

function App() {
  return (
    <div>
      {/* Navigation is now handled in LandingPage and dashboards */}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
        <Route path="/rag" element={<RagPage />} />
        <Route path="/conversation" element={<ConversationPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </div>
  );
}

export default App;
