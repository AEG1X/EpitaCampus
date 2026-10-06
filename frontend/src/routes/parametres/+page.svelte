<script>
	import { api } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';

	let sources = $state([]);
	let name = $state('Zeus');
	let url = $state('');
	let busy = $state(false);
	let error = $state('');

	const dateTimeFmt = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short', timeStyle: 'short' });

	let pwd = $state({ current_password: '', new_password: '', confirm: '' });
	let pwdMessage = $state(null);

	async function changePassword(e) {
		e.preventDefault();
		pwdMessage = null;
		if (pwd.new_password !== pwd.confirm) {
			pwdMessage = { ok: false, text: 'Les deux nouveaux mots de passe ne correspondent pas' };
			return;
		}
		try {
			await api('/auth/password', {
				method: 'POST',
				body: { current_password: pwd.current_password, new_password: pwd.new_password }
			});
			pwd = { current_password: '', new_password: '', confirm: '' };
			pwdMessage = {
				ok: true,
				text: 'Mot de passe changé. Tes autres appareils ont été déconnectés.'
			};
		} catch (err) {
			pwdMessage = { ok: false, text: err.message };
		}
	}

	async function load() {
		sources = await api('/calendar/sources');
	}

	$effect(() => {
		load();
	});

	async function add(e) {
		e.preventDefault();
		busy = true;
		error = '';
		try {
			await api('/calendar/sources', { method: 'POST', body: { name, url } });
			url = '';
			await load();
		} catch (err) {
			error = err.message;
		} finally {
			busy = false;
		}
	}

	async function sync(source) {
		busy = true;
		await api(`/calendar/sources/${source.id}/sync`, { method: 'POST' });
		await load();
		busy = false;
	}

	async function remove(source) {
		if (!confirm(`Retirer le calendrier « ${source.name} » et ses événements ?`)) return;
		await api(`/calendar/sources/${source.id}`, { method: 'DELETE' });
		load();
	}
</script>

<header class="page-head">
	<div>
		<h1>Paramètres</h1>
		<p>Calendriers synchronisés et sécurité de ton compte.</p>
	</div>
</header>

<div class="stack">
	<section class="card stack">
		<h2><Icon name="calendar" /> Calendriers synchronisés</h2>
		<p class="small muted">
			Colle ici le lien ICS de ton emploi du temps (sur Zeus : choisis ton groupe puis copie le lien
			d'export ICS / iCal). Le site le resynchronise automatiquement toutes les 30 minutes. Un lien
			Google Agenda ou Outlook fonctionne aussi.
		</p>

		{#if sources.length}
			<div class="table-wrap">
				<table>
					<thead>
						<tr><th>Nom</th><th>Dernière synchro</th><th></th></tr>
					</thead>
					<tbody>
						{#each sources as s (s.id)}
							<tr>
								<td>
									{s.name}
									<div class="small muted url">{s.url}</div>
								</td>
								<td>
									{s.last_sync ? dateTimeFmt.format(new Date(s.last_sync)) : 'jamais'}
									{#if s.last_error}<div class="small error">{s.last_error}</div>{/if}
								</td>
								<td class="row">
									<button class="secondary" disabled={busy} onclick={() => sync(s)}>
										Synchroniser
									</button>
									<button class="danger" onclick={() => remove(s)}>Retirer</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}

		<form class="row" onsubmit={add}>
			<input placeholder="Nom" bind:value={name} required />
			<input
				placeholder="https://… .ics"
				bind:value={url}
				required
				pattern="(https?|webcal)://.+"
				class="grow"
			/>
			<button disabled={busy}>{busy ? 'Import…' : 'Ajouter'}</button>
		</form>
		{#if error}<p class="error small">{error}</p>{/if}
	</section>

	<section class="card stack">
		<h2><Icon name="lock" /> Mot de passe</h2>
		<p class="small muted">
			Ton mot de passe est stocké haché avec Argon2 : personne ne peut le relire. Le changer
			déconnecte tous tes autres appareils.
		</p>
		<form class="pwd" onsubmit={changePassword}>
			<label>
				Mot de passe actuel
				<input
					type="password"
					bind:value={pwd.current_password}
					required
					autocomplete="current-password"
				/>
			</label>
			<label>
				Nouveau (8 caractères min.)
				<input
					type="password"
					bind:value={pwd.new_password}
					required
					minlength="8"
					autocomplete="new-password"
				/>
			</label>
			<label>
				Confirmation
				<input
					type="password"
					bind:value={pwd.confirm}
					required
					minlength="8"
					autocomplete="new-password"
				/>
			</label>
			<button>Changer</button>
		</form>
		{#if pwdMessage}<p class="small" class:ok={pwdMessage.ok} class:error={!pwdMessage.ok}>
				{pwdMessage.text}
			</p>{/if}
	</section>
</div>

<style>
	.grow {
		flex: 1;
	}

	.pwd {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 0.75rem;
		align-items: end;
	}

	.url {
		word-break: break-all;
		max-width: 420px;
	}
</style>
