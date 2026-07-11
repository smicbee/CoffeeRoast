export const builtInRecipes = [
  '0-1200m Rest v1.0.kpro','0-1200m RTD v1.0.kpro','1200-1500 m Rest v1.0.kpro','1200-1500m RTD v1.0.kpro',
  '1500-2000m Rest v1.0.kpro','1500-2000m RTD v1.0.kpro','2000-2700m Rest v1.0.kpro','2000-2700m RTD v1.0.kpro',
  'Cupping v1.0.kpro','D-Roast.kpro','Decaf v1.0.kpro','Filter Origin.kpro','Peanut.kpro','Raost v5.kpro',
  'Robusta v1.0.kpro','Super dark v1.0.kpro','WBRC competition.kpro'
];

export async function loadBuiltInRecipes(base = 'recipes/') {
  const loaded = await Promise.all(builtInRecipes.map(async file => {
    try {
      const response = await fetch(base + encodeURIComponent(file));
      if (!response.ok) throw new Error(`${response.status}`);
      return parseRecipe(await response.text(), file);
    } catch (error) { console.warn(`Rezept ${file} konnte nicht geladen werden`, error); return null; }
  }));
  return loaded.filter(Boolean);
}

export function parseRecipe(text, fileName = 'Eigenes Rezept.kpro') {
  const fields = {};
  text.split(/\r?\n/).forEach(line => {
    const split = line.indexOf(':');
    if (split <= 0) return;
    fields[line.slice(0, split).trim()] = line.slice(split + 1).trim();
  });
  const raw = String(fields.roast_profile || '').split(',').map(Number).filter(Number.isFinite);
  let pairs = [];
  for (let i = 2; i + 1 < raw.length - 2; i += 2) pairs.push({ time: raw[i], temp: raw[i + 1] });
  if (pairs.length < 2) {
    for (let i = 0; i + 1 < raw.length; i += 2) pairs.push({ time: raw[i], temp: raw[i + 1] });
  }
  pairs = normalisePoints(pairs);
  if (pairs.length < 2) throw new Error('Das Rezept enthält keine brauchbare roast_profile-Kurve.');
  const maxTime = Math.min(1199, Math.ceil(Math.max(...pairs.map(p => p.time))));
  const profile = Array.from({ length: Math.max(2, maxTime + 1) }, (_, t) => linearInterpolate(pairs, t));
  const levels = deriveRoastLevels(fields, profile);
  return {
    fileName,
    name: fields.profile_short_name || fileName.replace(/\.kpro$/i, ''),
    designer: fields.profile_designer || '',
    description: (fields.profile_description || 'Keine Beschreibung hinterlegt.').replace(/\\v/g, '\n'),
    points: pairs,
    profile,
    duration: profile.length - 1,
    endTemp: profile[profile.length - 1],
    pid: {
      kp: numberOr(fields.roast_PID_Kp, 3),
      ki: numberOr(fields.roast_PID_Ki, 0.02),
      kd: numberOr(fields.roast_PID_Kd, 0.2),
      future: numberOr(fields.roast_target_in_future, 40)
    },
    expectedFirstCrack: numberOr(fields.expect_fc, 208),
    minDesiredRoR: numberOr(fields.roast_min_desired_rate_of_rise, 3),
    timeShift: numberOr(fields.roast_target_timeshift, 0),
    roastLevels: levels,
    source: text
  };
}

function normalisePoints(points) {
  const map = new Map();
  points.filter(p => Number.isFinite(p.time) && Number.isFinite(p.temp) && p.time >= 0 && p.time <= 3600 && p.temp >= -10 && p.temp <= 300)
    .forEach(p => map.set(p.time, p.temp));
  return [...map].map(([time, temp]) => ({ time, temp })).sort((a, b) => a.time - b.time);
}

function deriveRoastLevels(fields, profile) {
  const explicit = ['Light','City','FullCity','French','Italian'].map(name => numberOr(fields[`RoastLevel_${name}`], NaN));
  if (explicit.every(Number.isFinite)) return explicit.map(v => clamp(Math.round(v), 0, profile.length - 1));
  const temps = String(fields.roast_levels || '').split(',').map(Number).filter(Number.isFinite).slice(0, 5);
  const fallbackTemps = [196, 205, 212, 220, 228];
  return fallbackTemps.map((fallback, i) => findClosestTime(profile, temps[i] || fallback));
}

function findClosestTime(profile, target) {
  let index = 0, delta = Infinity;
  profile.forEach((temp, i) => { const d = Math.abs(temp - target); if (d < delta) { delta = d; index = i; } });
  return index;
}

// Stetige, stückweise lineare Interpolation zwischen den Rezeptstützpunkten.
// Dadurch liegt jedes Zwischenziel exakt auf der Verbindungslinie; es gibt
// weder Treppenstufen noch kubische Überschwinger zwischen zwei Punkten.
function linearInterpolate(points, x) {
  if (x <= points[0].time) return points[0].temp;
  if (x >= points[points.length - 1].time) return points[points.length - 1].temp;
  let i = 0;
  while (i < points.length - 2 && x > points[i + 1].time) i++;
  const left = points[i], right = points[i + 1];
  const ratio = (x - left.time) / (right.time - left.time);
  return left.temp + (right.temp - left.temp) * ratio;
}
function numberOr(value, fallback) { const n = Number.parseFloat(value); return Number.isFinite(n) ? n : fallback; }
function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
