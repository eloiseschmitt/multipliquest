import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useAuth } from "../auth/useAuth";
import {
  fetchActiveSession,
  fetchProgress,
  startSession,
  submitAnswer,
  type AnswerResponse,
  type Correction,
  type GameSession,
  type Progress,
  type SessionSummary
} from "./api";

export function GameScreen() {
  const { user, logout } = useAuth();
  const [progress, setProgress] = useState<Progress | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [correction, setCorrection] = useState<Correction | null>(null);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([fetchProgress(), fetchActiveSession()])
      .then(([progressPayload, sessionPayload]) => {
        if (!active) {
          return;
        }
        setProgress(progressPayload);
        setSession(sessionPayload);
      })
      .catch((apiError: unknown) => {
        if (active) {
          setError(apiError instanceof Error ? apiError.message : "Impossible de charger la partie.");
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const question = session?.current_question ?? null;
  const displayName = user?.displayName || user?.username || "joueur";
  const unlockText = useMemo(() => {
    if (!progress) {
      return "";
    }
    if (progress.current_level >= 9) {
      return "Dernier niveau : table de 12";
    }
    return `Prochaine table : ${progress.newest_table + 1}`;
  }, [progress]);

  async function handleStart() {
    setError("");
    setCorrection(null);
    setSummary(null);
    setIsSubmitting(true);
    try {
      setSession(await startSession());
      setProgress(await fetchProgress());
    } catch (apiError) {
      setError(apiError instanceof Error ? apiError.message : "Impossible de démarrer.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question) {
      return;
    }
    const parsed = Number.parseInt(answer, 10);
    if (!Number.isInteger(parsed)) {
      setError("Entre un nombre pour valider ta réponse.");
      return;
    }

    setError("");
    setIsSubmitting(true);
    try {
      const payload: AnswerResponse = await submitAnswer(question.id, parsed);
      setCorrection(payload.correction);
      setSession(payload.session);
      setAnswer("");
      if (payload.summary) {
        setSummary(payload.summary);
        setProgress(payload.summary.progress);
      }
    } catch (apiError) {
      setError(apiError instanceof Error ? apiError.message : "Réponse non enregistrée.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return <main className="loading-shell">Chargement...</main>;
  }

  return (
    <main className="dashboard-shell game-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">MultipliQuest</p>
          <h1>Bonjour {displayName}</h1>
        </div>
        <button className="secondary-button" type="button" onClick={() => void logout()}>
          Déconnexion
        </button>
      </header>

      {progress ? (
        <section className="progress-summary" aria-label="Progression">
          <div>
            <span>Niveau</span>
            <strong>{progress.current_level}</strong>
          </div>
          <div>
            <span>Tables</span>
            <strong>{progress.available_tables.join(", ")}</strong>
          </div>
          <div>
            <span>XP</span>
            <strong>{progress.total_xp}</strong>
          </div>
        </section>
      ) : null}

      <section className="game-panel" aria-label="Exercice">
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}

        {!session || summary ? (
          <div className="start-panel">
            <p className="intro">
              Tables en cours : {progress?.available_tables.join(", ") ?? "2, 3, 4"}. {unlockText}
            </p>
            <button className="primary-button" type="button" onClick={() => void handleStart()} disabled={isSubmitting}>
              Jouer une série
            </button>
          </div>
        ) : null}

        {session && question && !summary ? (
          <form className="question-form" onSubmit={(event) => void handleSubmit(event)}>
            <div className="series-row">
              <span>
                Question {session.answered_count + 1} / {session.total_questions}
              </span>
              <span>Table de {question.table}</span>
            </div>
            <p className="question-text">
              {question.table} x {question.multiplier} = ?
            </p>
            <label htmlFor="answer">Ta réponse</label>
            <input
              id="answer"
              inputMode="numeric"
              min="0"
              max="144"
              pattern="[0-9]*"
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              disabled={isSubmitting}
            />
            <button className="primary-button" type="submit" disabled={isSubmitting}>
              Valider
            </button>
          </form>
        ) : null}

        {correction && !summary ? (
          <div className={correction.is_correct ? "feedback is-correct" : "feedback is-wrong"} aria-live="polite">
            {correction.is_correct ? (
              <p>Bravo, c'est correct.</p>
            ) : (
              <p>
                Pas encore : {correction.table} x {correction.multiplier} = {correction.correct_answer}.
              </p>
            )}
          </div>
        ) : null}

        {summary ? <SessionSummaryView summary={summary} /> : null}
      </section>
    </main>
  );
}

function SessionSummaryView({ summary }: { summary: SessionSummary }) {
  const progress = summary.progress;
  return (
    <section className="summary-panel" aria-label="Bilan de session">
      <h2>Bilan de la série</h2>
      <p className="score-line">
        {summary.score} / {summary.total_questions} bonnes réponses, {summary.xp_awarded} XP gagnés.
      </p>
      {summary.unlocked_level ? (
        <p className="success-message">Nouvelle table débloquée : niveau {summary.unlocked_level}.</p>
      ) : (
        <p className="intro">Continue comme ça : chaque série rapproche du prochain déblocage.</p>
      )}
      <div className="progress-bars">
        <ProgressMeter label="Réussite globale" value={progress.best_score} max={20} />
        <ProgressMeter label={`Maîtrise table ${progress.newest_table}`} value={progress.mastery_correct} max={20} />
      </div>
      <ul className="table-stats">
        {Object.entries(summary.table_stats).map(([table, stats]) => (
          <li key={table}>
            Table {table} : {stats.correct} / {stats.total}
          </li>
        ))}
      </ul>
    </section>
  );
}

function ProgressMeter({ label, value, max }: { label: string; value: number; max: number }) {
  return (
    <div className="meter">
      <div className="meter-label">
        <span>{label}</span>
        <strong>
          {value} / {max}
        </strong>
      </div>
      <progress value={value} max={max} />
    </div>
  );
}
