/*
 * Firmas digitales - utilidades compartidas (editor y página pública de firma).
 * Requiere pdf.js 3.x cargado como global `pdfjsLib`.
 *
 * Coordenadas de los recuadros: fracciones (0-1) de la página tal y como se
 * muestra (origen arriba-izquierda, rotación de la página aplicada).
 */
(function () {
    'use strict';

    const WORKER_SRC = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

    /**
     * Pinta todas las páginas del PDF dentro de `container`.
     * Cada página queda como:
     *   <div class="sig-page" data-page="N"><canvas></canvas><div class="sig-layer"></div></div>
     * Las páginas se renderizan de forma diferida cuando se acercan al viewport.
     */
    async function renderPdf(container, url, options) {
        options = options || {};
        pdfjsLib.GlobalWorkerOptions.workerSrc = WORKER_SRC;
        const pdf = await pdfjsLib.getDocument({ url: url, withCredentials: true }).promise;
        const pages = [];

        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const vp = page.getViewport({ scale: 1 });

            const wrap = document.createElement('div');
            wrap.className = 'sig-page';
            wrap.dataset.page = String(i);
            wrap.style.aspectRatio = vp.width + ' / ' + vp.height;

            const canvas = document.createElement('canvas');
            const layer = document.createElement('div');
            layer.className = 'sig-layer';
            const label = document.createElement('div');
            label.className = 'sig-page-label';
            label.textContent = i + ' / ' + pdf.numPages;

            wrap.appendChild(canvas);
            wrap.appendChild(layer);
            wrap.appendChild(label);
            container.appendChild(wrap);

            const info = { num: i, page: page, wrap: wrap, canvas: canvas, layer: layer, width: vp.width, height: vp.height, rendered: false };
            pages.push(info);
            if (options.onPage) options.onPage(info);
        }

        async function renderPage(p) {
            if (p.rendered) return;
            p.rendered = true;
            const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
            const scale = Math.max(p.wrap.clientWidth, 300) / p.width * dpr;
            const viewport = p.page.getViewport({ scale: scale });
            p.canvas.width = Math.floor(viewport.width);
            p.canvas.height = Math.floor(viewport.height);
            await p.page.render({ canvasContext: p.canvas.getContext('2d'), viewport: viewport }).promise;
        }

        if ('IntersectionObserver' in window) {
            const io = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        const p = pages[Number(entry.target.dataset.page) - 1];
                        renderPage(p);
                        io.unobserve(entry.target);
                    }
                });
            }, { rootMargin: '800px 0px' });
            pages.forEach(function (p) { io.observe(p.wrap); });
        } else {
            for (const p of pages) { await renderPage(p); }
        }

        return { pdf: pdf, pages: pages };
    }

    /** Lienzo para dibujar la firma (garabato) con ratón, dedo o lápiz. */
    function SignaturePad(canvas, opts) {
        opts = opts || {};
        const ctx = canvas.getContext('2d');
        let drawing = false;
        let points = [];
        let empty = true;
        const color = opts.color || '#1a237e';
        const onChange = opts.onChange || function () {};

        function resize() {
            const ratio = Math.min(window.devicePixelRatio || 1, 3);
            const rect = canvas.getBoundingClientRect();
            if (!rect.width) return;
            canvas.width = Math.floor(rect.width * ratio);
            canvas.height = Math.floor(rect.height * ratio);
            ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.strokeStyle = color;
            ctx.fillStyle = color;
            ctx.lineWidth = opts.lineWidth || 2.6;
            empty = true;
            onChange(empty);
        }

        function pos(e) {
            const rect = canvas.getBoundingClientRect();
            return { x: e.clientX - rect.left, y: e.clientY - rect.top };
        }

        canvas.addEventListener('pointerdown', function (e) {
            e.preventDefault();
            canvas.setPointerCapture(e.pointerId);
            drawing = true;
            const p = pos(e);
            points = [p];
            ctx.beginPath();
            ctx.arc(p.x, p.y, ctx.lineWidth / 2, 0, Math.PI * 2);
            ctx.fill();
            if (empty) { empty = false; onChange(empty); }
        });
        canvas.addEventListener('pointermove', function (e) {
            if (!drawing) return;
            e.preventDefault();
            const p = pos(e);
            points.push(p);
            if (points.length >= 3) {
                const a = points[points.length - 3];
                const b = points[points.length - 2];
                const mid1 = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
                const mid2 = { x: (b.x + p.x) / 2, y: (b.y + p.y) / 2 };
                ctx.beginPath();
                ctx.moveTo(mid1.x, mid1.y);
                ctx.quadraticCurveTo(b.x, b.y, mid2.x, mid2.y);
                ctx.stroke();
            } else {
                const a = points[0];
                ctx.beginPath();
                ctx.moveTo(a.x, a.y);
                ctx.lineTo(p.x, p.y);
                ctx.stroke();
            }
        });
        ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (ev) {
            canvas.addEventListener(ev, function () { drawing = false; points = []; });
        });

        return {
            resize: resize,
            clear: function () { ctx.clearRect(0, 0, canvas.width, canvas.height); empty = true; onChange(empty); },
            isEmpty: function () { return empty; },
            /** PNG transparente recortado al trazo (con un pequeño margen). */
            toDataURL: function () {
                const w = canvas.width, h = canvas.height;
                const data = ctx.getImageData(0, 0, w, h).data;
                let minX = w, minY = h, maxX = -1, maxY = -1;
                for (let y = 0; y < h; y++) {
                    for (let x = 0; x < w; x++) {
                        if (data[(y * w + x) * 4 + 3] > 0) {
                            if (x < minX) minX = x;
                            if (x > maxX) maxX = x;
                            if (y < minY) minY = y;
                            if (y > maxY) maxY = y;
                        }
                    }
                }
                if (maxX < 0) return canvas.toDataURL('image/png');
                const pad = 6;
                minX = Math.max(minX - pad, 0); minY = Math.max(minY - pad, 0);
                maxX = Math.min(maxX + pad, w - 1); maxY = Math.min(maxY + pad, h - 1);
                const out = document.createElement('canvas');
                out.width = maxX - minX + 1;
                out.height = maxY - minY + 1;
                out.getContext('2d').drawImage(canvas, minX, minY, out.width, out.height, 0, 0, out.width, out.height);
                return out.toDataURL('image/png');
            },
        };
    }

    function getCookie(name) {
        const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return m ? decodeURIComponent(m.pop()) : '';
    }

    window.SignaturePdf = { renderPdf: renderPdf, SignaturePad: SignaturePad, getCookie: getCookie };
})();
