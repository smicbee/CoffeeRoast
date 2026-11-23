#!/usr/bin/python3
"""Finish connections left by wide-rule Freerouting using obstacle-aware 45-degree routes."""
from pathlib import Path
import heapq, math
import pcbnew
P=Path(__file__).resolve().parents[1]/'CoffeeRoast-Control-RevC-UltraCompact.kicad_pcb'
b=pcbnew.LoadBoard(str(P));CLEAR=.28;STEP=.5

def add_track(net,pts,layer,width):
 n=b.FindNet(net)
 for a,c in zip(pts,pts[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(width));t.SetStart(pcbnew.VECTOR2I_MM(*a));t.SetEnd(pcbnew.VECTOR2I_MM(*c));b.Add(t)
def add_via(net,p,size=.8,drill=.4):
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(pcbnew.VECTOR2I_MM(*p));v.SetWidth(pcbnew.FromMM(size));v.SetDrill(pcbnew.FromMM(drill));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def pdist(px,py,a,b,c,d):
 vx,vy=c-a,d-b;wx,wy=px-a,py-b;q=(wx*vx+wy*vy)/(vx*vx+vy*vy) if vx or vy else 0;q=max(0,min(1,q));return math.hypot(px-(a+q*vx),py-(b+q*vy))
def obstacle_data(layer,target,width):
 lines=[];circles=[];rects=[];margin=width/2+CLEAR
 for t in b.GetTracks():
  if t.GetNetname()==target:continue
  if isinstance(t,pcbnew.PCB_VIA):
   p=t.GetPosition();circles.append((p.x/1e6,p.y/1e6,t.GetWidth(layer)/2e6+margin))
  elif t.GetLayer()==layer:
   s,e=t.GetStart(),t.GetEnd();lines.append((s.x/1e6,s.y/1e6,e.x/1e6,e.y/1e6,t.GetWidth()/2e6+margin))
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()==target or not p.IsOnLayer(layer):continue
   r=p.GetBoundingBox();rects.append((r.GetX()/1e6-margin,r.GetY()/1e6-margin,(r.GetX()+r.GetWidth())/1e6+margin,(r.GetY()+r.GetHeight())/1e6+margin))
 rects += [(48,0,96,21),(0,0,96,.6),(0,59.4,96,60),(0,0,.6,60),(95.4,0,96,60)]
 return lines,circles,rects
def safe_seg(a,c,data):
 lines,circles,rects=data;dist=math.hypot(c[0]-a[0],c[1]-a[1]);n=max(1,math.ceil(dist/.1))
 for i in range(n+1):
  q=i/n;x=a[0]+q*(c[0]-a[0]);y=a[1]+q*(c[1]-a[1])
  if any(x0<=x<=x1 and y0<=y<=y1 for x0,y0,x1,y1 in rects):return False
  if any(math.hypot(x-cx,y-cy)<=r for cx,cy,r in circles):return False
  if any(pdist(x,y,x0,y0,x1,y1)<=r for x0,y0,x1,y1,r in lines):return False
 return True
def astar(start,goal,layer,net,width):
 data=obstacle_data(layer,net,width)
 def q(p):return (round(p[0]/STEP)*STEP,round(p[1]/STEP)*STEP)
 s,g=q(start),q(goal);dirs=[(STEP,0),(-STEP,0),(0,STEP),(0,-STEP),(STEP,STEP),(STEP,-STEP),(-STEP,STEP),(-STEP,-STEP)]
 openq=[(0.0,s)];cost={s:0.0};parent={s:None}
 while openq:
  _,u=heapq.heappop(openq)
  if u==g:break
  for dx,dy in dirs:
   v=(u[0]+dx,u[1]+dy)
   if not(.7<=v[0]<=95.3 and .7<=v[1]<=59.3) or not safe_seg(u,v,data):continue
   nc=cost[u]+math.hypot(dx,dy)
   if nc<cost.get(v,1e99):cost[v]=nc;parent[v]=u;heapq.heappush(openq,(nc+math.hypot(v[0]-g[0],v[1]-g[1]),v))
 else:raise RuntimeError(f'no {net} route {start}->{goal}')
 path=[];u=g
 while u is not None:path.append(u);u=parent[u]
 path.reverse();out=[path[0]]
 for i in range(1,len(path)-1):
  a,m,c=path[i-1],path[i],path[i+1]
  if (m[0]-a[0],m[1]-a[1])!=(c[0]-m[0],c[1]-m[1]):out.append(m)
 out.append(path[-1]);out[0]=start;out[-1]=goal;return out

def route_multilayer(start,goal,net,width):
 layers=[pcbnew.F_Cu,pcbnew.B_Cu]
 data=[obstacle_data(layer,net,width) for layer in layers]
 via_data=[obstacle_data(layer,net,.8) for layer in layers]
 def q(p):return (round(p[0]/STEP)*STEP,round(p[1]/STEP)*STEP)
 sxy,gxy=q(start),q(goal);s=(sxy[0],sxy[1],1);g=(gxy[0],gxy[1],1)
 dirs=[(STEP,0),(-STEP,0),(0,STEP),(0,-STEP),(STEP,STEP),(STEP,-STEP),(-STEP,STEP),(-STEP,-STEP)]
 openq=[(0.0,s)];cost={s:0.0};parent={s:None}
 while openq:
  _,u=heapq.heappop(openq)
  if u==g:break
  x,y,li=u
  for dx,dy in dirs:
   v=(x+dx,y+dy,li)
   if not(.7<=v[0]<=95.3 and .7<=v[1]<=59.3) or not safe_seg((x,y),(v[0],v[1]),data[li]):continue
   nc=cost[u]+math.hypot(dx,dy)
   if nc<cost.get(v,1e99):cost[v]=nc;parent[v]=u;heapq.heappush(openq,(nc+math.hypot(v[0]-g[0],v[1]-g[1]),v))
  other=1-li;v=(x,y,other)
  if safe_seg((x,y),(x,y),via_data[li]) and safe_seg((x,y),(x,y),via_data[other]):
   nc=cost[u]+2.0
   if nc<cost.get(v,1e99):cost[v]=nc;parent[v]=u;heapq.heappush(openq,(nc+math.hypot(x-g[0],y-g[1]),v))
 else:raise RuntimeError(f'no multilayer {net} route {start}->{goal}')
 path=[];u=g
 while u is not None:path.append(u);u=parent[u]
 path.reverse();path[-1]=(goal[0],goal[1],path[-1][2])
 gx,gy,li=path[0];dx,dy=gx-start[0],gy-start[1]
 prefix=[(start[0],start[1],li)]
 if abs(dx)>1e-9 and abs(dy)>1e-9:
  if abs(dy)>=abs(dx):mid=(start[0],start[1]+math.copysign(abs(dy)-abs(dx),dy),li)
  else:mid=(start[0]+math.copysign(abs(dx)-abs(dy),dx),start[1],li)
  if math.hypot(mid[0]-start[0],mid[1]-start[1])>1e-9:prefix.append(mid)
 path=prefix+path
 run=[path[0]]
 for state in path[1:]:
  if state[2]!=run[-1][2]:
   pts=[(p[0],p[1]) for p in run];add_track(net,compress(pts),layers[run[0][2]],width);add_via(net,(state[0],state[1]));run=[state]
  else:run.append(state)
 pts=[(p[0],p[1]) for p in run];add_track(net,compress(pts),layers[run[0][2]],width)

def compress(path):
 if len(path)<3:return path
 out=[path[0]]
 for i in range(1,len(path)-1):
  a,m,c=path[i-1],path[i],path[i+1]
  if (m[0]-a[0],m[1]-a[1])!=(c[0]-m[0],c[1]-m[1]):out.append(m)
 out.append(path[-1]);return out

add_track('+24V_RAW',[(32,56.2),(32,58.5),(50.96,58.5),(50.96,56.2)],pcbnew.F_Cu,1.2)
target=(58.5,27.0);route_multilayer((13.963,40.833),target,'+3V3',.4);add_via('+3V3',target)
add_track('+3V3',[target,(58.8386,27.3386),(58.8386,27.65)],pcbnew.F_Cu,.4)
# Continuous top GND pour closes the small ground islands left by the signal router.
for existing in b.Zones():
 if existing.GetNetname()=='GND':existing.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
z=pcbnew.ZONE(b);z.SetNet(b.FindNet('GND'));z.SetLayer(pcbnew.F_Cu);z.SetLocalClearance(pcbnew.FromMM(.25));z.SetMinThickness(pcbnew.FromMM(.25));z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS);z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
o=z.Outline();o.NewOutline()
for x,y in ((.5,.5),(95.5,.5),(95.5,59.5),(.5,59.5)):o.Append(pcbnew.VECTOR2I_MM(x,y))
b.Add(z)
# Preserve the front fiducials' isolated optical copper geometry.
for cx,cy in ((3,3),(92,58),(40,3)):
 k=pcbnew.ZONE(b);k.SetLayer(pcbnew.F_Cu);k.SetIsRuleArea(True);k.SetDoNotAllowCopperPour(True);k.SetDoNotAllowPads(False);k.SetDoNotAllowTracks(False);k.SetDoNotAllowVias(False);k.SetDoNotAllowFootprints(False)
 q=k.Outline();q.NewOutline()
 for x,y in ((cx-2,cy-2),(cx+2,cy-2),(cx+2,cy+2),(cx-2,cy+2)):q.Append(pcbnew.VECTOR2I_MM(x,y))
 b.Add(k)
b.BuildConnectivity();pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(P),b);print('RevC remaining connections added with obstacle-aware routes')
