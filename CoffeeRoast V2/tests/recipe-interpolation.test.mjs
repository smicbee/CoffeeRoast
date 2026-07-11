import { readFile } from 'node:fs/promises';
import { parseRecipe } from '../src/recipes.js';

function assert(condition, message) {
  if (!condition) throw new Error(`Fehlgeschlagen: ${message}`);
}

const recipeText = await readFile(new URL('../recipes/Cupping v1.0.kpro', import.meta.url), 'utf8');
const recipe = parseRecipe(recipeText, 'Cupping v1.0.kpro');
assert(recipe.points.length >= 2, 'Rezept besitzt Stützpunkte');

for (let i = 0; i < recipe.points.length - 1; i++) {
  const left = recipe.points[i], right = recipe.points[i + 1];
  const start = Math.max(0, Math.ceil(left.time));
  const end = Math.min(recipe.profile.length - 1, Math.floor(right.time));
  for (let second = start; second <= end; second++) {
    const ratio = (second - left.time) / (right.time - left.time);
    const expected = left.temp + (right.temp - left.temp) * ratio;
    assert(Math.abs(recipe.profile[second] - expected) < 1e-9, `Sekunde ${second} liegt exakt auf der linearen Verbindung`);
  }
}

const source = await readFile(new URL('../src/recipes.js', import.meta.url), 'utf8');
assert(source.includes('linearInterpolate(pairs, t)'), 'Parser verwendet lineare Interpolation');
assert(!/pchip|Hermite|t\s*\*\*\s*3/i.test(source), 'Keine kubische Interpolation mehr aktiv');

console.log('CoffeeRoast Rezeptkurven: stetige lineare Interpolation OK');
