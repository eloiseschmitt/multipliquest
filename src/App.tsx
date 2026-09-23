import { AuthProvider } from "./auth/AuthContext";
import { useAuth } from "./auth/useAuth";
import { Dashboard } from "./Dashboard";
import { LoginPage } from "./LoginPage";
import "./styles.css";

function AppContent() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <main className="loading-shell" aria-live="polite">
        Chargement...
      </main>
    );
  }

  return user ? <Dashboard /> : <LoginPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
