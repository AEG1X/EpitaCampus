import jsQR from 'jsqr';

/** Lit le texte d'un QR code dans une image (fichier ou capture collée). */
export async function readQr(blob) {
	const bitmap = await createImageBitmap(blob);
	const canvas = document.createElement('canvas');
	canvas.width = bitmap.width;
	canvas.height = bitmap.height;
	const ctx = canvas.getContext('2d');
	// Fond blanc : les captures du thème sombre ont parfois de la transparence.
	ctx.fillStyle = '#fff';
	ctx.fillRect(0, 0, canvas.width, canvas.height);
	ctx.drawImage(bitmap, 0, 0);
	const { data, width, height } = ctx.getImageData(0, 0, canvas.width, canvas.height);
	const code = jsQR(data, width, height, { inversionAttempts: 'attemptBoth' });
	return code?.data ?? null;
}
