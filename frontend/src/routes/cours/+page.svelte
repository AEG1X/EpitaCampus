<script>
	import { api } from '#lib/api.js';
	import { formatDate, formatSize, isoDay } from '#lib/format.js';

	let courses = $state([]);
	let filter = $state('');
	let subject = $state('');
	let title = $state('');
	let error = $state('');
	let openId = $state(null);
	let uploading = $state(false);

	const subjects = $derived([...new Set(courses.map((c) => c.subject))].sort());
	const shown = $derived(
		courses.filter(
			(c) =>
				!filter || `${c.subject} ${c.title} ${c.notes}`.toLowerCase().includes(filter.toLowerCase())
		)
	);

	async function load() {
		courses = await api('/courses');
	}

	$effect(() => {
		load();
	});

	async function create(event) {
		event.preventDefault();
		error = '';
		try {
			const course = await api('/courses', { method: 'POST', body: { subject, title } });
			title = '';
			await load();
			openId = course.id;
		} catch (e) {
			error = e.message;
		}
	}

	async function save(course) {
		await api(`/courses/${course.id}`, {
			method: 'PUT',
			body: { subject: course.subject, title: course.title, notes: course.notes }
		});
	}

	async function remove(course) {
		if (!confirm(`Supprimer « ${course.title} » et ses fichiers ?`)) return;
		await api(`/courses/${course.id}`, { method: 'DELETE' });
		load();
	}

	async function reviewed(course) {
		await api(`/courses/${course.id}/review`, { method: 'POST' });
		load();
	}

	async function upload(course, files) {
		uploading = true;
		error = '';
		try {
			for (const file of files) {
				const form = new FormData();
				form.append('file', file);
				await api(`/courses/${course.id}/files`, { method: 'POST', form });
			}
			await load();
		} catch (e) {
			error = e.message;
		} finally {
			uploading = false;
		}
	}

	async function removeFile(file) {
		if (!confirm(`Supprimer ${file.filename} ?`)) return;
		await api(`/courses/files/${file.id}`, { method: 'DELETE' });
		load();
	}

	const today = isoDay();
</script>

<h1>Cours</h1>

<form class="card row" onsubmit={create}>
	<input placeholder="Matière (ex : Algo)" bind:value={subject} list="subjects" required />
	<datalist id="subjects">
		{#each subjects as s (s)}<option value={s}></option>{/each}
	</datalist>
	<input placeholder="Titre du cours" bind:value={title} required class="grow" />
	<button>Ajouter</button>
</form>
{#if error}<p class="error">{error}</p>{/if}

<div class="row toolbar">
	<input type="search" placeholder="Rechercher…" bind:value={filter} class="grow" />
</div>

{#if !courses.length}
	<p class="muted">Aucun cours pour l'instant. Ajoute ta première matière ci-dessus.</p>
{/if}

<div class="stack">
	{#each shown as course (course.id)}
		<article class="card">
			<button
				class="head"
				onclick={() => (openId = openId === course.id ? null : course.id)}
				aria-expanded={openId === course.id}
			>
				<span class="badge">{course.subject}</span>
				<strong>{course.title}</strong>
				<span class="small muted">{course.files.length} fichier(s)</span>
				{#if course.next_review && course.next_review <= today}
					<span class="badge exam">à réviser</span>
				{/if}
			</button>

			{#if openId === course.id}
				<div class="stack body">
					<div class="row">
						<input bind:value={course.subject} onchange={() => save(course)} />
						<input bind:value={course.title} onchange={() => save(course)} class="grow" />
					</div>
					<label>
						Notes / résumé
						<textarea rows="6" bind:value={course.notes} onchange={() => save(course)}></textarea>
					</label>

					<div>
						<h2>Fichiers</h2>
						<ul class="list">
							{#each course.files as file (file.id)}
								<li class="row">
									<a href="/api/courses/files/{file.id}" target="_blank" rel="noopener">
										{file.filename}
									</a>
									<span class="small muted">{formatSize(file.size)}</span>
									<button class="danger" onclick={() => removeFile(file)}>Supprimer</button>
								</li>
							{/each}
						</ul>
						<label class="upload">
							{uploading ? 'Envoi en cours…' : '+ Ajouter des fichiers (PDF, images…)'}
							<input
								type="file"
								multiple
								disabled={uploading}
								onchange={(e) => upload(course, e.currentTarget.files)}
							/>
						</label>
					</div>

					<div class="row spread">
						<span class="small muted">
							Révisé {course.review_count} fois
							{#if course.next_review}· prochaine révision : {formatDate(course.next_review)}{/if}
						</span>
						<span class="row">
							<button class="secondary" onclick={() => reviewed(course)}>J'ai révisé ✓</button>
							<button class="danger" onclick={() => remove(course)}>Supprimer le cours</button>
						</span>
					</div>
				</div>
			{/if}
		</article>
	{/each}
</div>

<style>
	.grow {
		flex: 1;
	}

	.toolbar {
		margin: 1rem 0;
	}

	.head {
		all: unset;
		display: flex;
		gap: 0.6rem;
		align-items: center;
		flex-wrap: wrap;
		cursor: pointer;
		width: 100%;
	}

	.body {
		margin-top: 1rem;
	}

	.spread {
		justify-content: space-between;
	}

	.upload {
		margin-top: 0.5rem;
		border: 1px dashed var(--border);
		border-radius: 8px;
		padding: 0.75rem;
		text-align: center;
		cursor: pointer;
	}

	.upload input {
		display: none;
	}
</style>
