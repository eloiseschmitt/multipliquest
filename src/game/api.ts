import { apiUrl } from "../config";

export interface Progress {
  current_level: number;
  available_tables: number[];
  newest_table: number;
  total_xp: number;
  best_score: number;
  global_success: boolean;
  mastery_attempts: number;
  mastery_correct: number;
  mastery_evaluable: boolean;
  mastery_success: boolean;
  completed_sessions: number;
}

export interface Question {
  id: number;
  position: number;
  table: number;
  multiplier: number;
}

export interface GameSession {
  id: number;
  level: number;
  status: "ACTIVE" | "COMPLETED";
  total_questions: number;
  score: number;
  xp_awarded: number;
  unlocked_level: number | null;
  answered_count: number;
  current_question: Question | null;
}

export interface Correction {
  id: number;
  position: number;
  table: number;
  multiplier: number;
  submitted_answer: number;
  is_correct: boolean;
  correct_answer: number;
}

export interface SessionSummary {
  id: number;
  level: number;
  status: "ACTIVE" | "COMPLETED";
  total_questions: number;
  score: number;
  xp_awarded: number;
  unlocked_level: number | null;
  table_stats: Record<string, { total: number; correct: number }>;
  progress: Progress;
}

export interface AnswerResponse {
  correction: Correction;
  session: GameSession;
  summary: SessionSummary | null;
}

function readCookie(name: string): string {
  const cookies = document.cookie ? document.cookie.split("; ") : [];
  const match = cookies.find((cookie) => cookie.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=").slice(1).join("=")) : "";
}

async function ensureCsrfCookie(): Promise<string> {
  const response = await fetch(apiUrl("/api/auth/csrf/"), {
    method: "GET",
    credentials: "include"
  });
  const data = (await response.json()) as { csrfToken?: string };
  return readCookie("csrftoken") || data.csrfToken || "";
}

async function requestJson<T>(input: RequestInfo | URL, init: RequestInit = {}): Promise<T> {
  const response = await fetch(input, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init.headers
    }
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(payload.detail ?? "Une erreur est survenue.");
  }

  return (await response.json()) as T;
}

async function mutatingRequest<T>(input: RequestInfo | URL, init: RequestInit = {}): Promise<T> {
  const csrfToken = readCookie("csrftoken") || (await ensureCsrfCookie());
  return requestJson<T>(input, {
    ...init,
    headers: {
      "X-CSRFToken": csrfToken,
      ...init.headers
    }
  });
}

export async function fetchProgress(): Promise<Progress> {
  return requestJson<Progress>(apiUrl("/api/game/progress/"));
}

export async function fetchActiveSession(): Promise<GameSession | null> {
  const data = await requestJson<{ session: GameSession | null }>(apiUrl("/api/game/session/"));
  return data.session;
}

export async function startSession(): Promise<GameSession> {
  const data = await mutatingRequest<{ session: GameSession }>(apiUrl("/api/game/session/"), {
    method: "POST",
    body: JSON.stringify({})
  });
  return data.session;
}

export async function submitAnswer(questionId: number, answer: number): Promise<AnswerResponse> {
  return mutatingRequest<AnswerResponse>(apiUrl("/api/game/answer/"), {
    method: "POST",
    body: JSON.stringify({ question_id: questionId, answer })
  });
}
