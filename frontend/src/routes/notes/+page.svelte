<script>
	import { api } from '#lib/api.js';
	import { formatDate, isoDay } from '#lib/format.js';
	import BarChart from '#lib/components/BarChart.svelte';
	import LineChart from '#lib/components/LineChart.svelte';

	let grades = $state([]);
	let error = $state('');
	let form = $state({
		subject: '',
		label: '',
		value: '',
		max_value: 20,
		coefficient: 1,
		date: isoDay()
	});

	const on20 = (g) => (g.value / g.max_value) * 20;

	function weightedAverage(list) {
		const coef = list.reduce((s, g) => s + g.coefficient, 0);
		return coef ? list.reduce((s, g) => s + on20(g) * g.coefficient, 0) / coef : null;
	}

	const subjects = $derived([...new Set(grades.map((g) => g.subject))].sort());
	const average = $derived(weightedAverage(grades));
	const bySubject = $derived(
		subjects.map((s) => ({
			label: s,
			value: weightedAverage(grades.filter((g) => g.subject === s))
		}))
	);
	// Moyenne générale recalculée après chaque note, dans l'ordre chronologique.
	const evolution = $derived(
		grades.map((g, i) => ({
			date: new Date(g.date),
			label: g.label,
			value: weightedAverage(grades.slice(0, i + 1))
		}))
	);

	async function load() {
		grades = await api('/grades');
	}

	$effect(() => {
		load();
	});

	async function add(e) {
		e.preventDefault();
		error = '';
		try {
			await api('/grades', {
				method: 'POST',
				body: {
					...form,
					value: Number(form.value),
					max_value: Number(form.max_value),
					coefficient: Number(form.coefficient)
				}
			});
			form.label = '';
			form.value = '';
			load();
		} catch (err) {
			error = err.message;
		}
	}

	async function remove(g) {
		if (!confirm(`Supprimer la note « ${g.label} » ?`)) return;
		await api(`/grades/${g.id}`, { method: 'DELETE' });
		load();
	}
</script>

<header class="page-head">
	<div>
		<h1>Notes</h1>
		<p>Tes résultats, ta moyenne pondérée et son évolution.</p>
	</div>
</header>

<form class="card add" onsubmit={add}>
	<label>
		Matière
		<input bind:value={form.subject} list="grade-subjects" required placeholder="Algo" />
	</label>
	<datalist id="grade-subjects">
		{#each subjects as s (s)}<option value={s}></option>{/each}
	</datalist>
	<label class="label-field">
		Intitulé
		<input bind:value={form.label} required placeholder="Partiel 1" />
	</label>
	<label>Note <input type="number" step="0.01" min="0" bind:value={form.value} required /></label>
	<label
		>Sur <input type="number" step="0.01" min="0.01" bind:value={form.max_value} required /></label
	>
	<label
		>Coef. <input
			type="number"
			step="0.1"
			min="0.1"
			bind:value={form.coefficient}
			required
		/></label
	>
	<label>Date <input type="date" bind:value={form.date} required /></label>
	<button>Ajouter</button>
</form>
{#if error}<p class="error">{error}</p>{/if}

{#if grades.length}
	<div class="grid charts">
		<section class="card">
			<h2>Moyenne générale</h2>
			<p class="big">{average.toFixed(2)}<span class="muted">/20</span></p>
			<p class="small muted">Pondérée par les coefficients, {grades.length} note(s)</p>
		</section>
		<section class="card wide">
			<h2>Moyenne par matière</h2>
			<BarChart items={bySubject} />
		</section>
		<section class="card wide">
			<h2>Évolution de la moyenne générale</h2>
			<LineChart points={evolution} />
		</section>
	</div>

	<section class="card">
		<h2>Toutes les notes</h2>
		<div class="table-wrap">
			<table>
				<thead>
					<tr
						><th>Date</th><th>Matière</th><th>Intitulé</th><th>Note</th><th>/20</th><th>Coef.</th
						><th></th></tr
					>
				</thead>
				<tbody>
					{#each [...grades].reverse() as g (g.id)}
						<tr>
							<td>{formatDate(g.date)}</td>
							<td>{g.subject}</td>
							<td>{g.label}</td>
							<td>{g.value}/{g.max_value}</td>
							<td>{on20(g).toFixed(2)}</td>
							<td>{g.coefficient}</td>
							<td><button class="danger" onclick={() => remove(g)}>Supprimer</button></td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>
{:else}
	<p class="muted">
		Ajoute tes notes ci-dessus pour voir tes moyennes et leur évolution. L'import automatique depuis
		Auriga viendra plus tard.
	</p>
{/if}

<style>
	.add {
		display: grid;
		gap: 0.75rem;
		grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
		align-items: end;
	}
	.label-field {
		grid-column: span 2;
	}
	.charts {
		margin: 1rem 0;
		grid-template-columns: minmax(220px, 1fr) 2fr;
	}
	.wide {
		grid-column: 1 / -1;
	}
	.charts > :nth-child(2) {
		grid-column: auto;
	}
	@media (max-width: 800px) {
		.charts {
			grid-template-columns: 1fr;
		}
	}
	.big {
		font-size: 2.4rem;
		font-weight: 700;
		margin: 0;
	}
</style>
