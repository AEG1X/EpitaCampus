<script>
	import { PDFDocument, degrees } from 'pdf-lib';

	let files = $state([]); // [{ name, bytes, pages }]
	let mode = $state('merge');
	let range = $state('');
	let rotation = $state(90);
	let error = $state('');
	let busy = $state(false);

	async function addFiles(list) {
		error = '';
		for (const file of list) {
			try {
				const bytes = new Uint8Array(await file.arrayBuffer());
				const doc = await PDFDocument.load(bytes, { ignoreEncryption: true });
				files.push({ name: file.name, bytes, pages: doc.getPageCount() });
			} catch {
				error = `${file.name} n'est pas un PDF lisible.`;
			}
		}
	}

	function move(i, delta) {
		const j = i + delta;
		if (j < 0 || j >= files.length) return;
		[files[i], files[j]] = [files[j], files[i]];
	}

	/** Transforme "1-3, 5" en indices [0, 1, 2, 4]. */
	function parseRange(text, max) {
		const pages = [];
		for (const part of text
			.split(',')
			.map((s) => s.trim())
			.filter(Boolean)) {
			const [a, b] = part.split('-').map((n) => parseInt(n, 10));
			const end = Number.isNaN(b) || b === undefined ? a : b;
			if (Number.isNaN(a) || a < 1 || end > max || end < a)
				throw new Error(`Plage invalide : « ${part} » (1 à ${max})`);
			for (let p = a; p <= end; p++) pages.push(p - 1);
		}
		return pages;
	}

	function download(bytes, name) {
		const url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }));
		const a = Object.assign(document.createElement('a'), { href: url, download: name });
		a.click();
		setTimeout(() => URL.revokeObjectURL(url), 1000);
	}

	const baseName = (name) => name.replace(/\.pdf$/i, '');

	async function run() {
		error = '';
		busy = true;
		try {
			if (mode === 'merge') {
				const out = await PDFDocument.create();
				for (const f of files) {
					const src = await PDFDocument.load(f.bytes, { ignoreEncryption: true });
					for (const page of await out.copyPages(src, src.getPageIndices())) out.addPage(page);
				}
				download(await out.save(), 'fusion.pdf');
			} else {
				const f = files[0];
				const src = await PDFDocument.load(f.bytes, { ignoreEncryption: true });
				const selected = range.trim() ? parseRange(range, f.pages) : src.getPageIndices();
				if (mode === 'extract') {
					const out = await PDFDocument.create();
					for (const page of await out.copyPages(src, selected)) out.addPage(page);
					download(await out.save(), `${baseName(f.name)}-extrait.pdf`);
				} else {
					for (const i of selected) {
						const page = src.getPage(i);
						page.setRotation(degrees((page.getRotation().angle + rotation) % 360));
					}
					download(await src.save(), `${baseName(f.name)}-pivote.pdf`);
				}
			}
		} catch (e) {
			error = e.message;
		} finally {
			busy = false;
		}
	}

	const canRun = $derived(mode === 'merge' ? files.length >= 2 : files.length >= 1);
</script>

<header class="page-head">
	<div>
		<h1>Outils PDF</h1>
		<p>Les fichiers restent sur ton appareil : rien n'est envoyé au serveur.</p>
	</div>
</header>

<div class="stack">
	<div class="row">
		<button class:secondary={mode !== 'merge'} onclick={() => (mode = 'merge')}>Fusionner</button>
		<button class:secondary={mode !== 'extract'} onclick={() => (mode = 'extract')}
			>Extraire des pages</button
		>
		<button class:secondary={mode !== 'rotate'} onclick={() => (mode = 'rotate')}>Pivoter</button>
	</div>

	<label class="drop card">
		Glisse tes PDF ici ou clique pour choisir
		<input
			type="file"
			accept="application/pdf"
			multiple
			onchange={(e) => addFiles(e.currentTarget.files)}
		/>
	</label>

	{#if files.length}
		<section class="card">
			<ul class="list">
				{#each files as f, i (f)}
					<li class="row">
						<span class="grow"
							>{i + 1}. {f.name} <span class="small muted">({f.pages} pages)</span></span
						>
						{#if mode === 'merge'}
							<button class="secondary" onclick={() => move(i, -1)} aria-label="Monter">↑</button>
							<button class="secondary" onclick={() => move(i, 1)} aria-label="Descendre">↓</button>
						{/if}
						<button class="danger" onclick={() => files.splice(i, 1)}>Retirer</button>
					</li>
				{/each}
			</ul>
			{#if mode !== 'merge' && files.length > 1}
				<p class="small muted">Seul le premier fichier sera utilisé.</p>
			{/if}
		</section>
	{/if}

	{#if mode !== 'merge'}
		<div class="row">
			<label>
				Pages (ex : 1-3, 7) — vide = toutes
				<input bind:value={range} placeholder="1-3, 7" />
			</label>
			{#if mode === 'rotate'}
				<label>
					Rotation
					<select bind:value={rotation}>
						<option value={90}>90° horaire</option>
						<option value={180}>180°</option>
						<option value={270}>90° anti-horaire</option>
					</select>
				</label>
			{/if}
		</div>
	{/if}

	{#if error}<p class="error">{error}</p>{/if}
	<div>
		<button onclick={run} disabled={!canRun || busy}
			>{busy ? 'Traitement…' : 'Télécharger le résultat'}</button
		>
	</div>
</div>

<style>
	.drop {
		border-style: dashed;
		text-align: center;
		padding: 2rem;
		cursor: pointer;
		position: relative;
	}
	.drop input {
		position: absolute;
		inset: 0;
		opacity: 0;
		cursor: pointer;
	}
	.grow {
		flex: 1;
	}
</style>
