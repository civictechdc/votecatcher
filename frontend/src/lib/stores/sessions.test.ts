import { describe, it, expect, vi, beforeEach } from "vitest";
import { get } from "svelte/store";
import { sessions, resetSessionsStore, type Session } from "./sessions";

vi.mock("./api-client", () => ({
	getApiClient: vi.fn(() => ({
		basePath: "http://localhost:8000/api",
	})),
}));

global.fetch = vi.fn();

describe("Sessions Store", () => {
	beforeEach(() => {
		resetSessionsStore();
		vi.clearAllMocks();
	});

	describe("initial state", () => {
		it("should have empty sessions array", () => {
			const state = get(sessions);
			expect(state.sessions).toEqual([]);
			expect(state.currentSession).toBeNull();
			expect(state.loading).toBe(false);
			expect(state.saving).toBe(false);
			expect(state.error).toBeNull();
		});
	});

	describe("fetchAll", () => {
		it("should fetch all sessions", async () => {
			const mockSessions: Session[] = [
				{
					id: 1,
					name: "Session 1",
					campaign_id: null,
					session_type: "REAL",
					snapshot_data: {},
					created_at: "2024-01-01T00:00:00",
					updated_at: "2024-01-01T00:00:00",
				},
			];

			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: true,
				json: async () => ({ sessions: mockSessions, total: 1 }),
			});

			await sessions.fetchAll();

			const state = get(sessions);
			expect(state.sessions).toEqual(mockSessions);
			expect(state.loading).toBe(false);
		});

		it("should handle fetch errors", async () => {
			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: false,
				json: async () => ({ detail: "Not found" }),
			});

			await sessions.fetchAll();

			const state = get(sessions);
			expect(state.error).toBe("Not found");
			expect(state.loading).toBe(false);
		});
	});

	describe("save", () => {
		it("should create a new session", async () => {
			const newSession: Session = {
				id: 1,
				name: "New Session",
				campaign_id: null,
				session_type: "REAL",
				snapshot_data: { job_ids: [1, 2] },
				created_at: "2024-01-01T00:00:00",
				updated_at: "2024-01-01T00:00:00",
			};

			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: true,
				json: async () => newSession,
			});

			const result = await sessions.save("New Session", { job_ids: [1, 2] });

			expect(result).toEqual(newSession);
			const state = get(sessions);
			expect(state.saving).toBe(false);
		});

		it("should handle save errors", async () => {
			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: false,
				json: async () => ({ detail: "Save failed" }),
			});

			await expect(sessions.save("Test", {})).rejects.toThrow("Save failed");

			const state = get(sessions);
			expect(state.error).toBe("Save failed");
		});
	});

	describe("load", () => {
		it("should load a session by id", async () => {
			const mockSession: Session = {
				id: 1,
				name: "Loaded Session",
				campaign_id: null,
				session_type: "REAL",
				snapshot_data: { test: true },
				created_at: "2024-01-01T00:00:00",
				updated_at: "2024-01-01T00:00:00",
			};

			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: true,
				json: async () => mockSession,
			});

			const result = await sessions.load(1);

			expect(result).toEqual(mockSession);
			const state = get(sessions);
			expect(state.currentSession).toEqual(mockSession);
		});

		it("should handle load errors", async () => {
			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: false,
				json: async () => ({ detail: "Session not found" }),
			});

			await expect(sessions.load(999)).rejects.toThrow("Session not found");

			const state = get(sessions);
			expect(state.error).toBe("Session not found");
		});
	});

	describe("delete", () => {
		it("should delete a session", async () => {
			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: true,
				status: 204,
			});

			await sessions.delete(1);

			const state = get(sessions);
			expect(state.loading).toBe(false);
		});

		it("should handle delete errors", async () => {
			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: false,
				json: async () => ({ detail: "Cannot delete" }),
			});

			await expect(sessions.delete(1)).rejects.toThrow("Cannot delete");
		});
	});

	describe("exportSession", () => {
		it("should trigger ZIP download", async () => {
			const mockBlob = new Blob(["test"], { type: "application/zip" });

			global.URL.createObjectURL = vi.fn(() => "blob:test");
			global.URL.revokeObjectURL = vi.fn();

			const mockAnchor = {
				click: vi.fn(),
				href: "",
				download: "",
			} as unknown as HTMLAnchorElement;

			vi.spyOn(document, "createElement").mockReturnValue(mockAnchor);
			vi.spyOn(document.body, "appendChild").mockImplementation(() => mockAnchor);
			vi.spyOn(document.body, "removeChild").mockImplementation(() => mockAnchor);

			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: true,
				blob: async () => mockBlob,
				headers: { get: vi.fn().mockReturnValue('attachment; filename="session_1.zip"') },
			});

			await sessions.export(1);

			expect(global.fetch).toHaveBeenCalledWith("http://localhost:8000/api/sessions/1/export");
		});
	});

	describe("clearError", () => {
		it("should clear error state", () => {
			sessions.clearError();
			const state = get(sessions);
			expect(state.error).toBeNull();
		});
	});

	describe("reset", () => {
		it("should reset store to initial state", () => {
			sessions.reset();
			const state = get(sessions);
			expect(state).toEqual({
				sessions: [],
				currentSession: null,
				loading: false,
				saving: false,
				error: null,
			});
		});
	});
});
