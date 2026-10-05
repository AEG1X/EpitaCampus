<script>
	import { api } from '#lib/api.js';
	import { formatTime, isoDay } from '#lib/format.js';

	const KIND_LABELS = { course: 'cours', exam: 'examen', other: 'autre' };
	const dayFmt = new Intl.DateTimeFormat('fr-FR', {
		weekday: 'long',
		day: 'numeric',
		month: 'long'
	});

	function mondayOf(date) {
		const d = new Date(date);
		d.setHours(0, 0, 0, 0);
		d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
		return d;
	}

	let weekStart = $state(mondayOf(new Date()));
	let events = $state([]);
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

	const days = $derived(
		Array.from({ length: 7 }, (_, i) => {
			const d = new Date(weekStart);
			d.setDate(d.getDate() + i);
			return d;
		})
	);

	const byDay = $derived(
		days.map((d) => ({
			date: d,
			events: events.filter((e) => isoDay(new Date(e.start)) === isoDay(d))
		}))
	);

	async function load() {
		const end = new Date(weekStart);
		end.setDate(end.getDate() + 7);
		const params = new URLSearchParams({ start: weekStart.toISOString(), end: end.toISOString() });
		events = await api(`/calendar/events?${params}`);
	}

	$effect(() => {
		weekStart;
		load();
	});

	function shift(weeks) {
		const d = new Date(weekStart);
		d.setDate(d.getDate() + weeks * 7);
		weekStart = d;
	}

	async function setKind(event, kind) {
		await api(`/calendar/events/${event.id}/kind`, { method: 'PATCH', body: { kind } });
		load();
	}

	async function remove(event) {
		if (!confirm(`Supprimer « ${event.title} » ?`)) return;
		await api(`/calendar/events/${event.id}`, { method: 'DELETE' });
		load();
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
			weekStart = mondayOf(new Date(form.day));
			load();
		} catch (err) {
			error = err.message;
		}
	}

	const today = isoDay();
</script>

<h1>Calendrier</h1>

<div class="row toolbar">
	<button class="secondary" onclick={() => shift(-1)}>←</button>
	<button class="secondary" onclick={() => (weekStart = mondayOf(new Date()))}>Cette semaine</button
	>
	<button class="secondary" onclick={() => shift(1)}>→</button>
	<strong>Semaine du {dayFmt.format(weekStart)}</strong>
	<span class="grow"></span>
	<button onclick={() => (showForm = !showForm)}>+ Ajouter un événement</button>
</div>

{#if showForm}
	<form class="card row form" onsubmit={add}>
		<input
			placeholder="Titre (ex : Partiel d'algo)"
			bind:value={form.title}
			required
			class="grow"
		/>
		<input type="date" bind:value={form.day} required />
		<input type="time" bind:value={form.start} required />
		<input type="time" bind:value={form.end} required />
		<select bind:value={form.kind}>
			<option value="exam">Examen</option>
			<option value="course">Cours</option>
			<option value="other">Autre</option>
		</select>
		<input placeholder="Salle" bind:value={form.location} />
		<button>Ajouter</button>
		{#if error}<p class="error small">{error}</p>{/if}
	</form>
{/if}

<p class="small muted">
	Les cours de Zeus arrivent automatiquement une fois le lien ICS ajouté dans
	<a href="/parametres">Paramètres</a>. Les examens sont détectés par leur titre ; tu peux corriger
	le type d'un événement avec le menu.
</p>

<div class="week">
	{#each byDay as day (day.date.getTime())}
		<section class="day card" class:today={isoDay(day.date) === today}>
			<h2>{dayFmt.format(day.date)}</h2>
			{#each day.events as e (e.id)}
				<div class="event {e.kind}">
					<div class="small">{formatTime(e.start)}–{formatTime(e.end)}</div>
					<strong>{e.title}</strong>
					{#if e.location}<div class="small muted">{e.location}</div>{/if}
					<div class="row small">
						<select value={e.kind} onchange={(ev) => setKind(e, ev.currentTarget.value)}>
							{#each Object.entries(KIND_LABELS) as [value, label] (value)}
								<option {value}>{label}</option>
							{/each}
						</select>
						{#if e.source_id === null}
							<button class="danger" onclick={() => remove(e)}>Supprimer</button>
						{/if}
					</div>
				</div>
			{:else}
				<p class="small muted">—</p>
			{/each}
		</section>
	{/each}
</div>

<style>
	.toolbar {
		margin-bottom: 1rem;
	}

	.grow {
		flex: 1;
	}

	.form {
		margin-bottom: 1rem;
	}

	.week {
		display: grid;
		gap: 0.75rem;
		grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
	}

	@media (min-width: 1200px) {
		.week {
			grid-template-columns: repeat(7, 1fr);
		}
	}

	.day {
		padding: 0.75rem;
	}

	.day h2 {
		font-size: 0.9rem;
		text-transform: capitalize;
	}

	.day.today {
		border-color: var(--accent);
	}

	.event {
		border-left: 3px solid var(--course);
		background: var(--surface-2);
		border-radius: 6px;
		padding: 0.4rem 0.5rem;
		margin-bottom: 0.5rem;
	}

	.event.exam {
		border-left-color: var(--exam);
	}

	.event.other {
		border-left-color: var(--other);
	}

	.event select {
		padding: 0.1rem 0.3rem;
		font-size: 0.8rem;
	}
</style>
