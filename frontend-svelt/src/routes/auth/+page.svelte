<script lang="ts">
  import { onMount } from "svelte"
  import { auth } from "$lib/stores/auth"
  import { get } from "svelte/store"
  import { featureFlags } from "$lib/config/featureFlags"
  import { Progress } from "$lib/components/ui"
  import { Navbar } from "$lib/components/layout"
  import DevFlags from "$lib/components/DevFlags.svelte"

  // Local state for form
  let mode: "signin" | "signup" = "signin"
  let email = ""
  let password = ""
  let code = ""
  let step = 0 // used for small progress in signup/2FA
  let msg = ""
  let loading = false

  // derived
  $: st = get(auth)

  onMount(async () => {
    await auth.initSession()
  })

  const submitSignUp = async () => {
    msg = ""
    loading = true
    const res = await auth.signUp(email, password)
    loading = false
    if (!res.ok) {
      msg = res.error || "Sign up failed"
      return
    }
    step = 1
  }

  const submitSignIn = async () => {
    msg = ""
    loading = true
    const res = await auth.signIn(email, password)
    loading = false
    if (!res.ok) {
      msg = res.error || "Sign in failed"
      return
    }
    const state = get(auth)
    if (state.twoFactorRequired && featureFlags.isEnabled("2fa")) {
      step = 2
    } else {
      location.href = "/getting-started"
    }
  }

  const request2fa = async () => {
    msg = ""
    loading = true
    const res = await auth.start2fa(email)
    loading = false
    if (!res.ok) msg = res.error || "Failed to start 2FA"
    else step = 3
  }

  const verify2fa = async () => {
    msg = ""
    loading = true
    const res = await auth.verify2fa(email, code)
    loading = false
    if (!res.ok) msg = res.error || "Invalid code"
    else location.href = "/getting-started"
  }
</script>

<svelte:head>
  <title>Sign in / Sign up — Votecatcher</title>
</svelte:head>

<div class="container" role="main">
  <Navbar />
  <div class="card" style="margin-top:1rem; max-width:640px; margin-left:auto; margin-right:auto;">
    <div class="space-y-4">
      <h1 tabindex="-1">Sign in or create an account</h1>
      <p class="text-muted">Simple, accessible auth. We will never show your password or expose keys.</p>

      <Progress value={Math.round(((step + 1) / 4) * 100)} />

      <div class="row" style="gap:0.5rem;">
        <button class="button-outline" on:click={() => (mode = "signin")} aria-pressed={mode === "signin"}>Sign in</button>
        <button class="button-outline" on:click={() => (mode = "signup")} aria-pressed={mode === "signup"}>Sign up</button>
      </div>

      {#if mode === "signup"}
        <div class="space-y-3" aria-live="polite">
          <label class="label" for="su-email">Email</label>
          <input id="su-email" class="input" type="email" bind:value={email} autocomplete="email" />
          <label class="label" for="su-pass">Password</label>
          <input id="su-pass" class="input" type="password" bind:value={password} autocomplete="new-password" />
          <div class="row" style="justify-content:space-between">
            <button class="button-outline" on:click={() => (mode = "signin")}>Back</button>
            <button class="button" on:click={submitSignUp} disabled={loading || !email || !password}>
              {loading ? "Working..." : step === 1 ? "Verification Sent" : "Create account"}
            </button>
          </div>
          <div class="text-muted small">We will send a verification email (mocked).</div>
        </div>
      {:else}
        <div class="space-y-3" aria-live="polite">
          <label class="label" for="si-email">Email</label>
          <input id="si-email" class="input" type="email" bind:value={email} autocomplete="email" />
          <label class="label" for="si-pass">Password</label>
          <input id="si-pass" class="input" type="password" bind:value={password} autocomplete="current-password" />
          <div class="row" style="justify-content:space-between">
            <button class="button-outline" on:click={() => (mode = "signup")}>Create account</button>
            <button class="button" on:click={submitSignIn} disabled={loading || !email || !password}>
              {loading ? "Working..." : "Sign in"}
            </button>
          </div>

          {#if featureFlags.isEnabled("2fa")}
            <div class="space-y-2">
              <hr />
              <div class="text-muted small">Two-factor authentication (dev toggle available)</div>
              <button class="button-outline" on:click={request2fa} disabled={loading || !email}>Request 2FA code</button>
            </div>
          {/if}
        </div>
      {/if}

      {#if step === 3}
        <div class="space-y-2">
          <label class="label" for="code">Enter 2FA code</label>
          <input id="code" class="input" bind:value={code} inputmode="numeric" />
          <div class="row" style="justify-content:space-between">
            <button class="button-outline" on:click={() => (step = 0)}>Cancel</button>
            <button class="button" on:click={verify2fa} disabled={!code || loading}>Verify</button>
          </div>
        </div>
      {/if}

      {#if msg}
        <div role="alert" style="color:var(--vc-danger)" class="small">{msg}</div>
      {/if}
    </div>

    <!-- Dev-only panel: visible in development (import.meta.env.DEV) -->
    <DevFlags />
  </div>
</div>

<style>
  @import "$lib/styles/theme.css";
</style>