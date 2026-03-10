<script lang="ts">
	import { Button } from '$lib/components/ui';
</script>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-bold text-slate-900">Dashboard</h1>
		<p class="mt-2 text-slate-600">Welcome to your workspace</p>
	</div>

	<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<h3 class="text-sm font-medium text-slate-600">Active Campaigns</h3>
			<p class="mt-2 text-3xl font-bold text-slate-900">0</p>
		</div>
		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<h3 class="text-sm font-medium text-slate-600">Running Jobs</h3>
			<p class="mt-2 text-3xl font-bold text-slate-900">0</p>
		</div>
		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<h3 class="text-sm font-medium text-slate-600">Pending Results</h3>
			<p class="mt-2 text-3xl font-bold text-slate-900">0</p>
		</div>
		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<h3 class="text-sm font-medium text-slate-600">Verified Signatures</h3>
			<p class="mt-2 text-3xl font-bold text-slate-900">0</p>
		</div>
	</div>

	<div class="rounded-lg border border-slate-200 bg-white p-6">
		<h2 class="text-lg font-semibold text-slate-900">Quick Actions</h2>
		<div class="mt-4 flex gap-4">
			<Button variant="primary" onclick={() => window.location.href = '/workspace/campaigns'}>
				Create Campaign
			</Button>
			<Button variant="secondary" onclick={() => window.location.href = '/workspace/jobs'}>
				View Jobs
			</Button>
		</div>
	</div>
</div>
