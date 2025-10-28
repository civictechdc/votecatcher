<script lang="ts" setup>
	// Explanation: Page-level SvelteKit route component for the landing page.
	// Uses modern Svelte 5 <script setup> style and onMount to run browser-only code.
	import { onMount } from 'svelte';
	import Navbar from '$lib/components/Navbar.svelte';
	import { getSession } from '$lib/api/auth';
	import { ArrowRight, Users, Shield, Flag } from 'lucide-svelte';

	let user: { id?: string } | null = null;
	let loading = true;

	// Explanation: read VITE_API_URL in the helper; here just call the helper on mount.
	onMount(async () => {
		try {
			const res = await getSession();
			user = res?.user ?? null;
		} catch (err) {
			// keep it simple: log and treat as unauthenticated
			console.error('session check failed', err);
			user = null;
		} finally {
			loading = false;
		}
	});

	$: homeLink = user ? '/workspace' : '/auth';
</script>

<!-- Explanation: Tailwind-based markup closely mirrors the original Next/React layout.
     Keep classes and structure similar for an easy visual migration. -->
<div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-red-50">
	<Navbar {user} showAuthButtons />
	<div class="container mx-auto px-4 py-16">
		<div class="mx-auto max-w-4xl text-center">
			<div class="mb-6 flex items-center justify-center gap-3">
				<h1 class="text-5xl font-bold text-slate-900">VoteCatcher ✓</h1>
			</div>

			<p class="mx-auto mb-4 max-w-3xl text-xl font-medium text-slate-700">
				Open Source Campaign Infrastructure
			</p>

			<p class="mx-auto mb-8 max-w-2xl text-lg text-slate-600">
				Automate ballot signature recognition and validation. Put powerful organizing tools in the
				hands of grassroots campaigns.
				<span class="font-semibold text-blue-700">
					Democracy should be accessible to everyone.</span
				>
			</p>

			<div class="mb-16 flex flex-col justify-center gap-4 sm:flex-row">
				<a href={homeLink} class="inline-flex">
					<button
						class="inline-flex items-center rounded-md bg-blue-600 px-8 py-3 text-lg text-white hover:bg-blue-700"
					>
						Start Your Campaign
						<ArrowRight class="ml-2" />
					</button>
				</a>

				<button
					class="rounded-md border border-red-200 bg-transparent px-8 py-3 text-lg text-red-700 hover:bg-red-50"
				>
					Learn More
				</button>
			</div>

			<div class="mt-16 grid gap-8 md:grid-cols-3">
				<div class="rounded-lg border border-blue-100 bg-white p-6 text-center shadow-sm">
					<div
						class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100"
					>
						<Shield class="h-8 w-8 text-blue-600" />
					</div>
					<h3 class="mb-2 text-xl font-semibold text-blue-900">Signature Validation</h3>
					<p class="text-slate-600">
						High-accuracy signature triaging using multimodal LLMs integrated with voter files.
					</p>
				</div>

				<div class="rounded-lg border border-red-100 bg-white p-6 text-center shadow-sm">
					<div
						class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100"
					>
						<Users class="h-8 w-8 text-red-600" />
					</div>
					<h3 class="mb-2 text-xl font-semibold text-red-900">Grassroots Focused</h3>
					<p class="text-slate-600">
						Built for community organizers and campaigns that need powerful tools without the high
						costs.
					</p>
				</div>

				<div class="rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm">
					<div
						class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-100"
					>
						<Flag class="h-8 w-8 text-slate-600" />
					</div>
					<h3 class="mb-2 text-xl font-semibold text-slate-900">Open Source</h3>
					<p class="text-slate-600">
						Transparent, community-driven technology that strengthens democratic participation.
					</p>
				</div>
			</div>

			<div class="mt-16 rounded-lg bg-gradient-to-r from-blue-600 to-red-600 p-8 text-white">
				<h2 class="mb-4 text-2xl font-bold">🗳️ Why This Matters</h2>
				<p class="mx-auto max-w-3xl text-lg opacity-90">
					Running a grassroots campaign shouldn&apos;t require expensive software or technical
					expertise. We believe technology should make democratic participation easier, not harder.
					VoteCatcher puts campaign infrastructure in the hands of the people.
				</p>
			</div>
		</div>
	</div>
</div>
