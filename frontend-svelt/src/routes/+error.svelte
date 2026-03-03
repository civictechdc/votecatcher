<script>
  let { error, status } = $props();
</script>

<div class="container" role="alert" aria-live="assertive">
  <div class="card" style="max-width:800px; margin:2rem auto; text-align:center;">
    <h1>{status}</h1>
    <p class="text-muted">{error?.message ?? "An unexpected error occurred."}</p>
    <a href="/" class="button-outline">Return home</a>
  </div>
</div>

<style>
  @import "$lib/styles/theme.css";
</style>