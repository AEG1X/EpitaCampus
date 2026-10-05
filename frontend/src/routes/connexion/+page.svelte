<script>
	import { goto } from '$app/navigation';
	import { api } from '#lib/api.js';
	import { session } from '#lib/session.svelte.js';

	let status = $state(null);
	let mode = $state('login');
	let email = $state('');
	let name = $state('');
	let password = $state('');
	let error = $state('');
	let busy = $state(false);

	$effect(() => {
		api('/auth/status').then((s) => {
			status = s;
			if (s.first_user) mode = 'signup';
		});
	});

	$effect(() => {
		if (session.user) goto('/');
	});

	async function submit(event) {
		event.preventDefault();
		error = '';
		busy = true;
		try {
			const body = mode === 'signup' ? { email, name, password } : { email, password };
			session.user = await api(`/auth/${mode}`, { method: 'POST', body });
			session.loaded = true;
			goto('/');
		} catch (e) {
			error = e.message;
		} finally {
			busy = false;
		}
	}
</script>

<div class="wrap">
	<form class="card stack" onsubmit={submit}>
		<h1>EpitaCampus</h1>
		{#if status?.first_user}
			<p class="muted small">Bienvenue ! Crée le premier compte, il sera administrateur.</p>
		{/if}
		{#if mode === 'signup'}
			<label>Prénom <input bind:value={name} required autocomplete="given-name" /></label>
		{/if}
		<label>E-mail <input type="email" bind:value={email} required autocomplete="email" /></label>
		<label>
			Mot de passe
			<input
				type="password"
				bind:value={password}
				required
				minlength={mode === 'signup' ? 8 : undefined}
				autocomplete={mode === 'signup' ? 'new-password' : 'current-password'}
			/>
		</label>
		{#if error}<p class="error small">{error}</p>{/if}
		<button disabled={busy}>{mode === 'signup' ? 'Créer le compte' : 'Se connecter'}</button>
		{#if status?.signup_open && !status.first_user}
			<button
				type="button"
				class="secondary"
				onclick={() => (mode = mode === 'login' ? 'signup' : 'login')}
			>
				{mode === 'login' ? 'Créer un compte' : "J'ai déjà un compte"}
			</button>
		{/if}
	</form>
</div>

<style>
	.wrap {
		min-height: 100vh;
		display: grid;
		place-items: center;
		padding: 1rem;
	}

	form {
		width: min(380px, 100%);
	}
</style>
