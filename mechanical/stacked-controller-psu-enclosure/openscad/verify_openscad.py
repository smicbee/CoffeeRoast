#!/usr/bin/env python3
"""Verify CoffeeRoast stacked RevA.2 + LOP-200 enclosure exports."""
from __future__ import annotations
import hashlib, json, math, subprocess, zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'generated'
REPO=ROOT.parents[2]
BOARD=REPO/'KiCAD'/'CoffeeRoast-Control-RevA'/'CoffeeRoast-Control-RevA.kicad_pcb'
DATASHEET=REPO/'mechanical'/'psu-enclosure'/'lop-200'/'reference'/'LOP-200-SPEC.pdf'

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
 bbox={'x':max(xs)-min(xs),'y':max(ys)-min(ys),'z':max(zs)-min(zs),
       'xmin':min(xs),'ymin':min(ys),'zmin':min(zs)}
 return {'triangles':len(tris),'connected_components':len({find(i) for i in range(len(tris))}),
         'open_or_nonmanifold_edges':sum(v!=2 for v in edges.values()),
         'bbox_mm':{k:round(v,4) for k,v in bbox.items()}}

def valid_3mf(p:Path)->bool:
 if not p.is_file() or not zipfile.is_zipfile(p): return False
 with zipfile.ZipFile(p) as z: names=z.namelist()
 return '[Content_Types].xml' in names and any(n.lower().endswith('.model') for n in names)

def approx(a,b,t=.10): return math.isclose(a,b,abs_tol=t)

def main()->int:
 checks=[]
 def check(name,passed,evidence): checks.append({'name':name,'passed':bool(passed),'evidence':evidence})
 names=('lower_base','controller_deck','lid_print','lid_design','psu_proxy','pcb_proxy')
 meshes={n:read_stl(OUT/f'{n}.stl') for n in names}
 check('stl_meshes_closed_manifold',all(m['open_or_nonmanifold_edges']==0 for m in meshes.values()),meshes)
 check('print_parts_single_connected_component',all(meshes[n]['connected_components']==1 for n in ('lower_base','controller_deck','lid_print')),
       {n:meshes[n]['connected_components'] for n in ('lower_base','controller_deck','lid_print')})
 b=meshes['lower_base']['bbox_mm']; d=meshes['controller_deck']['bbox_mm']; l=meshes['lid_print']['bbox_mm']
 pp=meshes['psu_proxy']['bbox_mm']; cp=meshes['pcb_proxy']['bbox_mm']
 check('expected_part_envelopes',approx(b['x'],166.0) and approx(b['y'],106.0) and approx(b['z'],40.8)
       and approx(d['x'],166.0) and approx(d['y'],106.0) and approx(d['z'],34.0)
       and approx(l['x'],169.0) and approx(l['y'],109.0)
       and approx(pp['x'],101.6) and approx(pp['y'],50.8) and approx(pp['z'],31.4)
       and approx(cp['x'],160.025,0.2) and approx(cp['y'],100.0,0.2),
       {'lower_base_mm':b,'controller_deck_mm':d,'lid_print_mm':l,'psu_proxy_mm':pp,'pcb_proxy_mm':cp})
 archives={n:{'valid':valid_3mf(OUT/f'{n}.3mf'),'bytes':(OUT/f'{n}.3mf').stat().st_size}
           for n in ('lower_base','controller_deck','lid_print')}
 check('print_3mf_archives_valid',all(v['valid'] for v in archives.values()),archives)
 previews={n:(OUT/n).stat().st_size for n in ('preview_closed.png','preview_exploded.png','preview_usb.png','preview_ac.png')}
 check('previews_generated',all(v>10000 for v in previews.values()),previews)
 check('source_contracts_present',BOARD.is_file() and DATASHEET.is_file(),
       {'board':str(BOARD),'board_sha256':sha256(BOARD) if BOARD.is_file() else None,
        'datasheet':str(DATASHEET),'datasheet_sha256':sha256(DATASHEET) if DATASHEET.is_file() else None})
 contract={'controller_pcb_mm':[160.0,100.0,1.6],'psu_mm':[101.6,50.8,25.4],
           'psu_mounting_pattern_mm':[95.25,44.45],
           'closed_nominal_mm':[169.0,109.0,76.6],
           'separation':'2.4 mm solid printed deck; 8.2 mm secondary feedthrough requires closed rated bushing',
           'usb':'right-wall J5 cutout, 11.0 x 5.8 mm'}
 report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL',
         'scope':'digital geometry prototype; not an electrical-safety certification',
         'openscad_version':subprocess.check_output(['openscad','--version'],text=True,stderr=subprocess.STDOUT).strip(),
         'design':contract,
         'release_blockers':[
          'Use documented flame-retardant UL94-V-0 filament/process; ordinary PLA/PETG is not released.',
          'Install the exact Mean Well LOP-200-24 on conductive M3 pillars and bond every PE-marked point.',
          'Fit a certified AC cable gland and a closed rated bushing in the 24 V separator feedthrough.',
          'Qualified-person inspection: fuse/switch, wire ratings, strain relief, touch probe, creepage/clearance and PE continuity.',
          'Measure installed controller component heights, USB plug insertion and cable bend clearance.',
          'Run worst-case thermal testing; stacking blocks direct top convection and full 200 W is not assumed.'
         ],'checks':checks}
 (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 files={p.name:{'bytes':p.stat().st_size,'sha256':sha256(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
 (OUT/'manifest.json').write_text(json.dumps({'status':'PROTOTYPE_NOT_RELEASED','source':'CoffeeRoast_RevA2_LOP200_stacked.scad','files':files},indent=2)+'\n')
 print(json.dumps(report,indent=2)); return 0 if report['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
