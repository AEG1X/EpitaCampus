<script>
	let token = $state('');
	let secret = $state('');
	let verdict = $state(null);

	function b64urlDecode(part) {
		const b64 = part
			.replace(/-/g, '+')
			.replace(/_/g, '/')
			.padEnd(Math.ceil(part.length / 4) * 4, '=');
		return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
	}

	const decoded = $derived.by(() => {
		const parts = token.trim().split('.');
		if (!token.trim()) return null;
		if (parts.length !== 3) return { error: 'Un JWT contient 3 parties séparées par des points.' };
		try {
			const text = (p) => new TextDecoder().decode(b64urlDecode(p));
			return { header: JSON.parse(text(parts[0])), payload: JSON.parse(text(parts[1])), parts };
		} catch {
			return { error: 'Impossible de décoder ce token (base64url ou JSON invalide).' };
		}
	});

	const TIME_CLAIMS = { exp: 'Expire le', iat: 'Émis le', nbf: 'Valide à partir du' };
	const dateTimeFmt = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'full', timeStyle: 'medium' });

	const expired = $derived(decoded?.payload?.exp ? decoded.payload.exp * 1000 < Date.now() : null);

	const HASHES = { HS256: 'SHA-256', HS384: 'SHA-384', HS512: 'SHA-512' };

	$effect(() => {
		token;
		secret;
		verdict = null;
	});

	async function verify() {
		const hash = HASHES[decoded.header.alg];
		if (!hash) {
			verdict = {
				ok: false,
				text: `Vérification possible uniquement pour HS256/384/512 (ici : ${decoded.header.alg}).`
			};
			return;
		}
		const key = await crypto.subtle.importKey(
			'raw',
			new TextEncoder().encode(secret),
			{ name: 'HMAC', hash },
			false,
			['verify']
		);
		const [h, p, s] = decoded.parts;
		const ok = await crypto.subtle.verify(
			'HMAC',
			key,
			b64urlDecode(s),
			new TextEncoder().encode(`${h}.${p}`)
		);
		verdict = { ok, text: ok ? 'Signature valide ✓' : 'Signature invalide ✗' };
	}
</script>

<header class="page-head">
	<div>
		<h1>Outil JWT</h1>
		<p>Le token n'est jamais envoyé au serveur : tout est calculé dans ton navigateur.</p>
	</div>
</header>
<p class="muted small">
	Le token n'est jamais envoyé au serveur : tout est calculé dans ton navigateur.
</p>

<div class="stack">
	<label>
		Token
		<textarea
			rows="4"
			bind:value={token}
			placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9…"
			spellcheck="false"></textarea>
	</label>

	{#if decoded?.error}
		<p class="error">{decoded.error}</p>
	{:else if decoded}
		<div class="grid">
			<section class="card">
				<h2>En-tête</h2>
				<pre>{JSON.stringify(decoded.header, null, 2)}</pre>
			</section>
			<section class="card">
				<h2>Contenu (payload)</h2>
				<pre>{JSON.stringify(decoded.payload, null, 2)}</pre>
			</section>
		</div>

		<section class="card">
			<h2>Dates</h2>
			<ul class="list">
				{#each Object.entries(TIME_CLAIMS) as [claim, label] (claim)}
					{#if typeof decoded.payload[claim] === 'number'}
						<li>
							{label} :
							<strong>{dateTimeFmt.format(new Date(decoded.payload[claim] * 1000))}</strong>
						</li>
					{/if}
				{/each}
			</ul>
			{#if expired !== null}
				<p class:error={expired} class:ok={!expired}>
					{expired ? 'Ce token est expiré.' : 'Ce token est encore valide.'}
				</p>
			{/if}
		</section>

		<section class="card row">
			<input placeholder="Secret HMAC" bind:value={secret} class="grow" />
			<button onclick={verify} disabled={!secret}>Vérifier la signature</button>
			{#if verdict}<span class:error={!verdict.ok} class:ok={verdict.ok}>{verdict.text}</span>{/if}
		</section>
	{/if}
</div>

<style>
	pre {
		margin: 0;
		white-space: pre-wrap;
		word-break: break-all;
		font-size: 0.85rem;
	}
	textarea {
		font-family: ui-monospace, monospace;
	}
	.grow {
		flex: 1;
	}
	.ok {
		color: var(--success);
	}
</style>
