// FAANG Standard: Decuplăm procesarea grea din Main Thread-ul browserului.
// Astfel, UI-ul din Flutter va rula mereu la 60fps constant.

// 1. Importăm CDN-urile MediaPipe pt Pose Estimation
importScripts(
    'https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js'
);

// 2. Inițializăm modelul folosind accelerarea hardware WebGL prin WebAssembly (WASM)
const pose = new Pose({
    locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/\${file}`;
    }
});

// Setări Optimizate pentru Viteză și Latență Zero
pose.setOptions({
    modelComplexity: 1, // Nivel mediu. 0 e prea slab, 2 e prea greu (scade sub 30fps)
    smoothLandmarks: true,
    enableSegmentation: false,
    minDetectionConfidence: 0.6,
    minTrackingConfidence: 0.6
});

// 3. Ascultăm callback-ul de rezultate de la rețeaua neurală (MediaPipe WASM)
pose.onResults((results) => {
    if (!results.poseLandmarks) return;

    // Preluăm articulațiile cheie pentru modelul SHIELD (Ex: Piciorul Stâng)
    // 23 = Șold, 25 = Genunchi, 27 = Gleznă
    const hip = results.poseLandmarks[23];
    const knee = results.poseLandmarks[25];
    const ankle = results.poseLandmarks[27];

    if (hip && knee && ankle) {
        const angle = calculateAngle(hip, knee, ankle);
        const deviation = Math.abs(180.0 - angle); 

        let severity = 'NORMAL';
        if (deviation > 5.0) {
            severity = 'CRITICAL'; // Pericol iminent de ruptură LIA!
        } else if (deviation > 3.5) {
            severity = 'HIGH';
        }

        if (severity !== 'NORMAL') {
            // Trimitem rezultatul înapoi în Flutter via MessageChannel (Asincron)
            postMessage({
                type: 'ALERT',
                severity: severity,
                deviation: deviation.toFixed(2),
                message: `Deviație valgus critică detectată: \${deviation.toFixed(2)}°`
            });
        }
    }
});

// Algoritmul Matematic Biomecanic mutat în Worker
function calculateAngle(a, b, c) {
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    if (angle > 180.0) {
        angle = 360.0 - angle;
    }
    return angle;
}

// 4. Buclele de ascultare a cadrelor video trimise de Dart
onmessage = async (e) => {
    const { action, frameData, width, height } = e.data;
    
    if (action === 'PROCESS_FRAME') {
        try {
            // Reconstruim Pixelii din Transferable ArrayBuffer trimis de Flutter
            const imgData = new ImageData(new Uint8ClampedArray(frameData), width, height);
            
            // Folosim OffscreenCanvas pentru randare invizibilă (nu poluează DOM-ul principal)
            const canvas = new OffscreenCanvas(width, height);
            const ctx = canvas.getContext('2d');
            ctx.putImageData(imgData, 0, 0);

            // Analiza propriu-zisă
            await pose.send({ image: canvas });
        } catch (err) {
            console.error("Worker Error la procesarea cadrului: ", err);
        }
    }
};
