<script>
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

<h1>Outils</h1>
<div class="grid">
	{#each tools as tool (tool.href)}
		<a class="card tool" href={tool.href}>
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
	.tool:hover {
		border-color: var(--accent);
	}
</style>
