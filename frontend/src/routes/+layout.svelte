<script>
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { api } from '#lib/api.js';
	import { session } from '#lib/session.svelte.js';
	import Icon from '#lib/components/Icon.svelte';

	let { children } = $props();
	let menuOpen = $state(false);

	const links = [
		{ href: '/', label: 'Tableau de bord', icon: 'home' },
		{ href: '/calendrier', label: 'Planning', icon: 'calendar' },
		{ href: '/cours', label: 'Cours', icon: 'book' },
		{ href: '/notes', label: 'Notes', icon: 'chart' },
		{ href: '/outils', label: 'Outils', icon: 'tool' },
		{ href: '/parametres', label: 'Paramètres', icon: 'settings' }
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
			<a class="brand" href="/"><span class="logo"><Icon name="cap" /></span>EpitaCampus</a>
			<button class="ghost" onclick={() => (menuOpen = !menuOpen)} aria-label="Menu">
				<Icon name={menuOpen ? 'x' : 'menu'} size={22} />
			</button>
		</header>
		<nav class:open={menuOpen}>
			<a class="brand desktop" href="/"><span class="logo"><Icon name="cap" /></span>EpitaCampus</a>
			{#each links as link (link.href)}
				<a href={link.href} class="link" class:active={active(link.href)}>
					<Icon name={link.icon} />
					{link.label}
				</a>
			{/each}
			<div class="spacer"></div>
			<div class="user">
				<span class="avatar">{session.user.name.slice(0, 1).toUpperCase()}</span>
				<span class="who">
					<strong>{session.user.name}</strong>
					<span class="small muted email">{session.user.email}</span>
				</span>
				<button class="ghost" onclick={logout} title="Se déconnecter" aria-label="Se déconnecter">
					<Icon name="logout" />
				</button>
			</div>
		</nav>
		<main>
			{@render children()}
		</main>
	</div>
{/if}

<style>
	.shell {
		display: grid;
		grid-template-columns: 248px 1fr;
		min-height: 100vh;
	}

	nav {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		padding: 1.25rem 0.85rem;
		background: var(--surface);
		border-right: 1px solid var(--border);
		position: sticky;
		top: 0;
		height: 100vh;
	}

	.link {
		display: flex;
		align-items: center;
		gap: 0.7rem;
		color: var(--muted);
		text-decoration: none;
		padding: 0.6rem 0.8rem;
		border-radius: var(--radius-sm);
		font-weight: 520;
		transition:
			background 0.15s,
			color 0.15s;
	}

	.link:hover {
		background: var(--surface-2);
		color: var(--text);
	}

	.link.active {
		background: var(--accent-soft);
		color: var(--accent);
		font-weight: 620;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		font-weight: 750;
		font-size: 1.08rem;
		letter-spacing: -0.01em;
		margin: 0 0.4rem 1.4rem;
		color: var(--text);
		text-decoration: none;
	}

	.logo {
		display: grid;
		place-items: center;
		width: 32px;
		height: 32px;
		border-radius: 10px;
		background: var(--gradient);
		color: white;
		box-shadow: 0 4px 12px color-mix(in srgb, var(--accent) 40%, transparent);
	}

	.spacer {
		flex: 1;
	}

	.user {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.6rem;
		border-radius: var(--radius-sm);
		background: var(--surface-2);
		min-width: 0;
	}

	.who {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
		line-height: 1.25;
	}

	.email {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.avatar {
		display: grid;
		place-items: center;
		width: 34px;
		height: 34px;
		border-radius: 50%;
		background: var(--gradient);
		color: white;
		font-weight: 700;
		flex-shrink: 0;
	}

	main {
		padding: 2.25rem 2.5rem;
		max-width: 1320px;
		width: 100%;
		min-width: 0;
	}

	.topbar {
		display: none;
	}

	@media (max-width: 860px) {
		.shell {
			grid-template-columns: 1fr;
		}

		.topbar {
			display: flex;
			justify-content: space-between;
			align-items: center;
			padding: 0.7rem 1rem;
			background: color-mix(in srgb, var(--surface) 85%, transparent);
			backdrop-filter: blur(12px);
			border-bottom: 1px solid var(--border);
			position: sticky;
			top: 0;
			z-index: 20;
		}

		.topbar .brand {
			margin: 0;
		}

		nav {
			display: none;
			height: auto;
			position: sticky;
			top: 57px;
			z-index: 19;
			border-right: 0;
			border-bottom: 1px solid var(--border);
			box-shadow: var(--shadow-lg);
		}

		nav.open {
			display: flex;
		}

		.desktop {
			display: none;
		}

		.spacer {
			height: 0.75rem;
		}

		main {
			padding: 1.25rem 1rem 2rem;
		}
	}
</style>
