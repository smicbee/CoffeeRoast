export class RoastChart {
  constructor(canvas, tooltip) {
    this.canvas=canvas;this.tooltip=tooltip;this.snapshot=null;this.view={minX:0,maxX:900,minY:0,maxY:260};
    this.resizeObserver=new ResizeObserver(()=>this.draw());this.resizeObserver.observe(canvas);
    canvas.addEventListener('mousemove',e=>this.pointer(e));canvas.addEventListener('mouseleave',()=>tooltip.hidden=true);
    canvas.addEventListener('wheel',e=>this.zoom(e),{passive:false});
  }
  setData(snapshot){this.snapshot=snapshot;if(snapshot.recipe&&this.view.maxX===900)this.view.maxX=Math.max(600,Math.ceil(snapshot.recipe.duration/60)*60);this.draw()}
  reset(){this.view={minX:0,maxX:Math.max(600,Math.ceil((this.snapshot?.recipe?.duration||900)/60)*60),minY:0,maxY:260};this.draw()}
  size(){const rect=this.canvas.getBoundingClientRect(),dpr=Math.min(2,devicePixelRatio||1);if(this.canvas.width!==Math.round(rect.width*dpr)||this.canvas.height!==Math.round(rect.height*dpr)){this.canvas.width=Math.round(rect.width*dpr);this.canvas.height=Math.round(rect.height*dpr)}return{w:rect.width,h:rect.height,dpr}}
  draw(){const {w,h,dpr}=this.size(),ctx=this.canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);const p={l:45,r:42,t:12,b:32},pw=w-p.l-p.r,ph=h-p.t-p.b;if(pw<=0)return;
    const x=v=>p.l+(v-this.view.minX)/(this.view.maxX-this.view.minX)*pw,y=v=>p.t+ph-(v-this.view.minY)/(this.view.maxY-this.view.minY)*ph;
    ctx.font='9px Space Mono,monospace';ctx.lineWidth=1;
    for(let temp=0;temp<=this.view.maxY;temp+=40){const yy=y(temp);ctx.strokeStyle='#282b31';ctx.beginPath();ctx.moveTo(p.l,yy);ctx.lineTo(w-p.r,yy);ctx.stroke();ctx.fillStyle='#6c7078';ctx.textAlign='right';ctx.fillText(`${temp}°`,p.l-8,yy+3)}
    const step=this.view.maxX>1200?240:120;for(let sec=0;sec<=this.view.maxX;sec+=step){const xx=x(sec);ctx.strokeStyle='#202329';ctx.beginPath();ctx.moveTo(xx,p.t);ctx.lineTo(xx,p.t+ph);ctx.stroke();ctx.fillStyle='#6c7078';ctx.textAlign='center';ctx.fillText(formatTime(sec),xx,h-9)}
    if(!this.snapshot)return;const s=this.snapshot;
    if(s.recipe)drawSeries(ctx,s.recipe.profile.map((v,i)=>({time:i,value:v})),x,y,'#e8793e',2,0,this.view);
    drawSeries(ctx,s.samples.map(a=>({time:a.time,value:a.temperature})),x,y,'#f6e6d6',2.5,0,this.view);
    drawSeries(ctx,s.samples.map(a=>({time:a.time,value:a.heater/255*260})),x,y,'#ff635f',1.2,.72,this.view);
    drawSeries(ctx,s.samples.map(a=>({time:a.time,value:a.fan/255*260})),x,y,'#73a8ff',1.2,.72,this.view);
    if(s.elapsed>0){const xx=x(s.elapsed);ctx.strokeStyle='#f5e2d088';ctx.setLineDash([4,5]);ctx.beginPath();ctx.moveTo(xx,p.t);ctx.lineTo(xx,p.t+ph);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#f5e2d0';ctx.beginPath();ctx.arc(xx,y(s.temperature),4,0,Math.PI*2);ctx.fill()}
  }
  pointer(e){if(!this.snapshot?.recipe)return;const r=this.canvas.getBoundingClientRect(),p={l:45,r:42,t:12,b:32},ratio=(e.clientX-r.left-p.l)/(r.width-p.l-p.r);if(ratio<0||ratio>1){this.tooltip.hidden=true;return}const time=this.view.minX+ratio*(this.view.maxX-this.view.minX),index=Math.round(time);const target=this.snapshot.recipe.profile[Math.min(index,this.snapshot.recipe.profile.length-1)];const sample=nearest(this.snapshot.samples,time);this.tooltip.innerHTML=`<b>${formatTime(time)}</b><br>Ziel ${formatNumber(target)} °C${sample?`<br>Ist ${formatNumber(sample.temperature)} °C<br>Heizung ${Math.round(sample.heater/2.55)} % · Lüfter ${Math.round(sample.fan/2.55)} %`:''}`;this.tooltip.hidden=false;this.tooltip.style.left=`${Math.min(r.width-175,Math.max(8,e.clientX-r.left+12))}px`;this.tooltip.style.top=`${Math.max(5,e.clientY-r.top-70)}px`}
  zoom(e){e.preventDefault();const factor=e.deltaY>0?1.15:.87,span=(this.view.maxX-this.view.minX)*factor,center=(this.view.maxX+this.view.minX)/2;this.view.minX=Math.max(0,center-span/2);this.view.maxX=this.view.minX+Math.min(2400,Math.max(180,span));this.draw()}
}
function drawSeries(ctx,items,x,y,color,width,alpha,view){ctx.save();ctx.strokeStyle=color;ctx.globalAlpha=alpha?1-alpha:1;ctx.lineWidth=width;ctx.lineJoin='round';ctx.lineCap='round';ctx.beginPath();let started=false;for(const p of items){if(!Number.isFinite(p.value)||p.time<view.minX||p.time>view.maxX)continue;const xx=x(p.time),yy=y(p.value);if(!started){ctx.moveTo(xx,yy);started=true}else ctx.lineTo(xx,yy)}if(started)ctx.stroke();ctx.restore()}
function nearest(samples,time){if(!samples.length)return null;return samples.reduce((best,s)=>Math.abs(s.time-time)<Math.abs(best.time-time)?s:best,samples[0])}
export function formatTime(seconds){seconds=Math.max(0,Math.round(seconds||0));return`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`}
function formatNumber(v){return Number.isFinite(v)?Math.round(v):'—'}
