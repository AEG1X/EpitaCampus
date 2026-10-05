<script>
	const PHASES = {
		work: { label: 'Travail', minutes: 25 },
		short: { label: 'Pause courte', minutes: 5 },
		long: { label: 'Pause longue', minutes: 15 }
	};

	let phase = $state('work');
	let remaining = $state(PHASES.work.minutes * 60);
	let running = $state(false);
	let done = $state(0);

	const display = $derived(
		`${String(Math.floor(remaining / 60)).padStart(2, '0')}:${String(remaining % 60).padStart(2, '0')}`
	);

	function setPhase(name) {
		phase = name;
		remaining = PHASES[name].minutes * 60;
	}

	function next() {
		if (phase === 'work') {
			done += 1;
			setPhase(done % 4 === 0 ? 'long' : 'short');
		} else {
			setPhase('work');
		}
		if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
			new Notification(`EpitaCampus : ${PHASES[phase].label}`);
		}
	}

	$effect(() => {
		if (!running) return;
		const end = Date.now() + remaining * 1000;
		const timer = setInterval(() => {
			remaining = Math.max(0, Math.round((end - Date.now()) / 1000));
			if (remaining === 0) {
				running = false;
				next();
			}
		}, 250);
		return () => clearInterval(timer);
	});

	$effect(() => {
		document.title = running ? `${display} · ${PHASES[phase].label}` : 'EpitaCampus';
		return () => (document.title = 'EpitaCampus');
	});

	function start() {
		if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
			Notification.requestPermission();
		}
		running = true;
	}
</script>

<h1>Minuteur Pomodoro</h1>

<section class="card timer stack">
	<div class="row center">
		{#each Object.entries(PHASES) as [name, p] (name)}
			<button class:secondary={phase !== name} onclick={() => ((running = false), setPhase(name))}
				>{p.label}</button
			>
		{/each}
	</div>
	<div class="time">{display}</div>
	<div class="row center">
		{#if running}
			<button onclick={() => (running = false)}>Pause</button>
		{:else}
			<button onclick={start}>Démarrer</button>
		{/if}
		<button class="secondary" onclick={() => ((running = false), setPhase(phase))}
			>Réinitialiser</button
		>
	</div>
	<p class="muted small">Sessions de travail terminées : {done}</p>
</section>

<style>
	.timer {
		max-width: 480px;
		text-align: center;
		align-items: center;
	}
	.center {
		justify-content: center;
	}
	.time {
		font-size: 4.5rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
</style>
