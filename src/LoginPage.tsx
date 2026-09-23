import { FormEvent, useState } from "react";
import { useAuth } from "./auth/useAuth";

export function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await login(username, password);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "";
      setError(message === "SESSION_EXPIRED" ? "Connexion impossible pour le moment." : message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel" aria-labelledby="login-title">
        <div>
          <p className="eyebrow">MultipliQuest</p>
          <h1 id="login-title">Connexion joueur</h1>
          <p className="intro">Entre ton identifiant et ton mot de passe pour retrouver ta progression.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="username">Identifiant</label>
          <input
            id="username"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />

          <label htmlFor="password">Mot de passe</label>
          <div className="password-row">
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <button type="button" className="secondary-button" onClick={() => setShowPassword((visible) => !visible)}>
              {showPassword ? "Masquer" : "Afficher"}
            </button>
          </div>

          {error ? (
            <p role="alert" className="form-error">
              {error}
            </p>
          ) : null}

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Connexion..." : "Se connecter"}
          </button>
        </form>
      </section>
    </main>
  );
}
