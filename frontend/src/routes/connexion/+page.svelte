<script>
	import { goto } from '$app/navigation';
	import { api } from '#lib/api.js';
	import { session } from '#lib/session.svelte.js';
	import Icon from '#lib/components/Icon.svelte';

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
		<div class="brand">
			<span class="logo"><Icon name="cap" size={26} /></span>
			<h1>EpitaCampus</h1>
			<p class="muted small">Tes cours, ton planning et tes notes au même endroit.</p>
		</div>
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
		background:
			radial-gradient(
				60rem 30rem at 10% -10%,
				color-mix(in srgb, var(--accent) 22%, transparent),
				transparent
			),
			radial-gradient(
				50rem 30rem at 110% 110%,
				color-mix(in srgb, var(--accent-2) 20%, transparent),
				transparent
			),
			var(--bg);
	}

	form {
		width: min(400px, 100%);
		padding: 2rem;
		box-shadow: var(--shadow-lg);
	}

	.brand {
		text-align: center;
		margin-bottom: 0.5rem;
	}

	.brand p {
		margin: 0.3rem 0 0;
	}

	.logo {
		display: inline-grid;
		place-items: center;
		width: 52px;
		height: 52px;
		border-radius: 16px;
		background: var(--gradient);
		color: white;
		margin-bottom: 0.75rem;
		box-shadow: 0 8px 24px color-mix(in srgb, var(--accent) 45%, transparent);
	}
</style>
