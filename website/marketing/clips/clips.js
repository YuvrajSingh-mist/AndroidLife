// AndroidLife clip runner - preload GIFs, then play long enough to see taps.

export function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function show(el) {
  if (!el) return;
  el.classList.add("is-on", "on", "in", "show");
}

export function hide(el) {
  if (!el) return;
  el.classList.remove("is-on", "on", "in", "show");
}

export function only(layerId) {
  document.querySelectorAll(".layer").forEach((layer) => {
    layer.classList.toggle("is-on", layer.id === layerId);
  });
}

export function bindControls(replayFn) {
  const replay = document.getElementById("replay");
  if (replay) replay.addEventListener("click", () => replayFn());
  // Wait for fonts + first paint, then start
  if (document.fonts?.ready) {
    document.fonts.ready.then(() => replayFn());
  } else {
    requestAnimationFrame(() => replayFn());
  }
}

/** Preload one or many image URLs. Resolves when all are decoded. */
export function preloadImages(urls) {
  const list = [...new Set(urls.filter(Boolean))];
  return Promise.all(
    list.map(
      (src) =>
        new Promise((resolve, reject) => {
          const img = new Image();
          img.decoding = "async";
          img.onload = async () => {
            try {
              if (img.decode) await img.decode();
            } catch (_) {
              /* ignore decode errors; bitmap is still usable */
            }
            resolve(img);
          };
          img.onerror = () => reject(new Error(`Failed to load ${src}`));
          img.src = src;
        })
    )
  );
}

/**
 * Point an <img> at a GIF only after preload, forcing a fresh decode/play
 * by cache-busting with a fragment when restarting.
 */
export async function setGif(imgEl, src, { restart = true } = {}) {
  if (!imgEl || !src) return;
  await preloadImages([src]);
  const url = restart ? `${src}${src.includes("?") ? "&" : "?"}t=${Date.now()}` : src;
  imgEl.src = url;
  try {
    if (imgEl.decode) await imgEl.decode();
  } catch (_) {}
}

/** Hold on a playing GIF for `ms` (use full loop length from known duration). */
export async function holdGif(ms) {
  await wait(ms);
}
