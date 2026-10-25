import React from 'react';
import { MotionConfig, AnimatePresence, motion } from 'framer-motion';
import { useApp } from './context/AppContext';
import { Sidebar } from './components/Sidebar';
import { AgentGraphPanel } from './components/AgentGraphPanel';
import { NewChatModal } from './components/NewChatModal';
import { ChatWorkspace } from './pages/ChatWorkspace';
import { KnowledgePage } from './pages/KnowledgePage';
import { MemoryPage } from './pages/MemoryPage';
import { WorkflowsPage } from './pages/WorkflowsPage';
import { ToolsPage } from './pages/ToolsPage';
import { SettingsPage } from './pages/SettingsPage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage, RegisterPage } from './pages/AuthPages';
import { pageVariants } from './lib/motion';

export const App: React.FC = () => {
  const { currentPage, isAuthenticated, theme, reducedMotion, fontSize } = useApp();

  if (!isAuthenticated) {
    if (currentPage === 'register') {
      return <RegisterPage />;
    }
    return <LoginPage />;
  }

  const renderActivePage = () => {
    switch (currentPage) {
      case 'chat':
        return <ChatWorkspace />;
      case 'knowledge':
        return <KnowledgePage />;
      case 'memory':
        return <MemoryPage />;
      case 'workflows':
        return <WorkflowsPage />;
      case 'tools':
        return <ToolsPage />;
      case 'settings':
        return <SettingsPage />;
      case 'dashboard':
        return <DashboardPage />;
      default:
        return <ChatWorkspace />;
    }
  };

  const getFontSizeClass = () => {
    if (fontSize === 'small') return 'text-[13px]';
    if (fontSize === 'large') return 'text-[16px]';
    return 'text-[14px]';
  };

  return (
    <MotionConfig reducedMotion={reducedMotion ? 'always' : 'user'}>
      <div
        data-theme={theme}
        className={`min-h-screen flex bg-[#18110c] text-[#fbf8f2] ${getFontSizeClass()} ${
          reducedMotion ? 'motion-reduce' : ''
        }`}
      >
        {/* Persistent Left Sidebar */}
        <Sidebar />

        {/* Main Center Workspace Area with Animated Page Transition */}
        <main className="flex-1 flex flex-col h-screen overflow-hidden min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPage}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="flex-1 flex flex-col h-full overflow-hidden"
            >
              {renderActivePage()}
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Contextual Right Agent Graph Panel (visible on Chat) */}
        {currentPage === 'chat' && <AgentGraphPanel />}

        {/* Global New Chat Setup Modal */}
        <NewChatModal />
      </div>
    </MotionConfig>
  );
};

export default App;
