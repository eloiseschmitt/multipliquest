import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: init.status ?? 200,
    headers: { "Content-Type": "application/json" }
  });
}

const childPayload = {
  user: {
    id: 1,
    username: "nina",
    display_name: "Nina",
    role: "CHILD",
    current_level: 2,
    total_xp: 80
  }
};

const progressPayload = {
  current_level: 1,
  available_tables: [2, 3, 4],
  newest_table: 4,
  total_xp: 80,
  best_score: 0,
  global_success: false,
  mastery_attempts: 0,
  mastery_correct: 0,
  mastery_evaluable: false,
  mastery_success: false,
  completed_sessions: 0
};

const activeSessionPayload = {
  session: null
};

function gameResponse(url: string) {
  if (url === "/api/game/progress/") {
    return jsonResponse(progressPayload);
  }
  if (url === "/api/game/session/") {
    return jsonResponse(activeSessionPayload);
  }
  return null;
}

describe("authentication flow", () => {
  beforeEach(() => {
    document.cookie = "csrftoken=test-csrf";
  });

  afterEach(() => {
    vi.restoreAllMocks();
    document.cookie = "csrftoken=; Max-Age=0";
  });

  it("logs in and shows the player dashboard", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();
      if (url === "/api/auth/me/") {
        return jsonResponse({ detail: "Forbidden" }, { status: 403 });
      }
      if (url === "/api/auth/login/") {
        return jsonResponse(childPayload);
      }
      const gamePayload = gameResponse(url);
      if (gamePayload) {
        return gamePayload;
      }
      return new Response(null, { status: 204 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByRole("heading", { name: "Connexion joueur" });
    await userEvent.type(screen.getByLabelText("Identifiant"), "nina");
    await userEvent.type(screen.getByLabelText("Mot de passe"), "secret");
    await userEvent.click(screen.getByRole("button", { name: "Se connecter" }));

    expect(await screen.findByRole("heading", { name: "Bonjour Nina" })).toBeInTheDocument();
    expect(screen.getByText("80")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Jouer une série" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login/",
      expect.objectContaining({
        credentials: "include",
        method: "POST",
        headers: expect.objectContaining({ "X-CSRFToken": "test-csrf" })
      })
    );
  });

  it("shows an understandable error when login fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = input.toString();
        if (url === "/api/auth/me/") {
          return jsonResponse({ detail: "Forbidden" }, { status: 403 });
        }
        return jsonResponse({ detail: "Identifiant ou mot de passe incorrect." }, { status: 400 });
      })
    );

    render(<App />);

    await screen.findByRole("heading", { name: "Connexion joueur" });
    await userEvent.type(screen.getByLabelText("Identifiant"), "nina");
    await userEvent.type(screen.getByLabelText("Mot de passe"), "bad");
    await userEvent.click(screen.getByRole("button", { name: "Se connecter" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Identifiant ou mot de passe incorrect.");
  });

  it("logs out and returns to the login page", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = input.toString();
        if (url === "/api/auth/me/") {
          return jsonResponse(childPayload);
        }
        if (url === "/api/auth/logout/") {
          return new Response(null, { status: 204 });
        }
        const gamePayload = gameResponse(url);
        if (gamePayload) {
          return gamePayload;
        }
        return new Response(null, { status: 204 });
      })
    );

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Bonjour Nina" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Déconnexion" }));

    expect(await screen.findByRole("heading", { name: "Connexion joueur" })).toBeInTheDocument();
  });

  it("starts a game session and shows immediate correction", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = input.toString();
      if (url === "/api/auth/me/") {
        return jsonResponse(childPayload);
      }
      if (url === "/api/game/progress/") {
        return jsonResponse(progressPayload);
      }
      if (url === "/api/game/session/" && init?.method === "POST") {
        return jsonResponse({
          session: {
            id: 10,
            level: 1,
            status: "ACTIVE",
            total_questions: 20,
            score: 0,
            xp_awarded: 0,
            unlocked_level: null,
            answered_count: 0,
            current_question: { id: 99, position: 1, table: 4, multiplier: 6 }
          }
        });
      }
      if (url === "/api/game/session/") {
        return jsonResponse({ session: null });
      }
      if (url === "/api/game/answer/") {
        return jsonResponse({
          correction: {
            id: 99,
            position: 1,
            table: 4,
            multiplier: 6,
            submitted_answer: 24,
            is_correct: true,
            correct_answer: 24
          },
          session: {
            id: 10,
            level: 1,
            status: "ACTIVE",
            total_questions: 20,
            score: 0,
            xp_awarded: 0,
            unlocked_level: null,
            answered_count: 1,
            current_question: { id: 100, position: 2, table: 3, multiplier: 8 }
          },
          summary: null
        });
      }
      return new Response(null, { status: 204 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: "Jouer une série" }));
    expect(await screen.findByText("4 x 6 = ?")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Ta réponse"), "24");
    await userEvent.click(screen.getByRole("button", { name: "Valider" }));

    expect(await screen.findByText("Bravo, c'est correct.")).toBeInTheDocument();
    expect(screen.getByText("3 x 8 = ?")).toBeInTheDocument();
  });

  it("redirects to login when the session is expired", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse({ detail: "Forbidden" }, { status: 403 }))
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Connexion joueur" })).toBeInTheDocument();
    });
  });
});
