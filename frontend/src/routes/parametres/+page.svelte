<script>
	import { api } from '#lib/api.js';

	let sources = $state([]);
	let name = $state('Zeus');
	let url = $state('');
	let busy = $state(false);
	let error = $state('');

	const dateTimeFmt = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short', timeStyle: 'short' });

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

<h1>Paramètres</h1>

<section class="card stack">
	<h2>Calendriers synchronisés</h2>
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

<style>
	.grow {
		flex: 1;
	}

	.url {
		word-break: break-all;
		max-width: 420px;
	}
</style>
