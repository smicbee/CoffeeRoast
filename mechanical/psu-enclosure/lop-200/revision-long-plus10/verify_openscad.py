#!/usr/bin/env python3
"""Verify the single-LOP-200 enclosure exports with stdlib only."""
from __future__ import annotations
import hashlib, json, math, subprocess, zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'generated'
DATASHEET=ROOT.parent/'reference'/'LOP-200-SPEC.pdf'
EXPECTED_DATASHEET_SHA='7904561abeabf3d70eb4e2914bb1d2d8f691e56d64ff5c7c57db118b84ea23d3'

def sha256(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def read_stl(p:Path)->dict:
 verts=[]; tris=[]; cur=[]
 for raw in p.read_text(encoding='ascii',errors='strict').splitlines():
  line=raw.strip()
  if line.startswith('vertex '):
   _,x,y,z=line.split(); v=tuple(round(float(q),6) for q in (x,y,z)); verts.append(v); cur.append(v)
   if len(cur)==3: tris.append(tuple(cur)); cur=[]
 if cur or not tris: raise ValueError(f'Invalid/empty STL: {p}')
 edges=Counter(); edge_faces=defaultdict(list)
 for fi,t in enumerate(tris):
  for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
   e=tuple(sorted((a,b))); edges[e]+=1; edge_faces[e].append(fi)
 parent=list(range(len(tris)))
 def find(x):
  while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
  return x
 def union(a,b):
  a,b=find(a),find(b)
  if a!=b: parent[b]=a
 for faces in edge_faces.values():
  for f in faces[1:]: union(faces[0],f)
 xs,ys,zs=zip(*verts)
 bbox={'x':max(xs)-min(xs),'y':max(ys)-min(ys),'z':max(zs)-min(zs),'xmin':min(xs),'ymin':min(ys),'zmin':min(zs)}
 return {'triangles':len(tris),'connected_components':len({find(i) for i in range(len(tris))}),
         'open_or_nonmanifold_edges':sum(v!=2 for v in edges.values()),
         'bbox_mm':{k:round(v,4) for k,v in bbox.items()}}

def valid_3mf(p:Path)->bool:
 if not p.is_file() or not zipfile.is_zipfile(p): return False
 with zipfile.ZipFile(p) as z: names=z.namelist()
 return '[Content_Types].xml' in names and any(n.lower().endswith('.model') for n in names)

def approx(a,b,t=.08): return math.isclose(a,b,abs_tol=t)

def main()->int:
 checks=[]
 def check(name,passed,evidence): checks.append({'name':name,'passed':bool(passed),'evidence':evidence})
 meshes={n:read_stl(OUT/f'{n}.stl') for n in ('base','lid','psu_proxy')}
 check('stl_meshes_closed_manifold',all(m['open_or_nonmanifold_edges']==0 for m in meshes.values()),meshes)
 check('print_parts_single_connected_component',meshes['base']['connected_components']==1 and meshes['lid']['connected_components']==1,
       {n:meshes[n]['connected_components'] for n in ('base','lid')})
 base=meshes['base']['bbox_mm']; lid=meshes['lid']['bbox_mm']; proxy=meshes['psu_proxy']['bbox_mm']
 check('expected_envelopes',approx(base['x'],132.4) and approx(base['y'],71.6) and approx(base['z'],39.8)
       and approx(lid['x'],132.4) and approx(lid['y'],71.6) and approx(lid['z'],2.4)
       and approx(proxy['x'],101.6) and approx(proxy['y'],50.8) and approx(proxy['z'],31.4),
       {'base_mm':base,'lid_mm':lid,'psu_proxy_mm':proxy})
 archives={n:{'valid':valid_3mf(OUT/f'{n}.3mf'),'bytes':(OUT/f'{n}.3mf').stat().st_size} for n in ('base','lid')}
 check('print_3mf_archives_valid',all(v['valid'] for v in archives.values()),archives)
 previews={n:(OUT/n).stat().st_size for n in ('preview_closed.png','preview_open.png','preview_glands.png')}
 check('previews_generated',all(v>10000 for v in previews.values()),previews)
 check('manufacturer_datasheet_pinned',DATASHEET.is_file() and sha256(DATASHEET)==EXPECTED_DATASHEET_SHA,
       {'path':str(DATASHEET),'sha256':sha256(DATASHEET) if DATASHEET.is_file() else None})
 contract={'psu_mm':[101.6,50.8,25.4],'mounting_pattern_mm':[95.25,44.45],
           'mount_holes':'4 x 3.3 mm; M3 fixed conductive pillars, <=6 mm diameter',
           'shell_mm':[132.4,71.6,42.2],'cable_glands':'2 x 16.2 mm holes; select certified glands for actual cable OD'}
 report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL',
         'scope':'digital geometry prototype; not an electrical-safety certification',
         'openscad_version':subprocess.check_output(['openscad','--version'],text=True,stderr=subprocess.STDOUT).strip(),
         'design':contract,
         'release_blockers':[
          'Use a flame-retardant material with documented UL94 V-0 rating; ordinary PLA/PETG is not released.',
          'Install certified cable glands sized to the actual AC and 24 V cable diameters.',
          'Bond protective earth to every Mean Well PE-marked mounting point with conductive M3 hardware.',
          'Qualified-person inspection: fuse/switch, strain relief, touch probe, creepage/clearance, wiring and PE continuity.',
          'Thermal test in final orientation and load; full 200 W needs forced air per manufacturer data.',
          'Fit-test the physical LOP-200-24 and actual JST-VH harnesses before unattended use.'
         ],'checks':checks}
 (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 files={p.name:{'bytes':p.stat().st_size,'sha256':sha256(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
 (OUT/'manifest.json').write_text(json.dumps({'status':'PROTOTYPE_NOT_RELEASED','source':'CoffeeRoast_LOP200_single_enclosure.scad','files':files},indent=2)+'\n')
 print(json.dumps(report,indent=2)); return 0 if report['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
