<script>
	import { api } from '#lib/api.js';
	import { formatDate, formatTime, isoDay } from '#lib/format.js';
	import { daysUntil, revisionSessions, urgency } from '#lib/planning.js';
	import Icon from '#lib/components/Icon.svelte';

	const KIND_LABELS = { course: 'Cours', exam: 'Examen', other: 'Autre' };
	const VIEWS = [
		{ id: 'week', label: 'Semaine', icon: 'columns' },
		{ id: 'month', label: 'Mois', icon: 'grid' },
		{ id: 'list', label: 'Liste', icon: 'list' }
	];
	const HOUR_PX = 52;
	const weekdayFmt = new Intl.DateTimeFormat('fr-FR', { weekday: 'short' });
	const monthFmt = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' });
	const longDayFmt = new Intl.DateTimeFormat('fr-FR', {
		weekday: 'long',
		day: 'numeric',
		month: 'long'
	});

	function startOfDay(d) {
		const x = new Date(d);
		x.setHours(0, 0, 0, 0);
		return x;
	}
	function addDays(d, n) {
		const x = new Date(d);
		x.setDate(x.getDate() + n);
		return x;
	}
	function mondayOf(d) {
		const x = startOfDay(d);
		return addDays(x, -((x.getDay() + 6) % 7));
	}

	let view = $state(typeof window !== 'undefined' && window.innerWidth < 760 ? 'list' : 'week');
	let cursor = $state(startOfDay(new Date()));
	let events = $state([]);
	let upcomingExams = $state([]);
	let selected = $state(null);
	let showForm = $state(false);
	let form = $state({
		title: '',
		day: isoDay(),
		start: '09:00',
		end: '11:00',
		kind: 'exam',
		location: ''
	});
	let error = $state('');
	let now = $state(new Date());

	// Période affichée selon la vue.
	const range = $derived.by(() => {
		if (view === 'week') {
			const start = mondayOf(cursor);
			return { start, end: addDays(start, 7) };
		}
		if (view === 'month') {
			const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
			const start = mondayOf(first);
			return { start, end: addDays(start, 42) };
		}
		const start = startOfDay(cursor);
		return { start, end: addDays(start, 30) };
	});

	const days = $derived(
		Array.from({ length: Math.round((range.end - range.start) / 86400000) }, (_, i) =>
			addDays(range.start, i)
		)
	);

	const sessionsByDay = $derived.by(() => {
		const map = {};
		for (const s of revisionSessions(upcomingExams)) (map[s.day] ??= []).push(s);
		return map;
	});

	const eventsByDay = $derived.by(() => {
		const map = {};
		for (const e of events) (map[isoDay(new Date(e.start))] ??= []).push(e);
		return map;
	});

	// Plage horaire de la grille : 8h-20h, élargie si un événement déborde.
	const hours = $derived.by(() => {
		let min = 8;
		let max = 20;
		for (const e of events) {
			const s = new Date(e.start);
			const en = new Date(e.end);
			min = Math.min(min, s.getHours());
			max = Math.max(max, en.getHours() + (en.getMinutes() ? 1 : 0));
		}
		return { min, max: Math.min(max, 24) };
	});

	/** Place les événements qui se chevauchent côte à côte. */
	function layoutDay(list) {
		const sorted = [...list].sort((a, b) => new Date(a.start) - new Date(b.start));
		const placed = [];
		let group = [];
		let groupEnd = 0;
		const flush = () => {
			const cols = Math.max(...group.map((g) => g.col)) + 1;
			for (const g of group) g.cols = cols;
			group = [];
		};
		for (const e of sorted) {
			const s = new Date(e.start).getTime();
			const en = Math.max(new Date(e.end).getTime(), s + 15 * 60000);
			if (group.length && s >= groupEnd) flush();
			const used = new Set(group.filter((g) => g.end > s).map((g) => g.col));
			let col = 0;
			while (used.has(col)) col++;
			const item = { event: e, col, cols: 1, end: en };
			group.push(item);
			placed.push(item);
			groupEnd = Math.max(groupEnd, en);
		}
		if (group.length) flush();
		return placed;
	}

	function position(e) {
		const s = new Date(e.start);
		const en = new Date(e.end);
		const top = (s.getHours() - hours.min + s.getMinutes() / 60) * HOUR_PX;
		const height = Math.max(((en - s) / 3600000) * HOUR_PX, 22);
		return `top:${top}px;height:${height - 2}px`;
	}

	const nowTop = $derived((now.getHours() - hours.min + now.getMinutes() / 60) * HOUR_PX);

	const title = $derived.by(() => {
		if (view === 'month') return monthFmt.format(cursor);
		if (view === 'week') {
			const end = addDays(range.start, 6);
			return `${range.start.getDate()} – ${end.getDate()} ${monthFmt.format(end)}`;
		}
		return `À partir du ${longDayFmt.format(cursor)}`;
	});

	async function load() {
		const params = new URLSearchParams({
			start: range.start.toISOString(),
			end: range.end.toISOString()
		});
		events = await api(`/calendar/events?${params}`);
	}

	async function loadExams() {
		const start = startOfDay(new Date());
		const params = new URLSearchParams({
			start: start.toISOString(),
			end: addDays(start, 90).toISOString()
		});
		upcomingExams = (await api(`/calendar/events?${params}`)).filter((e) => e.kind === 'exam');
	}

	$effect(() => {
		range;
		load();
	});

	$effect(() => {
		loadExams();
		const timer = setInterval(() => (now = new Date()), 60000);
		return () => clearInterval(timer);
	});

	function shift(dir) {
		if (view === 'month') cursor = new Date(cursor.getFullYear(), cursor.getMonth() + dir, 1);
		else cursor = addDays(cursor, dir * (view === 'week' ? 7 : 30));
	}

	async function setKind(event, kind) {
		const updated = await api(`/calendar/events/${event.id}/kind`, {
			method: 'PATCH',
			body: { kind }
		});
		selected = updated;
		load();
		loadExams();
	}

	async function remove(event) {
		if (!confirm(`Supprimer « ${event.title} » ?`)) return;
		await api(`/calendar/events/${event.id}`, { method: 'DELETE' });
		selected = null;
		load();
		loadExams();
	}

	async function add(e) {
		e.preventDefault();
		error = '';
		try {
			await api('/calendar/events', {
				method: 'POST',
				body: {
					title: form.title,
					kind: form.kind,
					location: form.location,
					start: new Date(`${form.day}T${form.start}`).toISOString(),
					end: new Date(`${form.day}T${form.end}`).toISOString()
				}
			});
			form.title = '';
			showForm = false;
			cursor = startOfDay(new Date(form.day));
			load();
			loadExams();
		} catch (err) {
			error = err.message;
		}
	}

	function openForm(day) {
		if (day) form.day = isoDay(day);
		showForm = true;
	}

	const today = isoDay();
	const listDays = $derived(days.filter((d) => eventsByDay[isoDay(d)] || sessionsByDay[isoDay(d)]));
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && ((selected = null), (showForm = false))} />

<header class="page-head">
	<div>
		<h1>Planning</h1>
		<p>Cours synchronisés depuis Zeus, examens et sessions de révision conseillées.</p>
	</div>
	<button onclick={() => openForm()}><Icon name="plus" /> Ajouter un examen</button>
</header>

<div class="toolbar">
	<div class="row">
		<div class="nav">
			<button class="ghost" onclick={() => shift(-1)} aria-label="Précédent"
				><Icon name="left" /></button
			>
			<button class="secondary" onclick={() => (cursor = startOfDay(new Date()))}
				>Aujourd'hui</button
			>
			<button class="ghost" onclick={() => shift(1)} aria-label="Suivant"
				><Icon name="right" /></button
			>
		</div>
		<strong class="title">{title}</strong>
	</div>
	<div class="segmented" role="tablist">
		{#each VIEWS as v (v.id)}
			<button
				role="tab"
				aria-selected={view === v.id}
				class:on={view === v.id}
				onclick={() => (view = v.id)}
			>
				<Icon name={v.icon} size={15} />
				{v.label}
			</button>
		{/each}
	</div>
</div>

<div class="layout">
	<div class="main card" class:flush={view !== 'list'}>
		{#if view === 'week'}
			<div class="week">
				<div class="corner"></div>
				{#each days as d (d.getTime())}
					<div class="day-head" class:is-today={isoDay(d) === today}>
						<span>{weekdayFmt.format(d)}</span>
						<strong>{d.getDate()}</strong>
					</div>
				{/each}

				<div class="corner allday-label small muted">Révisions</div>
				{#each days as d (d.getTime())}
					<div class="allday">
						{#each sessionsByDay[isoDay(d)] ?? [] as s (s.exam.id + '-' + s.offset)}
							<span class="chip revision" title="Réviser pour {s.exam.title}">
								J-{s.offset} · {s.exam.title}
							</span>
						{/each}
					</div>
				{/each}

				<div class="hours" style="height:{(hours.max - hours.min) * HOUR_PX}px">
					{#each Array.from({ length: hours.max - hours.min }, (_, i) => hours.min + i) as h (h)}
						<span style="top:{(h - hours.min) * HOUR_PX}px">{String(h).padStart(2, '0')}:00</span>
					{/each}
				</div>
				{#each days as d (d.getTime())}
					<div
						class="col"
						class:is-today={isoDay(d) === today}
						style="height:{(hours.max - hours.min) * HOUR_PX}px; --hour:{HOUR_PX}px"
					>
						{#each layoutDay(eventsByDay[isoDay(d)] ?? []) as item (item.event.id)}
							{@const e = item.event}
							<button
								class="event {e.kind}"
								style="{position(e)};left:calc({(item.col / item.cols) *
									100}% + 2px);width:calc({100 / item.cols}% - 4px)"
								onclick={() => (selected = e)}
							>
								<strong
									>{#if e.kind === 'exam'}<Icon name="alert" size={12} stroke={2.5} />{/if}
									{e.title}</strong
								>
								<span>{formatTime(e.start)}–{formatTime(e.end)}</span>
								{#if e.location}<span class="loc">{e.location}</span>{/if}
							</button>
						{/each}
						{#if isoDay(d) === today && nowTop >= 0 && nowTop <= (hours.max - hours.min) * HOUR_PX}
							<div class="now" style="top:{nowTop}px"></div>
						{/if}
					</div>
				{/each}
			</div>
		{:else if view === 'month'}
			<div class="month">
				{#each days.slice(0, 7) as d (d.getTime())}
					<div class="month-head">{weekdayFmt.format(d)}</div>
				{/each}
				{#each days as d (d.getTime())}
					{@const list = eventsByDay[isoDay(d)] ?? []}
					{@const sessions = sessionsByDay[isoDay(d)] ?? []}
					<div
						class="cell"
						class:out={d.getMonth() !== cursor.getMonth()}
						class:is-today={isoDay(d) === today}
					>
						<button class="ghost num" onclick={() => ((cursor = d), (view = 'week'))}
							>{d.getDate()}</button
						>
						{#each sessions as s (s.exam.id + '-' + s.offset)}
							<span class="chip revision">J-{s.offset} {s.exam.title}</span>
						{/each}
						{#each list.slice(0, 3) as e (e.id)}
							<button class="chip {e.kind}" onclick={() => (selected = e)}>
								<span class="dot"></span>{formatTime(e.start)}
								{e.title}
							</button>
						{/each}
						{#if list.length > 3}
							<button class="ghost more" onclick={() => ((cursor = d), (view = 'week'))}>
								+{list.length - 3} autres
							</button>
						{/if}
					</div>
				{/each}
			</div>
		{:else}
			{#each listDays as d (d.getTime())}
				<section class="list-day">
					<h3 class:is-today={isoDay(d) === today}>{longDayFmt.format(d)}</h3>
					{#each sessionsByDay[isoDay(d)] ?? [] as s (s.exam.id + '-' + s.offset)}
						<div class="list-item revision">
							<span class="list-time">J-{s.offset}</span>
							<span class="list-bar"></span>
							<span><strong>Réviser : {s.exam.title}</strong></span>
						</div>
					{/each}
					{#each eventsByDay[isoDay(d)] ?? [] as e (e.id)}
						<button class="list-item {e.kind}" onclick={() => (selected = e)}>
							<span class="list-time"
								>{formatTime(e.start)}<br /><small>{formatTime(e.end)}</small></span
							>
							<span class="list-bar"></span>
							<span class="list-what">
								<strong>{e.title}</strong>
								<span class="small muted">
									{KIND_LABELS[e.kind]}{e.location ? ` · ${e.location}` : ''}
								</span>
							</span>
						</button>
					{/each}
				</section>
			{:else}
				<div class="empty">
					<span class="emoji">🗓️</span>Rien de prévu sur les 30 prochains jours.
				</div>
			{/each}
		{/if}
	</div>

	<aside class="side">
		<section class="card">
			<h2><Icon name="flame" /> Prochains examens</h2>
			{#if upcomingExams.length}
				<ul class="exam-list">
					{#each upcomingExams.slice(0, 8) as e (e.id)}
						{@const n = daysUntil(e.start)}
						<li>
							<button class="exam-item {urgency(n)}" onclick={() => (selected = e)}>
								<span class="count">{n === 0 ? 'Auj.' : `J-${n}`}</span>
								<span class="exam-text">
									<strong>{e.title}</strong>
									<span class="small muted">{formatDate(e.start)} · {formatTime(e.start)}</span>
								</span>
							</button>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="small muted">
					Aucun examen prévu. Ajoute-les avec le bouton en haut, ou corrige le type d'un cours Zeus.
				</p>
			{/if}
		</section>
		<section class="card legend small">
			<span><span class="swatch course"></span> Cours</span>
			<span><span class="swatch exam"></span> Examen</span>
			<span><span class="swatch other"></span> Autre</span>
			<span><span class="swatch revision"></span> Révision conseillée</span>
			<p class="muted">
				Les cours arrivent de Zeus via le lien ICS dans <a href="/parametres">Paramètres</a>. Les
				examens sont détectés par leur titre (partiel, exam, QCM…).
			</p>
		</section>
	</aside>
</div>

{#if selected}
	<div class="overlay" role="presentation" onclick={() => (selected = null)}>
		<div
			class="modal card"
			role="dialog"
			aria-modal="true"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={() => {}}
		>
			<div class="modal-head">
				<span class="badge {selected.kind}">{KIND_LABELS[selected.kind]}</span>
				<button class="ghost" onclick={() => (selected = null)} aria-label="Fermer"
					><Icon name="x" /></button
				>
			</div>
			<h2 class="modal-title">{selected.title}</h2>
			<p class="row muted">
				<Icon name="clock" size={15} />
				{longDayFmt.format(new Date(selected.start))}, {formatTime(selected.start)}–{formatTime(
					selected.end
				)}
			</p>
			{#if selected.location}<p class="row muted">
					<Icon name="pin" size={15} />
					{selected.location}
				</p>{/if}
			{#if selected.description}<p class="desc small">{selected.description}</p>{/if}
			<label>
				Type
				<select value={selected.kind} onchange={(ev) => setKind(selected, ev.currentTarget.value)}>
					{#each Object.entries(KIND_LABELS) as [value, label] (value)}
						<option {value}>{label}</option>
					{/each}
				</select>
			</label>
			<div class="row modal-foot">
				{#if selected.source_id === null}
					<button class="danger" onclick={() => remove(selected)}
						><Icon name="trash" size={15} /> Supprimer</button
					>
				{:else}
					<span class="small muted">Synchronisé depuis un calendrier</span>
				{/if}
			</div>
		</div>
	</div>
{/if}

{#if showForm}
	<div class="overlay" role="presentation" onclick={() => (showForm = false)}>
		<form
			class="modal card stack"
			onsubmit={add}
			onclick={(e) => e.stopPropagation()}
			onkeydown={() => {}}
			role="dialog"
			aria-modal="true"
			tabindex="-1"
		>
			<div class="modal-head">
				<h2>Nouvel événement</h2>
				<button type="button" class="ghost" onclick={() => (showForm = false)} aria-label="Fermer"
					><Icon name="x" /></button
				>
			</div>
			<label>Titre <input bind:value={form.title} required placeholder="Partiel d'algo" /></label>
			<div class="form-grid">
				<label>Jour <input type="date" bind:value={form.day} required /></label>
				<label>Début <input type="time" bind:value={form.start} required /></label>
				<label>Fin <input type="time" bind:value={form.end} required /></label>
			</div>
			<div class="form-grid">
				<label>
					Type
					<select bind:value={form.kind}>
						<option value="exam">Examen</option>
						<option value="course">Cours</option>
						<option value="other">Autre</option>
					</select>
				</label>
				<label class="span2">Salle <input bind:value={form.location} placeholder="Amphi 4" /></label
				>
			</div>
			{#if error}<p class="error small">{error}</p>{/if}
			<button>Ajouter</button>
		</form>
	</div>
{/if}

<style>
	.toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
		margin-bottom: 1rem;
	}

	.nav {
		display: flex;
		align-items: center;
		gap: 0.15rem;
	}

	.title {
		font-size: 1.05rem;
		margin-left: 0.4rem;
	}

	.title::first-letter {
		text-transform: uppercase;
	}

	.segmented {
		display: inline-flex;
		background: var(--surface-2);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 3px;
	}

	.segmented button {
		background: transparent;
		color: var(--muted);
		padding: 0.35rem 0.75rem;
		border-radius: 7px;
	}

	.segmented button.on {
		background: var(--surface);
		color: var(--text);
		box-shadow: var(--shadow);
	}

	.layout {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 290px;
		gap: 1rem;
		align-items: start;
	}

	.main.flush {
		padding: 0;
		overflow: hidden;
	}

	/* ---- Semaine ---- */
	.week {
		display: grid;
		grid-template-columns: 3.4rem repeat(7, minmax(0, 1fr));
		overflow-x: auto;
	}

	.corner {
		border-bottom: 1px solid var(--border);
	}

	.day-head {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.7rem 0 0.5rem;
		border-bottom: 1px solid var(--border);
		border-left: 1px solid var(--border);
		font-size: 0.75rem;
		color: var(--muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.day-head strong {
		font-size: 1.25rem;
		color: var(--text);
		letter-spacing: 0;
		width: 2.1rem;
		height: 2.1rem;
		display: grid;
		place-items: center;
		border-radius: 50%;
	}

	.day-head.is-today {
		color: var(--accent);
	}

	.day-head.is-today strong {
		background: var(--accent);
		color: white;
	}

	.allday-label {
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.65rem;
		writing-mode: horizontal-tb;
	}

	.allday {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: 4px;
		min-height: 2rem;
		border-left: 1px solid var(--border);
		border-bottom: 1px solid var(--border);
	}

	.hours {
		position: relative;
	}

	.hours span {
		position: absolute;
		right: 0.45rem;
		transform: translateY(-50%);
		font-size: 0.7rem;
		color: var(--muted);
		font-variant-numeric: tabular-nums;
	}

	.hours span:first-child {
		transform: none;
	}

	.col {
		position: relative;
		border-left: 1px solid var(--border);
		background-image: repeating-linear-gradient(
			to bottom,
			var(--border) 0,
			var(--border) 1px,
			transparent 1px,
			transparent var(--hour)
		);
	}

	.col.is-today {
		background-color: color-mix(in srgb, var(--accent) 4%, transparent);
	}

	.event {
		position: absolute;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		justify-content: flex-start;
		gap: 0;
		overflow: hidden;
		text-align: left;
		padding: 0.3rem 0.45rem;
		border-radius: 8px;
		font-size: 0.74rem;
		font-weight: 500;
		line-height: 1.25;
		background: var(--course-soft);
		color: var(--course);
		border-left: 3px solid var(--course);
		box-shadow: none;
	}

	.event strong {
		font-weight: 650;
		color: var(--text);
		display: flex;
		align-items: center;
		gap: 0.2rem;
	}

	.event.exam {
		background: var(--exam);
		border-left-color: color-mix(in srgb, var(--exam) 70%, black);
		color: rgb(255 255 255 / 0.9);
	}

	.event.exam strong {
		color: white;
	}

	.event.other {
		background: var(--other-soft);
		border-left-color: var(--other);
		color: var(--other);
	}

	.event .loc {
		opacity: 0.8;
	}

	.now {
		position: absolute;
		left: 0;
		right: 0;
		height: 2px;
		background: var(--danger);
		z-index: 2;
	}

	.now::before {
		content: '';
		position: absolute;
		left: -5px;
		top: -4px;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--danger);
	}

	/* ---- Puces (mois + révisions) ---- */
	.chip {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		width: 100%;
		font-size: 0.7rem;
		font-weight: 600;
		padding: 0.12rem 0.4rem;
		border-radius: 6px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		background: var(--course-soft);
		color: var(--course);
		justify-content: flex-start;
		line-height: 1.4;
	}

	.chip.revision {
		display: block;
		background: var(--revision-soft);
		color: var(--revision);
		border: 1px dashed color-mix(in srgb, var(--revision) 50%, transparent);
	}

	.chip.exam {
		background: var(--exam);
		color: white;
	}

	.chip.other {
		background: var(--other-soft);
		color: var(--other);
	}

	.chip .dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: currentColor;
		flex-shrink: 0;
	}

	/* ---- Mois ---- */
	.month {
		display: grid;
		grid-template-columns: repeat(7, minmax(0, 1fr));
	}

	.month-head {
		padding: 0.6rem;
		font-size: 0.72rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--muted);
		border-bottom: 1px solid var(--border);
		text-align: center;
	}

	.cell {
		min-height: 7rem;
		padding: 0.3rem;
		display: flex;
		flex-direction: column;
		gap: 3px;
		border-right: 1px solid var(--border);
		border-bottom: 1px solid var(--border);
		min-width: 0;
	}

	.cell:nth-child(7n) {
		border-right: 0;
	}

	.cell.out {
		background: var(--surface-2);
	}

	.cell.out .num {
		color: var(--muted);
		opacity: 0.6;
	}

	.num {
		align-self: flex-start;
		font-weight: 650;
		color: var(--text);
		padding: 0.1rem 0.45rem;
		border-radius: 999px;
		font-size: 0.8rem;
	}

	.cell.is-today .num {
		background: var(--accent);
		color: white;
	}

	.more {
		font-size: 0.7rem;
		padding: 0 0.3rem;
		align-self: flex-start;
	}

	/* ---- Liste ---- */
	.list-day + .list-day {
		margin-top: 1.1rem;
	}

	.list-day h3 {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--muted);
		margin: 0 0 0.5rem;
	}

	.list-day h3::first-letter {
		text-transform: uppercase;
	}

	.list-day h3.is-today {
		color: var(--accent);
	}

	.list-item {
		display: grid;
		grid-template-columns: 3.2rem 4px 1fr;
		gap: 0.75rem;
		width: 100%;
		text-align: left;
		align-items: stretch;
		padding: 0.5rem;
		border-radius: var(--radius-sm);
		background: transparent;
		color: var(--text);
		font-weight: 400;
	}

	button.list-item:hover {
		background: var(--surface-2);
		filter: none;
	}

	.list-time {
		font-weight: 650;
		font-variant-numeric: tabular-nums;
		line-height: 1.3;
	}

	.list-time small {
		color: var(--muted);
		font-weight: 500;
	}

	.list-bar {
		border-radius: 4px;
		background: var(--course);
	}

	.list-item.exam .list-bar {
		background: var(--exam);
	}

	.list-item.other .list-bar {
		background: var(--other);
	}

	.list-item.revision .list-bar {
		background: var(--revision);
	}

	.list-item.revision {
		color: var(--revision);
	}

	.list-what {
		display: flex;
		flex-direction: column;
	}

	/* ---- Colonne de droite ---- */
	.side {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		position: sticky;
		top: 1rem;
	}

	.exam-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.exam-item {
		display: flex;
		align-items: center;
		gap: 0.7rem;
		width: 100%;
		text-align: left;
		background: var(--surface-2);
		color: var(--text);
		padding: 0.5rem;
		font-weight: 400;
	}

	.exam-item:hover {
		filter: none;
		background: var(--surface-3);
	}

	.count {
		min-width: 3rem;
		text-align: center;
		padding: 0.35rem 0;
		border-radius: 8px;
		font-weight: 800;
		font-size: 0.85rem;
		background: var(--accent-soft);
		color: var(--accent);
	}

	.medium .count {
		background: var(--revision-soft);
		color: var(--revision);
	}

	.high .count {
		background: var(--exam);
		color: white;
	}

	.exam-text {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.exam-text strong {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1rem;
	}

	.legend span {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
	}

	.legend p {
		margin: 0.25rem 0 0;
	}

	.swatch {
		width: 10px;
		height: 10px;
		border-radius: 3px;
		background: var(--course);
	}

	.swatch.exam {
		background: var(--exam);
	}

	.swatch.other {
		background: var(--other);
	}

	.swatch.revision {
		background: var(--revision);
	}

	/* ---- Fenêtres ---- */
	.overlay {
		position: fixed;
		inset: 0;
		background: rgb(10 12 25 / 0.45);
		backdrop-filter: blur(3px);
		display: grid;
		place-items: center;
		padding: 1rem;
		z-index: 50;
	}

	.modal {
		width: min(440px, 100%);
		box-shadow: var(--shadow-lg);
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.modal p {
		margin: 0;
		gap: 0.4rem;
	}

	.modal-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.modal-head h2 {
		margin: 0;
	}

	.modal-title {
		font-size: 1.25rem;
		margin: 0;
	}

	.modal-foot {
		justify-content: flex-end;
	}

	.desc {
		white-space: pre-line;
		max-height: 8rem;
		overflow: auto;
		color: var(--muted);
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.6rem;
	}

	.span2 {
		grid-column: span 2;
	}

	@media (max-width: 1100px) {
		.layout {
			grid-template-columns: 1fr;
		}

		.side {
			position: static;
		}
	}

	@media (max-width: 760px) {
		.week {
			grid-template-columns: 2.8rem repeat(7, minmax(90px, 1fr));
		}

		.cell {
			min-height: 4.5rem;
		}

		.cell .chip {
			font-size: 0;
			padding: 0;
			height: 6px;
		}
	}
</style>
