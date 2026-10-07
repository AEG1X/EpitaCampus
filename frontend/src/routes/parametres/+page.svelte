<script>
	import { api } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';
	import { readQr } from '#lib/qr.js';

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

	let moodle = $state(null);
	let moodleForm = $state({ base_url: 'https://moodle.epita.fr', token: '' });
	let moodleError = $state('');
	let moodleBusy = $state(false);

	const launchUrl = $derived(
		`${moodleForm.base_url.replace(/\/$/, '')}/admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=${Math.floor(Math.random() * 1e9)}&urlscheme=moodlemobile`
	);

	let qrBusy = $state(false);

	async function connectWithQr(blob) {
		moodleError = '';
		qrBusy = true;
		try {
			const text = await readQr(blob);
			if (!text)
				throw new Error('Aucun QR code trouvé dans cette image, recadre la capture sur le QR code');
			moodle = await api('/moodle/qr', { method: 'PUT', body: { qr_text: text } });
			setTimeout(loadMoodle, 3000);
		} catch (err) {
			moodleError = err.message;
		} finally {
			qrBusy = false;
		}
	}

	function onPaste(event) {
		if (moodle?.connected) return;
		const item = [...(event.clipboardData?.items ?? [])].find((i) => i.type.startsWith('image/'));
		if (item) {
			event.preventDefault();
			connectWithQr(item.getAsFile());
		}
	}

	function onDrop(event) {
		event.preventDefault();
		const file = event.dataTransfer?.files?.[0];
		if (file) connectWithQr(file);
	}

	let copied = $state(false);

	async function copyLaunch() {
		try {
			await navigator.clipboard.writeText(launchUrl);
			copied = true;
		} catch {
			// Le presse-papiers n'est pas disponible hors HTTPS : on affiche le lien à copier.
			prompt('Copie ce lien :', launchUrl);
		}
		setTimeout(() => (copied = false), 3000);
	}

	async function loadMoodle() {
		moodle = await api('/moodle');
		// Pendant une synchro, on rafraîchit l'état toutes les 3 secondes.
		if (moodle.syncing) setTimeout(loadMoodle, 3000);
	}

	async function connectMoodle(e) {
		e.preventDefault();
		moodleBusy = true;
		moodleError = '';
		try {
			moodle = await api('/moodle', { method: 'PUT', body: moodleForm });
			moodleForm.token = '';
			setTimeout(loadMoodle, 3000);
		} catch (err) {
			moodleError = err.message;
		} finally {
			moodleBusy = false;
		}
	}

	async function syncMoodle() {
		moodle = await api('/moodle/sync', { method: 'POST' });
		setTimeout(loadMoodle, 3000);
	}

	async function disconnectMoodle() {
		if (!confirm('Retirer la clé Moodle ? Les cours et fichiers déjà importés sont conservés.'))
			return;
		await api('/moodle', { method: 'DELETE' });
		loadMoodle();
	}

	$effect(() => {
		loadMoodle();
	});

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

<svelte:window onpaste={onPaste} />

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
		<h2><Icon name="book" /> Moodle</h2>
		{#if moodle?.connected}
			<div class="row">
				<span class="badge ok-badge"><Icon name="check" size={12} stroke={3} /> Connecté</span>
				<strong>{moodle.site_name || moodle.base_url}</strong>
				<span class="small muted">{moodle.courses} cours · {moodle.files} fichiers importés</span>
			</div>
			<p class="small muted">
				{#if moodle.syncing}
					Synchronisation en cours… (la première peut prendre quelques minutes)
				{:else if moodle.last_sync}
					Dernière synchro : {dateTimeFmt.format(new Date(moodle.last_sync))}. Le site revérifie
					Moodle toutes les 6 heures.
				{/if}
			</p>
			{#if moodle.last_error}<p class="small error">{moodle.last_error}</p>{/if}
			<div class="row">
				<button class="secondary" disabled={moodle.syncing} onclick={syncMoodle}>
					{moodle.syncing ? 'Synchro en cours…' : 'Synchroniser maintenant'}
				</button>
				<button class="danger" onclick={disconnectMoodle}>Déconnecter</button>
			</div>
		{:else if moodle}
			<ol class="small muted steps">
				<li>
					Ouvre
					<a
						href="{moodleForm.base_url.replace(/\/$/, '')}/user/profile.php"
						target="_blank"
						rel="noopener"
					>
						ton profil Moodle</a
					>
					et descends jusqu'à la partie <strong>Application mobile</strong> : un QR code s'affiche.
				</li>
				<li>
					Fais une capture du QR code avec <strong>Cmd + Ctrl + Maj + 4</strong> (elle va directement
					dans le presse-papiers).
				</li>
				<li>Reviens ici et appuie sur <strong>Cmd + V</strong>. C'est tout.</li>
			</ol>
			<label
				class="drop"
				class:busy={qrBusy}
				ondragover={(e) => e.preventDefault()}
				ondrop={onDrop}
			>
				{qrBusy ? 'Connexion à Moodle…' : 'Colle (Cmd+V) ou dépose ici la capture du QR code'}
				<input
					type="file"
					accept="image/*"
					onchange={(e) => e.currentTarget.files[0] && connectWithQr(e.currentTarget.files[0])}
				/>
			</label>
			<p class="small muted">
				Le QR code expire au bout de 10 minutes et doit être affiché sur le même réseau que ce site.
			</p>
			<details class="small">
				<summary class="muted">Autre méthode (clé manuelle, avancé)</summary>
				<ol class="small muted steps manual">
					<li>
						<button type="button" class="secondary copy" onclick={copyLaunch}>
							{copied ? 'Lien copié ✓' : 'Copier le lien de connexion Moodle'}
						</button>
					</li>
					<li>Ouvre un <strong>nouvel onglet vide</strong> (Cmd+T).</li>
					<li>
						Dans cet onglet vide, ouvre l'inspecteur (Cmd+Option+I), onglet <strong>Réseau</strong>,
						filtre <strong>Tout</strong>.
					</li>
					<li>
						Clique dans la barre d'adresse, colle le lien (Cmd+V) et appuie sur Entrée. Connecte-toi
						avec Forge ID si besoin. L'erreur « adresse pas valide » est normale : clique OK.
					</li>
					<li>
						Dans Réseau, clique sur <strong>launch.php</strong> et copie la valeur de
						<strong>Location</strong> (elle commence par <code>moodlemobile://token=</code>).
					</li>
					<li>Colle-la ci-dessous et clique Connecter. Elle est vérifiée puis stockée chiffrée.</li>
				</ol>
				<form class="row" onsubmit={connectMoodle}>
					<input
						bind:value={moodleForm.base_url}
						required
						pattern="https://.+"
						placeholder="https://moodle…"
					/>
					<input
						type="password"
						bind:value={moodleForm.token}
						required
						minlength="10"
						placeholder="moodlemobile://token=… ou clé"
						autocomplete="off"
						class="grow"
					/>
					<button disabled={moodleBusy}>{moodleBusy ? 'Vérification…' : 'Connecter'}</button>
				</form>
			</details>
			{#if moodleError}<p class="error small">{moodleError}</p>{/if}
		{/if}
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

	.steps {
		margin: 0;
		padding-left: 1.2rem;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.drop {
		position: relative;
		display: block;
		text-align: center;
		padding: 1.5rem 1rem;
		border: 2px dashed var(--border);
		border-radius: var(--radius-sm);
		color: var(--muted);
		font-size: 0.95rem;
		cursor: pointer;
	}

	.drop:hover {
		border-color: var(--accent);
		color: var(--accent);
	}

	.drop.busy {
		border-color: var(--accent);
		color: var(--accent);
	}

	.drop input {
		position: absolute;
		inset: 0;
		opacity: 0;
		cursor: pointer;
	}

	details {
		margin-top: 0.25rem;
	}

	details[open] {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	summary {
		cursor: pointer;
	}

	.copy {
		margin: 0.2rem 0;
	}

	.ok-badge {
		background: color-mix(in srgb, var(--success) 15%, transparent);
		color: var(--success);
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
