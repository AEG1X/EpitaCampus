/** Petit client pour l'API FastAPI. Lève une erreur avec le message renvoyé par le serveur. */
export async function api(path, { method = 'GET', body, form } = {}) {
	const options = { method, credentials: 'same-origin', headers: {} };
	if (form) {
		options.body = form;
	} else if (body !== undefined) {
		options.headers['Content-Type'] = 'application/json';
		options.body = JSON.stringify(body);
	}
	const res = await fetch(`/api${path}`, options);
	const data = res.headers.get('content-type')?.includes('json') ? await res.json() : null;
	if (!res.ok) {
		const detail = data?.detail;
		const message = Array.isArray(detail)
			? detail.map((d) => d.msg).join(', ')
			: detail || `Erreur ${res.status}`;
		const error = new Error(message);
		error.status = res.status;
		throw error;
	}
	return data;
}
