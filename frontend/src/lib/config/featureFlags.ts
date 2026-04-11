// Lightweight feature flag helper.
// - Read comma-separated flags from VITE_FEATURES (e.g. "mockAuth,2fa,passkeys")
// - Allow localStorage dev toggles (key: vc:flags) for quick dev testing
// - Keep logic minimal and synchronous so it's safe in both server and client contexts.
const env =
	typeof import.meta !== "undefined"
		? ((import.meta as unknown as Record<string, Record<string, string>>)["env"] ?? {})
		: {};
const raw = (env["VITE_FEATURES"] as string) || "";
const envFlags = new Set(
	raw
		.split(",")
		.map((s) => s.trim())
		.filter(Boolean),
);

function getLocalFlags(): Set<string> {
	if (typeof window === "undefined") return new Set();
	try {
		const rawLs = localStorage.getItem("vc:flags") || "";
		return new Set(
			rawLs
				.split(",")
				.map((s) => s.trim())
				.filter(Boolean),
		);
	} catch {
		return new Set();
	}
}

export const featureFlags = {
	isEnabled(flag: string) {
		return envFlags.has(flag) || getLocalFlags().has(flag);
	},
	// Toggle a flag locally (dev-only)
	toggleLocal(flag: string) {
		if (typeof window === "undefined") return;
		const flags = getLocalFlags();
		if (flags.has(flag)) flags.delete(flag);
		else flags.add(flag);
		localStorage.setItem("vc:flags", Array.from(flags).join(","));
	},
	list() {
		return Array.from(new Set([...Array.from(envFlags), ...Array.from(getLocalFlags())]));
	},
};
