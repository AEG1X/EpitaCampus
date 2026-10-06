<script>
	import { api } from '#lib/api.js';
	import { daysLabel, formatDate, formatTime, isoDay } from '#lib/format.js';
	import { REVISION_OFFSETS, urgency } from '#lib/planning.js';
	import Icon from '#lib/components/Icon.svelte';

	let data = $state(null);
	let error = $state('');
	let now = $state(new Date());

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
		const timer = setInterval(() => (now = new Date()), 60000);
		return () => clearInterval(timer);
	});

	const greeting = now.getHours() < 18 ? 'Bonjour' : 'Bonsoir';
	const longDate = new Intl.DateTimeFormat('fr-FR', {
		weekday: 'long',
		day: 'numeric',
		month: 'long'
	}).format(now);

	const nextExam = $derived(data?.exams[0]);
	const upcomingToday = $derived(data?.today.filter((e) => new Date(e.end) > now) ?? []);
	const status = (e) =>
		new Date(e.start) <= now && now < new Date(e.end)
			? 'now'
			: new Date(e.end) <= now
				? 'past'
				: 'next';
	const today = isoDay();
</script>

{#if error}
	<p class="error">{error}</p>
{:else if data}
	<header class="page-head">
		<div>
			<h1>{greeting} {data.user.name} 👋</h1>
			<p class="date">{longDate}</p>
		</div>
		<a class="button secondary" href="/calendrier"><Icon name="calendar" /> Voir le planning</a>
	</header>

	<section class="stats">
		<div class="stat card hero" class:calm={!nextExam}>
			<span class="stat-label"><Icon name="flame" size={16} /> Prochain examen</span>
			{#if nextExam}
				<strong class="stat-value">
					{nextExam.days_left === 0 ? "Aujourd'hui" : `J-${nextExam.days_left}`}
				</strong>
				<span class="stat-sub">{nextExam.title}</span>
			{:else}
				<strong class="stat-value">Aucun</strong>
				<span class="stat-sub">Rien de prévu sur 45 jours</span>
			{/if}
		</div>
		<div class="stat card">
			<span class="stat-label"><Icon name="clock" size={16} /> Aujourd'hui</span>
			<strong class="stat-value">{data.today.length}</strong>
			<span class="stat-sub">
				{#if upcomingToday.length}
					prochain à {formatTime(upcomingToday[0].start)}
				{:else}
					{data.today.length ? 'journée terminée' : 'journée libre'}
				{/if}
			</span>
		</div>
		<div class="stat card">
			<span class="stat-label"><Icon name="book" size={16} /> À réviser</span>
			<strong class="stat-value">{data.reviews.length}</strong>
			<span class="stat-sub">cours en attente</span>
		</div>
		<div class="stat card">
			<span class="stat-label"><Icon name="chart" size={16} /> Moyenne</span>
			<strong class="stat-value">
				{data.average !== null ? data.average.toFixed(2) : '—'}<small>/20</small>
			</strong>
			<span class="stat-sub">{data.grade_count} note(s)</span>
		</div>
	</section>

	<div class="columns">
		<section class="card">
			<h2><Icon name="clock" /> Aujourd'hui</h2>
			{#if data.today.length}
				<ol class="timeline">
					{#each data.today as e (e.id)}
						<li class="{e.kind} {status(e)}">
							<span class="time">{formatTime(e.start)}<br /><small>{formatTime(e.end)}</small></span
							>
							<span class="bar"></span>
							<span class="what">
								<strong>{e.title}</strong>
								<span class="small muted row">
									{#if e.location}<Icon name="pin" size={13} /> {e.location}{/if}
									{#if status(e) === 'now'}<span class="badge course">en cours</span>{/if}
									{#if e.kind === 'exam'}<span class="badge exam">examen</span>{/if}
								</span>
							</span>
						</li>
					{/each}
				</ol>
			{:else}
				<div class="empty"><span class="emoji">☀️</span>Rien au programme aujourd'hui.</div>
			{/if}
		</section>

		<section class="card">
			<h2><Icon name="alert" /> Examens à venir</h2>
			{#if data.exams.length}
				<ul class="exams">
					{#each data.exams as e (e.id)}
						<li class="exam {urgency(e.days_left)}">
							<span class="countdown">
								{#if e.days_left === 0}
									<strong>Auj.</strong>
								{:else}
									<small>J-</small><strong>{e.days_left}</strong>
								{/if}
							</span>
							<span class="exam-body">
								<strong>{e.title}</strong>
								<span class="small muted">
									{formatDate(e.start)} · {formatTime(e.start)} · {daysLabel(e.days_left)}
									{#if e.location}· {e.location}{/if}
								</span>
								<span class="sessions">
									{#each REVISION_OFFSETS as offset (offset)}
										{@const d = new Date(e.start)}
										{@const day = isoDay(
											new Date(d.getFullYear(), d.getMonth(), d.getDate() - offset)
										)}
										<span
											class="session"
											class:done={day < today}
											class:today={day === today}
											title="Révision conseillée le {formatDate(day)}"
										>
											{#if day < today}<Icon name="check" size={11} stroke={3} />{/if}
											J-{offset}
										</span>
									{/each}
								</span>
							</span>
						</li>
					{/each}
				</ul>
			{:else}
				<div class="empty">
					<span class="emoji">🎯</span>Aucun examen dans les 45 prochains jours.
					<div class="small">Ajoute-les dans le <a href="/calendrier">planning</a>.</div>
				</div>
			{/if}
		</section>

		<section class="card">
			<h2><Icon name="cap" /> À réviser aujourd'hui</h2>
			{#if data.reviews.length}
				<ul class="list">
					{#each data.reviews as c (c.id)}
						<li class="row review">
							<span class="badge course">{c.subject}</span>
							<span class="grow">{c.title}</span>
							<button class="secondary" onclick={() => reviewed(c.id)}>
								<Icon name="check" size={15} /> Révisé
							</button>
						</li>
					{/each}
				</ul>
			{:else}
				<div class="empty"><span class="emoji">🎉</span>Tu es à jour dans tes révisions.</div>
			{/if}
		</section>

		<section class="card">
			<h2><Icon name="book" /> Derniers cours ajoutés</h2>
			{#if data.recent_courses.length}
				<ul class="list">
					{#each data.recent_courses as c (c.id)}
						<li class="row">
							<span class="badge">{c.subject}</span>
							<a class="grow plain" href="/cours">{c.title}</a>
						</li>
					{/each}
				</ul>
			{:else}
				<div class="empty">
					<span class="emoji">📚</span>Aucun cours pour l'instant.
					<div class="small"><a href="/cours">Ajoute ton premier cours</a></div>
				</div>
			{/if}
		</section>
	</div>
{/if}

<style>
	.date {
		text-transform: capitalize;
	}

	.stats {
		display: grid;
		gap: 1rem;
		grid-template-columns: repeat(4, 1fr);
		margin-bottom: 1rem;
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		min-width: 0;
	}

	.stat-label {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--muted);
	}

	.stat-value {
		font-size: 1.9rem;
		font-weight: 750;
		letter-spacing: -0.02em;
		line-height: 1.2;
		margin-top: 0.35rem;
	}

	.stat-value small {
		font-size: 0.95rem;
		color: var(--muted);
		font-weight: 600;
	}

	.stat-sub {
		font-size: 0.82rem;
		color: var(--muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.hero {
		background: var(--gradient);
		border: 0;
		color: white;
	}

	.hero .stat-label,
	.hero .stat-sub {
		color: rgb(255 255 255 / 0.85);
	}

	.columns {
		display: grid;
		gap: 1rem;
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.timeline {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.timeline li {
		display: grid;
		grid-template-columns: 3.4rem 4px 1fr;
		gap: 0.75rem;
		align-items: stretch;
	}

	.timeline li.past {
		opacity: 0.5;
	}

	.time {
		font-weight: 650;
		font-variant-numeric: tabular-nums;
		line-height: 1.3;
	}

	.time small {
		color: var(--muted);
		font-weight: 500;
	}

	.bar {
		border-radius: 4px;
		background: var(--course);
	}

	.exam .bar,
	li.exam > .bar {
		background: var(--exam);
	}

	li.other > .bar {
		background: var(--other);
	}

	.what {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		padding: 0.1rem 0;
	}

	.what .row {
		gap: 0.3rem;
	}

	.exams {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.exams .exam {
		display: flex;
		gap: 0.9rem;
		align-items: center;
		padding: 0.7rem;
		border-radius: var(--radius-sm);
		background: var(--surface-2);
	}

	.countdown {
		display: flex;
		justify-content: center;
		align-items: center;
		flex-shrink: 0;
		min-width: 3.4rem;
		height: 3.4rem;
		border-radius: 12px;
		background: var(--accent-soft);
		color: var(--accent);
	}

	.countdown strong {
		font-size: 1.35rem;
		font-weight: 800;
	}

	.countdown small {
		font-weight: 700;
	}

	.exam.medium .countdown {
		background: var(--revision-soft);
		color: var(--revision);
	}

	.exam.high .countdown {
		background: var(--exam);
		color: white;
	}

	.exam-body {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		min-width: 0;
	}

	.sessions {
		display: flex;
		gap: 0.3rem;
		margin-top: 0.15rem;
	}

	.session {
		display: inline-flex;
		align-items: center;
		gap: 0.2rem;
		font-size: 0.7rem;
		font-weight: 650;
		padding: 0.08rem 0.45rem;
		border-radius: 999px;
		border: 1px dashed var(--border);
		color: var(--muted);
	}

	.session.done {
		border-style: solid;
		border-color: transparent;
		background: var(--surface-3);
	}

	.session.today {
		border: 0;
		background: var(--revision);
		color: white;
	}

	.review {
		flex-wrap: nowrap;
	}

	.plain {
		color: inherit;
		text-decoration: none;
	}

	.plain:hover {
		color: var(--accent);
	}

	@media (max-width: 1100px) {
		.stats {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (max-width: 760px) {
		.columns {
			grid-template-columns: 1fr;
		}
	}
</style>
