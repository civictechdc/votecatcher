<script lang="ts">
	export let value = 0; // 0..100
	// aria-valuenow should be integer
	const ariaNow = Math.round(value);
</script>

<div aria-hidden="true" class="progress-track" style="height: 12px;">
	<div class="progress-fill" style="width: {value}%"></div>
</div>
<div class="small text-muted" aria-live="polite" aria-atomic="true">
	Progress: {ariaNow}%
</div>
