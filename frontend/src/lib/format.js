const dateFmt = new Intl.DateTimeFormat('fr-FR', {
	weekday: 'short',
	day: 'numeric',
	month: 'short'
});
const timeFmt = new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' });

export const formatDate = (d) => dateFmt.format(new Date(d));
export const formatTime = (d) => timeFmt.format(new Date(d));
export const formatSize = (bytes) =>
	bytes < 1024 * 1024 ? `${Math.round(bytes / 1024)} Ko` : `${(bytes / 1024 / 1024).toFixed(1)} Mo`;

/** Date du jour au format AAAA-MM-JJ (heure locale). */
export function isoDay(d = new Date()) {
	const pad = (n) => String(n).padStart(2, '0');
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function daysLabel(n) {
	if (n === 0) return "aujourd'hui";
	if (n === 1) return 'demain';
	return `dans ${n} jours`;
}
