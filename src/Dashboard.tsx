import { useAuth } from "./auth/useAuth";

export function Dashboard() {
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  const displayName = user.displayName || user.username;

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">MultipliQuest</p>
          <h1>Bonjour {displayName}</h1>
        </div>
        <button className="secondary-button" type="button" onClick={() => void logout()}>
          Déconnexion
        </button>
      </header>

      <section className="progress-summary" aria-label="Progression">
        <div>
          <span>Niveau</span>
          <strong>{user.currentLevel}</strong>
        </div>
        <div>
          <span>XP</span>
          <strong>{user.totalXp}</strong>
        </div>
      </section>
    </main>
  );
}
