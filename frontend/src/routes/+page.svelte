<script>
	import { api } from '#lib/api.js';
	import { daysLabel, formatDate, formatTime } from '#lib/format.js';

	let data = $state(null);
	let error = $state('');

	async function load() {
		try {
			data = await api('/dashboard');
		} catch (e) {
			error = e.message;
		}
	}

	async function reviewed(id) {
		await api(`/courses/${id}/review`, { method: 'POST' });
		load();
	}

	$effect(() => {
		load();
	});

	const hour = new Date().getHours();
	const greeting = hour < 18 ? 'Bonjour' : 'Bonsoir';
</script>

{#if error}
	<p class="error">{error}</p>
{:else if data}
	<h1>{greeting} {data.user.name} 👋</h1>

	<div class="grid">
		<section class="card">
			<h2>Aujourd'hui</h2>
			{#if data.today.length}
				<ul class="list">
					{#each data.today as e (e.id)}
						<li>
							<strong>{formatTime(e.start)}–{formatTime(e.end)}</strong>
							{e.title}
							<span class="badge {e.kind}">{e.kind === 'exam' ? 'examen' : 'cours'}</span>
							{#if e.location}<div class="small muted">{e.location}</div>{/if}
						</li>
					{/each}
				</ul>
			{:else}
				<p class="muted">Rien au programme aujourd'hui.</p>
			{/if}
			<a class="small" href="/calendrier">Voir le calendrier →</a>
		</section>

		<section class="card">
			<h2>Examens à venir</h2>
			{#if data.exams.length}
				<ul class="list">
					{#each data.exams as e (e.id)}
						<li class:urgent={e.revise_today}>
							<strong>{e.title}</strong>
							<div class="small muted">
								{formatDate(e.start)} à {formatTime(e.start)} · {daysLabel(e.days_left)}
							</div>
							{#if e.revise_today}
								<div class="small revise">📚 Session de révision conseillée aujourd'hui</div>
							{:else if e.revision_dates.length}
								<div class="small muted">
									Révisions conseillées : {e.revision_dates.map(formatDate).join(', ')}
								</div>
							{/if}
						</li>
					{/each}
				</ul>
			{:else}
				<p class="muted">Aucun examen dans les 45 prochains jours.</p>
			{/if}
		</section>

		<section class="card">
			<h2>À réviser</h2>
			{#if data.reviews.length}
				<ul class="list">
					{#each data.reviews as c (c.id)}
						<li class="row spread">
							<span><span class="badge">{c.subject}</span> {c.title}</span>
							<button class="secondary small" onclick={() => reviewed(c.id)}>Révisé ✓</button>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="muted">Tu es à jour dans tes révisions 🎉</p>
			{/if}
		</section>

		<section class="card">
			<h2>Moyenne générale</h2>
			{#if data.average !== null}
				<p class="big">{data.average.toFixed(2)}<span class="muted">/20</span></p>
				<p class="small muted">Sur {data.grade_count} note(s)</p>
			{:else}
				<p class="muted">Aucune note pour l'instant.</p>
			{/if}
			<a class="small" href="/notes">Voir mes notes →</a>
		</section>

		<section class="card">
			<h2>Derniers cours ajoutés</h2>
			{#if data.recent_courses.length}
				<ul class="list">
					{#each data.recent_courses as c (c.id)}
						<li><span class="badge">{c.subject}</span> {c.title}</li>
					{/each}
				</ul>
			{:else}
				<p class="muted">Aucun cours. <a href="/cours">Ajoute ton premier cours</a>.</p>
			{/if}
		</section>
	</div>
{/if}

<style>
	.big {
		font-size: 2.4rem;
		font-weight: 700;
		margin: 0;
	}

	.spread {
		justify-content: space-between;
		flex-wrap: nowrap;
	}

	.urgent strong {
		color: var(--exam);
	}

	.revise {
		color: var(--warning);
		font-weight: 600;
	}
</style>
