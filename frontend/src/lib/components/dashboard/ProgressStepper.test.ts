import { describe, it, expect } from "vitest";
import { render } from "@testing-library/svelte";
import ProgressStepper from "./ProgressStepper.svelte";
import type { VoterListStatus, PetitionsStatus } from "$lib/api/generated/models/Campaign";

describe("ProgressStepper — Type Contract (BDD)", () => {
	const campaignId = "test-campaign-1";

	describe("Given a campaign with no uploads", () => {
		it("should render the empty state when no voter list and no petitions", () => {
			const voterListStatus: VoterListStatus = {
				exists: false,
				rowCount: null,
				uploadedAt: null,
				regionName: null,
			};
			const petitionStatus: PetitionsStatus = {
				exists: false,
				fileCount: 0,
				signatureCount: 0,
			};

			const { container } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: false,
					campaignId,
				},
			});

			expect(container.textContent).toContain("Voter List");
			expect(container.textContent).toContain("Petitions");
		});

		it("should show Upload Voter List CTA when empty", () => {
			const voterListStatus: VoterListStatus = {
				exists: false,
				rowCount: null,
				uploadedAt: null,
				regionName: null,
			};
			const petitionStatus: PetitionsStatus = {
				exists: false,
				fileCount: 0,
				signatureCount: 0,
			};

			const { getByRole } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: false,
					campaignId,
				},
			});

			expect(getByRole("button", { name: /upload voter list/i })).toBeTruthy();
		});
	});

	describe("Given a campaign with voter list only", () => {
		it("should show voter count and region from camelCase properties", () => {
			const voterListStatus: VoterListStatus = {
				exists: true,
				rowCount: 15000,
				uploadedAt: "2026-04-01T00:00:00Z",
				regionName: "Washington DC",
			};
			const petitionStatus: PetitionsStatus = {
				exists: false,
				fileCount: 0,
				signatureCount: 0,
			};

			const { container } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: false,
					campaignId,
				},
			});

			expect(container.textContent).toContain("15,000");
			expect(container.textContent).toContain("Washington DC");
		});

		it("should show Upload Petitions CTA when voter list exists but no petitions", () => {
			const voterListStatus: VoterListStatus = {
				exists: true,
				rowCount: 5000,
				uploadedAt: "2026-04-01",
				regionName: "DC",
			};
			const petitionStatus: PetitionsStatus = {
				exists: false,
				fileCount: 0,
				signatureCount: 0,
			};

			const { getByRole } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: false,
					campaignId,
				},
			});

			expect(getByRole("button", { name: /upload petitions/i })).toBeTruthy();
		});
	});

	describe("Given a campaign with petitions only", () => {
		it("should display file count and signature count from camelCase properties", () => {
			const voterListStatus: VoterListStatus = {
				exists: false,
				rowCount: null,
				uploadedAt: null,
				regionName: null,
			};
			const petitionStatus: PetitionsStatus = {
				exists: true,
				fileCount: 3,
				signatureCount: 450,
			};

			const { container } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: false,
					campaignId,
				},
			});

			expect(container.textContent).toContain("3 files");
			expect(container.textContent).toContain("450 signatures");
		});
	});

	describe("Given a campaign with both uploads and no jobs", () => {
		it("should show Create Job CTA when ready to process", () => {
			const voterListStatus: VoterListStatus = {
				exists: true,
				rowCount: 10000,
				uploadedAt: "2026-04-09",
				regionName: "DC",
			};
			const petitionStatus: PetitionsStatus = {
				exists: true,
				fileCount: 5,
				signatureCount: 800,
			};

			const { getByRole } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: false,
					campaignId,
				},
			});

			expect(getByRole("button", { name: /create job/i })).toBeTruthy();
		});
	});

	describe("Given a campaign that has jobs", () => {
		it("should not render the setup stepper when jobs exist", () => {
			const voterListStatus: VoterListStatus = {
				exists: true,
				rowCount: 10000,
				uploadedAt: "2026-04-09",
				regionName: "DC",
			};
			const petitionStatus: PetitionsStatus = {
				exists: true,
				fileCount: 5,
				signatureCount: 800,
			};

			const { container } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: true,
					campaignId,
				},
			});

			expect(container.querySelector("h2")).toBeNull();
		});
	});

	describe("Given a voter list with null optional fields", () => {
		it("should handle null rowCount, uploadedAt, and regionName gracefully", () => {
			const voterListStatus: VoterListStatus = {
				exists: true,
				rowCount: null,
				uploadedAt: null,
				regionName: null,
			};
			const petitionStatus: PetitionsStatus = {
				exists: false,
				fileCount: 0,
				signatureCount: 0,
			};

			const { container } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: false,
					campaignId,
				},
			});

			expect(container.textContent).toContain("Voter List");
			expect(container.textContent).toContain("0 voters");
		});
	});

	describe("Given a petition status with zero signature count", () => {
		it("should not show signature count when zero", () => {
			const voterListStatus: VoterListStatus = {
				exists: false,
				rowCount: null,
				uploadedAt: null,
				regionName: null,
			};
			const petitionStatus: PetitionsStatus = {
				exists: true,
				fileCount: 2,
				signatureCount: 0,
			};

			const { container } = render(ProgressStepper, {
				props: {
					voterListStatus,
					petitionStatus,
					hasJobs: false,
					campaignId,
				},
			});

			expect(container.textContent).toContain("2 files");
			expect(container.textContent).not.toContain("0 signatures");
		});
	});
});
