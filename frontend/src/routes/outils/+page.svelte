<script>
	import Icon from '#lib/components/Icon.svelte';
	const tools = [
		{
			href: '/outils/pdf',
			title: 'PDF',
			text: 'Fusionner, extraire des pages, faire pivoter. Tout se passe dans ton navigateur.'
		},
		{
			href: '/outils/jwt',
			title: 'JWT',
			text: 'Décoder un token, vérifier sa signature HMAC et sa date d’expiration.'
		},
		{
			href: '/outils/pomodoro',
			title: 'Minuteur Pomodoro',
			text: 'Sessions de 25 min de travail et 5 min de pause pour réviser.'
		}
	];
</script>

<header class="page-head">
	<div>
		<h1>Outils</h1>
		<p>Des utilitaires qui tournent dans ton navigateur.</p>
	</div>
</header>
<div class="grid">
	{#each tools as tool (tool.href)}
		<a class="card tool" href={tool.href}>
			<span class="tool-icon"><Icon name={tool.icon} size={22} /></span>
			<h2>{tool.title}</h2>
			<p class="muted small">{tool.text}</p>
		</a>
	{/each}
</div>

<style>
	.tool {
		color: inherit;
		text-decoration: none;
	}
	.tool {
		transition:
			transform 0.15s,
			border-color 0.15s;
	}
	.tool:hover {
		border-color: var(--accent);
		transform: translateY(-2px);
	}
	.tool-icon {
		display: grid;
		place-items: center;
		width: 44px;
		height: 44px;
		border-radius: 12px;
		background: var(--accent-soft);
		color: var(--accent);
		margin-bottom: 0.8rem;
	}
</style>
