<script>
	/** Barres horizontales : une barre par matière, échelle 0–20 avec repère à 10. */
	let { items } = $props(); // [{ label, value }]
	let hovered = $state(null);

	const rowH = 30;
	const labelW = 120;
	const width = 520;
	const plotW = width - labelW - 50;
	const height = $derived(items.length * rowH + 24);
	const x = (v) => labelW + (v / 20) * plotW;
</script>

<svg viewBox="0 0 {width} {height}" role="img" aria-label="Moyenne par matière">
	{#each [0, 5, 10, 15, 20] as tick (tick)}
		<line class="grid" class:mid={tick === 10} x1={x(tick)} x2={x(tick)} y1="0" y2={height - 18} />
		<text class="tick" x={x(tick)} y={height - 4} text-anchor="middle">{tick}</text>
	{/each}
	{#each items as item, i (item.label)}
		{@const y = i * rowH + 8}
		<g
			role="presentation"
			onmouseenter={() => (hovered = i)}
			onmouseleave={() => (hovered = null)}
			opacity={hovered === null || hovered === i ? 1 : 0.45}
		>
			<rect x="0" {y} {width} height={rowH - 4} fill="transparent" />
			<text class="label" x={labelW - 8} y={y + 15} text-anchor="end">{item.label}</text>
			<rect
				class="bar"
				x={labelW}
				y={y + 4}
				width={Math.max(x(item.value) - labelW, 2)}
				height="14"
				rx="4"
			/>
			<text class="value" x={x(item.value) + 6} y={y + 15}>{item.value.toFixed(2)}</text>
		</g>
	{/each}
</svg>

<style>
	svg {
		width: 100%;
		height: auto;
		font-size: 12px;
	}
	.grid {
		stroke: var(--border);
		stroke-width: 1;
	}
	.grid.mid {
		stroke: var(--muted);
		stroke-dasharray: 3 3;
	}
	.tick,
	.label {
		fill: var(--muted);
	}
	.value {
		fill: var(--text);
		font-weight: 600;
	}
	.bar {
		fill: var(--accent);
	}
</style>
