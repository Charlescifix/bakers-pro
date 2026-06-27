import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { pageConfigs } from './data/mock';
import Dashboard from './pages/Dashboard';
import GenericPage from './pages/GenericPage';
import QuoteBuilderModal from './pages/QuoteBuilderModal';
import RecipeBuilderModal from './pages/RecipeBuilderModal';
import ProductBuilderModal from './pages/ProductBuilderModal';
import ImportUploadModal from './pages/ImportUploadModal';
import SettingsPage from './pages/SettingsPage';
import { LoginPage, RegisterPage } from './pages/AuthPages';
import { UserProvider } from './lib/user-context';

function ConfigPage({ slug }: { slug: keyof typeof pageConfigs }) {
  return <GenericPage config={pageConfigs[slug]} />;
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  return localStorage.getItem('access_token') ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <UserProvider>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<RequireAuth><AppShell /></RequireAuth>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="ingredients" element={<ConfigPage slug="ingredients" />} />
        <Route path="packaging" element={<ConfigPage slug="packaging" />} />
        <Route path="suppliers" element={<ConfigPage slug="suppliers" />} />
        <Route path="recipes" element={
          <GenericPage
            config={pageConfigs['recipes']}
            renderCreateModal={(onClose, onCreated) => (
              <RecipeBuilderModal onClose={onClose} onCreated={onCreated} />
            )}
          />
        } />
        <Route path="products" element={
          <GenericPage
            config={pageConfigs['products']}
            renderCreateModal={(onClose, onCreated) => (
              <ProductBuilderModal onClose={onClose} onCreated={onCreated} />
            )}
          />
        } />
        <Route path="customers" element={<ConfigPage slug="customers" />} />
        <Route path="sales-channels" element={<ConfigPage slug="sales-channels" />} />
        <Route path="quotes" element={
          <GenericPage
            config={pageConfigs['quotes']}
            renderCreateModal={(onClose, onCreated) => (
              <QuoteBuilderModal onClose={onClose} onCreated={onCreated} />
            )}
          />
        } />
        <Route path="orders" element={<ConfigPage slug="orders" />} />
        <Route path="production" element={<ConfigPage slug="production" />} />
        <Route path="shopping-lists" element={<ConfigPage slug="shopping-lists" />} />
        <Route path="imports" element={
          <GenericPage
            config={pageConfigs['imports']}
            renderCreateModal={(onClose, onCreated) => (
              <ImportUploadModal onClose={onClose} onCreated={onCreated} />
            )}
          />
        } />
        <Route path="reports" element={<ConfigPage slug="reports" />} />
        <Route path="intelligence" element={<ConfigPage slug="intelligence" />} />
        <Route path="allergens" element={<ConfigPage slug="allergens" />} />
        <Route path="compliance" element={<ConfigPage slug="compliance" />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
    </UserProvider>
  );
}
