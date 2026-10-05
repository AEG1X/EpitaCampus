<script>
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { api } from '#lib/api.js';
	import { session } from '#lib/session.svelte.js';

	let { children } = $props();
	let menuOpen = $state(false);

	const links = [
		{ href: '/', label: 'Tableau de bord' },
		{ href: '/cours', label: 'Cours' },
		{ href: '/calendrier', label: 'Calendrier' },
		{ href: '/notes', label: 'Notes' },
		{ href: '/outils', label: 'Outils' },
		{ href: '/parametres', label: 'Paramètres' }
	];

	const isPublic = $derived(page.url.pathname === '/connexion');

	$effect(() => {
		if (session.loaded) return;
		api('/auth/me')
			.then((user) => {
				session.user = user;
			})
			.catch(() => {
				session.user = null;
			})
			.finally(() => {
				session.loaded = true;
			});
	});

	$effect(() => {
		if (session.loaded && !session.user && !isPublic) goto('/connexion');
	});

	$effect(() => {
		page.url.pathname;
		menuOpen = false;
	});

	async function logout() {
		await api('/auth/logout', { method: 'POST' });
		session.user = null;
		goto('/connexion');
	}

	function active(href) {
		return href === '/' ? page.url.pathname === '/' : page.url.pathname.startsWith(href);
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>EpitaCampus</title>
</svelte:head>

{#if isPublic}
	{@render children()}
{:else if session.user}
	<div class="shell">
		<header class="topbar">
			<a class="brand" href="/">EpitaCampus</a>
			<button class="secondary menu-btn" onclick={() => (menuOpen = !menuOpen)} aria-label="Menu">
				☰
			</button>
		</header>
		<nav class:open={menuOpen}>
			<a class="brand desktop" href="/">EpitaCampus</a>
			{#each links as link (link.href)}
				<a href={link.href} class:active={active(link.href)}>{link.label}</a>
			{/each}
			<div class="spacer"></div>
			<div class="who small muted">{session.user.name}</div>
			<button class="secondary" onclick={logout}>Se déconnecter</button>
		</nav>
		<main>
			{@render children()}
		</main>
	</div>
{/if}

<style>
	.shell {
		display: grid;
		grid-template-columns: 220px 1fr;
		min-height: 100vh;
	}

	nav {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		padding: 1.25rem 0.75rem;
		background: var(--surface);
		border-right: 1px solid var(--border);
		position: sticky;
		top: 0;
		height: 100vh;
	}

	nav a {
		color: var(--text);
		text-decoration: none;
		padding: 0.5rem 0.75rem;
		border-radius: 8px;
	}

	nav a:hover {
		background: var(--surface-2);
	}

	nav a.active {
		background: color-mix(in srgb, var(--accent) 15%, transparent);
		color: var(--accent);
		font-weight: 600;
	}

	.brand {
		font-weight: 700;
		font-size: 1.1rem;
		margin-bottom: 1rem;
		color: var(--text);
		text-decoration: none;
	}

	nav a.brand:hover {
		background: none;
	}

	.spacer {
		flex: 1;
	}

	.who {
		padding: 0 0.75rem 0.5rem;
	}

	main {
		padding: 2rem;
		max-width: 1200px;
		width: 100%;
	}

	.topbar {
		display: none;
	}

	@media (max-width: 800px) {
		.shell {
			grid-template-columns: 1fr;
		}

		.topbar {
			display: flex;
			justify-content: space-between;
			align-items: center;
			padding: 0.75rem 1rem;
			background: var(--surface);
			border-bottom: 1px solid var(--border);
			position: sticky;
			top: 0;
			z-index: 10;
		}

		.topbar .brand {
			margin: 0;
		}

		nav {
			display: none;
			height: auto;
			position: static;
			border-right: 0;
			border-bottom: 1px solid var(--border);
		}

		nav.open {
			display: flex;
		}

		.desktop {
			display: none;
		}

		main {
			padding: 1rem;
		}
	}
</style>
