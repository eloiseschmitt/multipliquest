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
        return new Response(null, { status: 204 });
      })
    );

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Bonjour Nina" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Déconnexion" }));

    expect(await screen.findByRole("heading", { name: "Connexion joueur" })).toBeInTheDocument();
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
