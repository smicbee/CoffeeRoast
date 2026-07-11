import { readFile } from 'node:fs/promises';
import { parseRecipe } from '../src/recipes.js';

function assert(condition, message) { if (!condition) throw new Error(`Fehlgeschlagen: ${message}`); }
const recipeText = await readFile(new URL('../recipes/Cupping v1.0.kpro', import.meta.url), 'utf8');
const recipe = parseRecipe(recipeText, 'Cupping v1.0.kpro');
assert(recipe.points.length >= 3, 'Rezept besitzt genügend Stützpunkte');

for (let i=0;i<recipe.points.length-1;i++) {
  const left=recipe.points[i],right=recipe.points[i+1],lo=Math.min(left.temp,right.temp)-1e-9,hi=Math.max(left.temp,right.temp)+1e-9;
  for(let second=Math.ceil(left.time);second<=Math.min(Math.floor(right.time),recipe.profile.length-1);second++)
    assert(recipe.profile[second]>=lo&&recipe.profile[second]<=hi,`kein Überschwingen bei Sekunde ${second}`);
  if(Number.isInteger(left.time)&&left.time<recipe.profile.length)assert(Math.abs(recipe.profile[left.time]-left.temp)<1e-9,`Stützpunkt ${left.time} exakt`);
}
const source=await readFile(new URL('../src/recipes.js',import.meta.url),'utf8');
assert(source.includes('pchipInterpolate(pairs, t)'),'Parser verwendet geglättete PCHIP-Kurve');
assert(/Hermite-Interpolation/.test(source)&&/slope\[i\]/.test(source),'gemeinsame Tangenten an Stützpunkten implementiert');
assert(!source.includes('linearInterpolate'),'scharfkantige lineare Interpolation entfernt');
console.log('CoffeeRoast Rezeptkurven: rund geglättete monotone PCHIP-Interpolation OK');
