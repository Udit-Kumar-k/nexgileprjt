import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { OrganizationPage } from './pages/organization/OrganizationPage';
import { CarbonPage } from './pages/carbon/CarbonPage';
import { PCFPage } from './pages/pcf/PCFPage';
import { SupplierPage } from './pages/supplier/SupplierPage';
import { AnalyticsPage } from './pages/analytics/AnalyticsPage';
import { CompliancePage } from './pages/compliance/CompliancePage';
import { IntegrationPage } from './pages/integration/IntegrationPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const RoleDefaultRedirect: React.FC = () => {
  const { user } = useAuthStore();
  if (user?.role === 'Supplier') {
    return <Navigate to="/supplier" replace />;
  }
  return <Navigate to="/dashboard" replace />;
};

export const App: React.FC = () => {
  const { initializeAuth } = useAuthStore();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  const { user } = useAuthStore();
  const isSupplier = user?.role === 'Supplier';

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<RoleDefaultRedirect />} />
          <Route
            path="dashboard"
            element={isSupplier ? <Navigate to="/supplier" replace /> : <DashboardPage />}
          />
          <Route path="organization" element={<OrganizationPage />} />
          <Route path="carbon" element={<CarbonPage />} />
          <Route path="pcf" element={<PCFPage />} />
          <Route path="supplier" element={<SupplierPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="compliance" element={<CompliancePage />} />
          <Route path="integration" element={<IntegrationPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
