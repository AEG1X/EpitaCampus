<script>
	/** Courbe de l'évolution d'une valeur sur /20 dans le temps, avec info-bulle au survol. */
	let { points } = $props(); // [{ date: Date, value, label }]
	let hovered = $state(null);

	const width = 560;
	const height = 220;
	const pad = { l: 32, r: 16, t: 12, b: 26 };
	const fmt = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short' });

	const t0 = $derived(points.length ? points[0].date.getTime() : 0);
	const t1 = $derived(points.length ? points[points.length - 1].date.getTime() : 1);
	const x = (d) =>
		pad.l + (t1 === t0 ? 0.5 : (d.getTime() - t0) / (t1 - t0)) * (width - pad.l - pad.r);
	const y = (v) => pad.t + (1 - v / 20) * (height - pad.t - pad.b);
	const path = $derived(
		points.map((p, i) => `${i ? 'L' : 'M'}${x(p.date)},${y(p.value)}`).join('')
	);

	function onMove(event) {
		const svg = event.currentTarget;
		const box = svg.getBoundingClientRect();
		const mx = ((event.clientX - box.left) / box.width) * width;
		let best = 0;
		points.forEach((p, i) => {
			if (Math.abs(x(p.date) - mx) < Math.abs(x(points[best].date) - mx)) best = i;
		});
		hovered = best;
	}
</script>

<svg
	viewBox="0 0 {width} {height}"
	role="img"
	aria-label="Évolution de la moyenne"
	onmousemove={onMove}
	onmouseleave={() => (hovered = null)}
>
	{#each [0, 5, 10, 15, 20] as tick (tick)}
		<line
			class="grid"
			class:mid={tick === 10}
			x1={pad.l}
			x2={width - pad.r}
			y1={y(tick)}
			y2={y(tick)}
		/>
		<text class="tick" x={pad.l - 6} y={y(tick) + 4} text-anchor="end">{tick}</text>
	{/each}
	{#if points.length}
		<text class="tick" x={pad.l} y={height - 6}>{fmt.format(points[0].date)}</text>
		<text class="tick" x={width - pad.r} y={height - 6} text-anchor="end">
			{fmt.format(points[points.length - 1].date)}
		</text>
	{/if}
	<path d={path} class="line" />
	{#if hovered !== null}
		{@const p = points[hovered]}
		{@const px = x(p.date)}
		<line class="cross" x1={px} x2={px} y1={pad.t} y2={height - pad.b} />
		<circle cx={px} cy={y(p.value)} r="5" class="dot" />
		<g transform="translate({Math.min(px + 8, width - 170)}, {pad.t + 4})">
			<rect width="160" height="40" rx="6" class="tip" />
			<text x="8" y="16" class="tip-text">{fmt.format(p.date)} · {p.label}</text>
			<text x="8" y="32" class="tip-value">Moyenne : {p.value.toFixed(2)}/20</text>
		</g>
	{/if}
</svg>

<style>
	svg {
		width: 100%;
		height: auto;
		font-size: 12px;
	}
	.grid {
		stroke: var(--border);
	}
	.grid.mid {
		stroke: var(--muted);
		stroke-dasharray: 3 3;
	}
	.tick {
		fill: var(--muted);
	}
	.line {
		fill: none;
		stroke: var(--accent);
		stroke-width: 2;
		stroke-linejoin: round;
	}
	.cross {
		stroke: var(--muted);
		stroke-width: 1;
	}
	.dot {
		fill: var(--accent);
		stroke: var(--surface);
		stroke-width: 2;
	}
	.tip {
		fill: var(--surface);
		stroke: var(--border);
	}
	.tip-text {
		fill: var(--muted);
		font-size: 11px;
	}
	.tip-value {
		fill: var(--text);
		font-weight: 600;
	}
</style>
