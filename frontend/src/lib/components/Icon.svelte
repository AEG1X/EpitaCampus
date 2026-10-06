<script>
	/** Icônes au trait (style Lucide). Un « c:x,y,r » dessine un cercle. */
	const ICONS = {
		home: ['M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z'],
		book: [
			'M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z',
			'M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5'
		],
		calendar: [
			'M8 2v4',
			'M16 2v4',
			'M3 10h18',
			'M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z'
		],
		chart: ['M3 3v18h18', 'M7 16v-5', 'M12 16V8', 'M17 16V7'],
		tool: [
			'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94z'
		],
		settings: [
			'M4 21v-7',
			'M4 10V3',
			'M12 21v-9',
			'M12 8V3',
			'M20 21v-5',
			'M20 12V3',
			'M1 14h6',
			'M9 8h6',
			'M17 16h6'
		],
		logout: ['M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4', 'M16 17l5-5-5-5', 'M21 12H9'],
		clock: ['c:12,12,10', 'M12 6v6l4 2'],
		alert: [
			'M12 9v4',
			'M12 17h.01',
			'M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z'
		],
		check: ['M20 6 9 17l-5-5'],
		plus: ['M12 5v14', 'M5 12h14'],
		left: ['m15 18-6-6 6-6'],
		right: ['m9 18 6-6-6-6'],
		pin: ['M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z', 'c:12,10,3'],
		file: ['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z', 'M14 2v6h6'],
		upload: ['M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4', 'M17 8l-5-5-5 5', 'M12 3v12'],
		menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
		flame: [
			'M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3 0 1.38 1.12 2.5 2.5 2.5z'
		],
		cap: ['M22 10 12 5 2 10l10 5 10-5z', 'M6 12v5c3 3 9 3 12 0v-5'],
		trash: ['M3 6h18', 'M8 6V4h8v2', 'M19 6l-1 14H6L5 6'],
		search: ['c:11,11,8', 'm21 21-4.3-4.3'],
		lock: ['M5 11h14v10H5z', 'M8 11V7a4 4 0 0 1 8 0v4'],
		key: ['c:7.5,15.5,5.5', 'M11.5 11.5 21 2', 'M16 7l3 3', 'M19 4l2 2'],
		list: ['M8 6h13', 'M8 12h13', 'M8 18h13', 'M3 6h.01', 'M3 12h.01', 'M3 18h.01'],
		grid: ['M3 3h18v18H3z', 'M3 9h18', 'M3 15h18', 'M9 3v18', 'M15 3v18'],
		columns: ['M3 3h18v18H3z', 'M9 3v18', 'M15 3v18'],
		x: ['M18 6 6 18', 'M6 6l12 12']
	};

	let { name, size = 18, stroke = 2 } = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	stroke="currentColor"
	stroke-width={stroke}
	stroke-linecap="round"
	stroke-linejoin="round"
	aria-hidden="true"
>
	{#each ICONS[name] ?? [] as d, i (i)}
		{#if d.startsWith('c:')}
			{@const [cx, cy, r] = d.slice(2).split(',')}
			<circle {cx} {cy} {r} />
		{:else}
			<path {d} />
		{/if}
	{/each}
</svg>

<style>
	svg {
		flex-shrink: 0;
		vertical-align: -0.2em;
	}
</style>
