import { isoDay } from './format.js';

/** Jours avant un examen où une session de révision est conseillée. */
export const REVISION_OFFSETS = [7, 3, 1];

/** Sessions de révision « virtuelles » (une par examen et par jour J-7, J-3, J-1). */
export function revisionSessions(exams) {
	const sessions = [];
	for (const exam of exams) {
		const examDay = new Date(exam.start);
		examDay.setHours(0, 0, 0, 0);
		for (const offset of REVISION_OFFSETS) {
			const day = new Date(examDay);
			day.setDate(day.getDate() - offset);
			sessions.push({ day: isoDay(day), offset, exam });
		}
	}
	return sessions;
}

/** Nombre de jours calendaires entre aujourd'hui et une date. */
export function daysUntil(date) {
	const a = new Date();
	a.setHours(0, 0, 0, 0);
	const b = new Date(date);
	b.setHours(0, 0, 0, 0);
	return Math.round((b - a) / 86400000);
}

/** Niveau d'urgence d'un examen, pour la couleur. */
export function urgency(days) {
	if (days <= 2) return 'high';
	if (days <= 7) return 'medium';
	return 'low';
}
