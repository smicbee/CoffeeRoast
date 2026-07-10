import { WebSerialTransport, SimulationTransport } from './serial.js';
import { loadBuiltInRecipes, parseRecipe } from './recipes.js';
import { RoastEngine, RoastState } from './engine.js';
import { RoastChart, formatTime } from './chart.js';

const $ = id => document.getElementById(id);
const engine = new RoastEngine();
const chart = new RoastChart($('roastChart'), $('chartTooltip'));
let recipes = [], simulation = false, roastLevel = 0, toastTimer;
const logLines = [];

async function boot() {
  $('browserHint').hidden = WebSerialTransport.isSupported();
  bindEvents();
  try {
    recipes = await loadBuiltInRecipes();
    recipes.sort((a,b)=>a.name.localeCompare(b.name,'de'));
    renderRecipeOptions();
    const preferred = Number(localStorage.getItem('coffeeRoast.recipeIndex') || 0);
    selectRecipe(Math.min(preferred, recipes.length - 1));
  } catch (error) { showToast(error.message, true); }
  engine.addEventListener('update', e => render(e.detail));
  engine.emit();
}

function bindEvents() {
  $('connectButton').addEventListener('click', () => engine.connected ? disconnect() : connect());
  $('simulationButton').addEventListener('click', toggleSimulation);
  $('primaryActionButton').addEventListener('click', primaryAction);
  $('cooldownButton').addEventListener('click', () => engine.coolDown('Manuelle Abkühlung'));
  $('refreshStatusButton').addEventListener('click', refreshStatus);
  $('recipeSelect').addEventListener('change', e => selectRecipe(Number(e.target.value)));
  $('loadRecipeButton').addEventListener('click', () => $('recipeFileInput').click());
  $('recipeFileInput').addEventListener('change', importRecipe);
  $('fanSlider').addEventListener('input', e => { engine.initialFanPercent = Number(e.target.value); $('fanSliderValue').textContent = `${e.target.value} %`; });
  $('preheatInput').addEventListener('change', e => { engine.preheatTarget = clamp(Number(e.target.value),80,230); e.target.value=engine.preheatTarget; });
  $('roastLevelButtons').addEventListener('click', e => { const button=e.target.closest('[data-level]');if(!button)return;setRoastLevel(Number(button.dataset.level)); });
  $('resetZoomButton').addEventListener('click',()=>chart.reset());
  $('exportButton').addEventListener('click',exportCsv);
  ['kpInput','kiInput','kdInput'].forEach(id=>$(id).addEventListener('change',applyPid));
  document.querySelectorAll('.preflight-check').forEach(c=>c.addEventListener('change',updatePreflightButton));
  $('preflightDialog').addEventListener('close',()=>{if($('preflightDialog').returnValue==='confirm')engine.beginPreheat().catch(fail)});
  window.addEventListener('beforeunload',e=>{if([RoastState.PREHEATING,RoastState.RUNNING].includes(engine.state)){e.preventDefault();e.returnValue='Die Heizung ist aktiv.'}});
  navigator.serial?.addEventListener('disconnect',()=>{if(engine.connected){engine.enterFailsafe('USB-Verbindung getrennt');showToast('USB-Verbindung wurde getrennt – Failsafe aktiv.',true)}});
}

function makeTransport() { return simulation ? new SimulationTransport(addLog) : new WebSerialTransport(addLog); }
async function connect() {
  try { engine.setTransport(makeTransport()); await engine.connect(); showToast(simulation?'Simulation gestartet.':'CoffeeRoast-Controller verbunden.'); }
  catch(error){fail(error)}
}
async function disconnect(){try{await engine.disconnect();showToast('Controller sicher getrennt.')}catch(error){fail(error)}}
async function toggleSimulation(){
  if(engine.connected) await disconnect();
  simulation=!simulation;$('simulationButton').setAttribute('aria-pressed',String(simulation));
  if(simulation){await connect()}else showToast('Hardwaremodus aktiv.');
}

async function primaryAction() {
  if(!engine.connected){await connect();return}
  if(engine.state===RoastState.IDLE){await openPreflight();return}
  if(engine.state===RoastState.READY){engine.beginRoast();showToast('Röstung gestartet. Bohnen jetzt einfüllen.');return}
  if(engine.state===RoastState.RUNNING||engine.state===RoastState.PREHEATING){await engine.coolDown('Manuell beendet');return}
  if(engine.state===RoastState.COOLING){if(confirm('Die Maschine kühlt noch. Trotzdem eine neue Röstung starten?'))await openPreflight();return}
  if(engine.state===RoastState.FAILSAFE){showToast('Failsafe bleibt aktiv. Ursache beheben und Controller neu verbinden.',true)}
}

async function openPreflight(){
  document.querySelectorAll('.preflight-check').forEach(c=>c.checked=false);updatePreflightButton();
  $('preflightStatus').textContent='Controllerstatus wird geprüft …';$('preflightDialog').showModal();
  try{const status=await engine.refreshStatus();$('preflightStatus').textContent=status||'Simulation: keine Hardwarewarnungen.';if(/failsafe/i.test(status)){$('confirmPreflightButton').disabled=true;showToast('Controller meldet Failsafe.',true)}}
  catch(error){$('preflightStatus').textContent=`Status nicht verfügbar: ${error.message}`;$('confirmPreflightButton').disabled=true}
}
function updatePreflightButton(){const all=[...document.querySelectorAll('.preflight-check')].every(c=>c.checked);$('confirmPreflightButton').disabled=!all||engine.state===RoastState.FAILSAFE}
async function refreshStatus(){try{const s=await engine.refreshStatus();showToast(s||'Kein Status empfangen.')}catch(error){fail(error)}}

function renderRecipeOptions(){$('recipeSelect').innerHTML=recipes.map((r,i)=>`<option value="${i}">${escapeHtml(r.name)}</option>`).join('')}
function selectRecipe(index){if(!recipes[index])return;$('recipeSelect').value=String(index);engine.setRecipe(recipes[index]);localStorage.setItem('coffeeRoast.recipeIndex',String(index));updateRecipeCard(recipes[index]);setRoastLevel(0);chart.reset()}
function updateRecipeCard(recipe){$('recipeDescription').textContent=recipe.description;$('recipeDuration').textContent=formatTime(recipe.duration);$('recipeEndTemp').textContent=`${Math.round(recipe.endTemp)} °C`;$('recipePointCount').textContent=String(recipe.points.length);$('kpInput').value=fmt(recipe.pid.kp,3);$('kiInput').value=fmt(recipe.pid.ki,3);$('kdInput').value=fmt(recipe.pid.kd,3)}
async function importRecipe(event){const file=event.target.files?.[0];if(!file)return;try{const recipe=parseRecipe(await file.text(),file.name);recipes.push(recipe);renderRecipeOptions();selectRecipe(recipes.length-1);showToast(`${recipe.name} geladen.`)}catch(error){fail(error)}finally{event.target.value=''}}
function setRoastLevel(level){roastLevel=level;document.querySelectorAll('.bean-level').forEach(b=>b.classList.toggle('selected',Number(b.dataset.level)===level));engine.setRoastLevel(level);$('roastStopTime').textContent=level&&engine.stopAt>=0?`Auto-Stopp ${formatTime(engine.stopAt)}`:'kein Auto-Stopp'}
function applyPid(){engine.pid.configure({kp:Number($('kpInput').value),ki:Number($('kiInput').value),kd:Number($('kdInput').value),future:engine.recipe?.pid.future||40});showToast('PID-Werte übernommen.')}

function render(s) {
  const meta=s.connected?stateMeta(s.state):{title:'Nicht verbunden',subtitle:simulation?'Simulation starten oder Hardwaremodus wählen.':'CoffeeRoast-Controller über USB verbinden.',color:'#686d75'};$('stateTitle').textContent=meta.title;$('stateSubtitle').textContent=meta.subtitle;$('stateIcon').style.color=meta.color;
  $('currentTemp').textContent=number(s.temperature);$('targetTemp').textContent=s.target>0?number(s.target):'—';$('elapsedTime').textContent=formatTime(s.elapsed);
  $('heaterPercent').textContent=String(Math.round(s.heater/2.55));$('fanPercent').textContent=String(Math.round(s.fan/2.55));
  $('tempTrend').textContent=temperatureTrend(s.samples);$('targetDelta').textContent=Number.isFinite(s.temperature)&&s.target>0?`${signed(s.target-s.temperature)} °C Differenz`:'Profil inaktiv';
  $('remainingTime').textContent=s.recipe&&s.state===RoastState.RUNNING?`${formatTime(Math.max(0,(s.stopAt>=0?s.stopAt:s.recipe.duration)-s.elapsed))} verbleibend`:'Noch nicht gestartet';
  $('outputHint').textContent=s.state===RoastState.FAILSAFE?'Failsafe-Ausgänge':s.heater>0?'Heizung aktiv':'Heizung aus';
  $('connectionText').textContent=s.connected?(s.portName||'Verbunden'):'Controller verbinden';$('connectButton').classList.toggle('connected',s.connected);
  $('diagConnection').textContent=s.connected?'Verbunden':'Getrennt';$('diagFirmware').textContent=s.status||'—';$('diagErrors').textContent=String(s.sensorErrors);$('diagLastResponse').textContent=lastLogResponse();
  $('safetyBadge').textContent=s.state===RoastState.FAILSAFE?'Failsafe':s.heater>0?'Heizung aktiv':'Sicher';$('safetyBadge').classList.toggle('safe',s.state!==RoastState.FAILSAFE&&s.heater===0);
  updateActions(s);updateStepper(s.state);chart.setData(s);
}
function updateActions(s){const b=$('primaryActionButton'),cool=$('cooldownButton');b.disabled=!s.recipe||s.state===RoastState.FAILSAFE;cool.disabled=!s.connected||![RoastState.PREHEATING,RoastState.READY,RoastState.RUNNING].includes(s.state);let icon='▶',text='Sicherheitscheck starten',sub='Vorheizen vorbereiten';if(!s.connected){text='Controller verbinden';sub=simulation?'Simulation starten':'USB-Gerät auswählen'}else if(s.state===RoastState.PREHEATING){icon='■';text='Vorheizen abbrechen';sub='Heizung aus & abkühlen'}else if(s.state===RoastState.READY){text='Röstung starten';sub='Bohnen einfüllen und Profil starten'}else if(s.state===RoastState.RUNNING){icon='■';text='Röstung beenden';sub='Sofort in Abkühlung wechseln'}else if(s.state===RoastState.COOLING){text='Neue Röstung';sub='Nur wenn sicher und gewollt'}else if(s.state===RoastState.FAILSAFE){icon='!';text='FAILSAFE';sub='Neu verbinden nach Fehlerbehebung'}$('primaryActionIcon').textContent=icon;$('primaryActionText').textContent=text;$('primaryActionSubtext').textContent=sub}
function updateStepper(state){const ids=['stepConnect','stepPreheat','stepRoast','stepCool'];ids.forEach(id=>$(id).classList.remove('active','done'));if(engine.connected)$('stepConnect').classList.add('done');if(state===RoastState.PREHEATING)$('stepPreheat').classList.add('active');if(state===RoastState.READY)$('stepPreheat').classList.add('done');if(state===RoastState.RUNNING){$('stepPreheat').classList.add('done');$('stepRoast').classList.add('active')}if(state===RoastState.COOLING){$('stepPreheat').classList.add('done');$('stepRoast').classList.add('done');$('stepCool').classList.add('active')}['phasePreheat','phaseRoast','phaseCool'].forEach(id=>$(id).classList.remove('active'));if(state===RoastState.PREHEATING||state===RoastState.READY)$('phasePreheat').classList.add('active');if(state===RoastState.RUNNING)$('phaseRoast').classList.add('active');if(state===RoastState.COOLING)$('phaseCool').classList.add('active')}

function exportCsv(){if(!engine.samples.length){showToast('Noch keine Messdaten zum Exportieren.',true);return}const rows=['Zeit_s;Zeit;Temperatur_C;Ziel_C;Heizung_PWM;Heizung_Prozent;Luefter_PWM;Luefter_Prozent;Status'];engine.samples.forEach(s=>rows.push([s.time.toFixed(1),formatTime(s.time),fmt(s.temperature,2),fmt(s.target,2),Math.round(s.heater),Math.round(s.heater/2.55),Math.round(s.fan),Math.round(s.fan/2.55),s.state].join(';')));const blob=new Blob(['\uFEFF'+rows.join('\r\n')],{type:'text/csv;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`CoffeeRoast_${new Date().toISOString().replace(/[:.]/g,'-')}.csv`;a.click();URL.revokeObjectURL(a.href);showToast('CSV exportiert.')}
function addLog(line){logLines.unshift(line);if(logLines.length>100)logLines.length=100;$('serialLog').textContent=logLines.join('\n')}
function lastLogResponse(){return logLines.find(l=>l.includes('←'))?.split('←')[1]?.trim()||'—'}
function temperatureTrend(samples){if(samples.length<3)return'Warte auf Verlauf';const a=samples[Math.max(0,samples.length-8)],b=samples.at(-1),dt=b.time-a.time;if(dt<=0)return'Warte auf Verlauf';const rate=(b.temperature-a.temperature)/dt*60;return`${signed(rate)} °C/min`}
function stateMeta(state){return({idle:{title:'Bereit',subtitle:'Rezept wählen und sicher starten.',color:'#66d19e'},preheating:{title:'Vorheizen',subtitle:'Kammer leer lassen, bis die Zieltemperatur erreicht ist.',color:'#ff635f'},ready:{title:'Bereit zum Rösten',subtitle:'Bohnen einfüllen und Röstprofil starten.',color:'#66d19e'},running:{title:'Röstung läuft',subtitle:'Temperaturprofil wird automatisch geregelt.',color:'#e8793e'},cooling:{title:'Abkühlen',subtitle:'Heizung aus, Lüfter führt Wärme ab.',color:'#73a8ff'},failsafe:{title:'FAILSAFE',subtitle:'Heizung aus. Ursache vor Neustart beheben.',color:'#ff635f'}})[state]}
function showToast(message,error=false){clearTimeout(toastTimer);$('toast').textContent=message;$('toast').classList.toggle('error',error);$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,4200)}function fail(error){console.error(error);showToast(error?.message||String(error),true)}
function number(v){return Number.isFinite(v)?String(Math.round(v)):'—'}function fmt(v,d=1){return Number.isFinite(Number(v))?Number(v).toFixed(d).replace(/\.?0+$/,''):'—'}function signed(v){return`${v>=0?'+':''}${fmt(v,1)}`}function clamp(v,a,b){return Math.max(a,Math.min(b,v))}function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
boot();
