<script lang="ts">
	import { ArrowRight, Users, Shield, Flag } from 'lucide-svelte';
	import DevFlags from '$lib/components/DevFlags.svelte';
	import { getCTADestination } from '$lib/utils/mode';

	const homeLink = $derived(getCTADestination());
</script>

<div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-red-50">
	<div class="container mx-auto px-4 py-16">
		<div class="mx-auto max-w-4xl text-center">
			<div class="mb-6 flex items-center justify-center gap-3">
				<h1 class="text-5xl font-bold text-blue-600">VoteCatcher ✓</h1>
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
				<!-- Make the anchor the clickable element (avoid nested <button> inside <a>) -->
				<a
					href={homeLink}
					class="inline-flex items-center justify-center rounded-md bg-blue-600 px-8 py-3 text-lg text-white hover:bg-blue-700"
				>
					Start Your Campaign
					<ArrowRight class="ml-2" />
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

	{#if import.meta.env.DEV}
		<!-- Dev-only UI to toggle flags in real time -->
		<DevFlags />
	{/if}
</div>
