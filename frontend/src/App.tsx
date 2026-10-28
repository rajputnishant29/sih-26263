import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppShell } from './components/layout/AppShell';

import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { InstitutionsPage } from './pages/InstitutionsPage';
import { ProgrammeApprovalsPage } from './pages/ProgrammeApprovalsPage';
import { UploadWizardPage } from './pages/UploadWizardPage';
import { StudentRecordsPage } from './pages/StudentRecordsPage';
import { ExceptionsPage } from './pages/ExceptionsPage';
import { VerificationPortalPage } from './pages/VerificationPortalPage';
import { CertificatePreviewPage } from './pages/CertificatePreviewPage';
import { ReportsPage } from './pages/ReportsPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { RulesAndIntegrationsPage } from './pages/RulesAndIntegrationsPage';
import { TraceabilityMatrixPage } from './pages/TraceabilityMatrixPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 30, // 30 seconds
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900 text-white text-xs">
        Loading EDUTrace Secure Portal...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardPage />} />
              <Route path="institutions" element={<InstitutionsPage />} />
              <Route path="programmes" element={<ProgrammeApprovalsPage />} />
              <Route path="upload" element={<UploadWizardPage />} />
              <Route path="students" element={<StudentRecordsPage />} />
              <Route path="exceptions" element={<ExceptionsPage />} />
              <Route path="verification" element={<VerificationPortalPage />} />
              <Route path="certificates" element={<CertificatePreviewPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="audit" element={<AuditTrailPage />} />
              <Route path="rules" element={<RulesAndIntegrationsPage />} />
              <Route path="traceability" element={<TraceabilityMatrixPage />} />
            </Route>

            {/* Public fallback for QR verification route if accessed standalone */}
            <Route path="/verify/:slug" element={<CertificatePreviewPage />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
