#!/usr/bin/env python3
import argparse, json, math, os, re, tempfile, time, uuid
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_BODY = 1_000_000
MAX_SAMPLES = 2400
ALLOWED_ORIGIN = 'https://coffeeroast.michaelbeetz.de'
RATE_LIMIT = 12
RATE_WINDOW = 3600
requests_by_ip = defaultdict(deque)

def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def validate(payload):
    if not isinstance(payload, dict): raise ValueError('JSON-Objekt erwartet')
    samples = payload.get('samples')
    if not isinstance(samples, list) or not (2 <= len(samples) <= MAX_SAMPLES): raise ValueError('2 bis 2400 Messpunkte erforderlich')
    clean = []
    last_time = -1
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict): raise ValueError(f'Messpunkt {index} ist ungültig')
        row = {}
        for key in ('time','temperature','target','ror','heater','fan'):
            value = sample.get(key)
            if value is None and key == 'ror': row[key] = None; continue
            if not finite(value): raise ValueError(f'{key} in Messpunkt {index} ist ungültig')
            row[key] = round(float(value), 4)
        if row['time'] < last_time or row['time'] < 0 or row['time'] > 7200: raise ValueError('Zeitachse ist ungültig')
        if not (-20 <= row['temperature'] <= 400 and -20 <= row['target'] <= 400): raise ValueError('Temperatur außerhalb des zulässigen Bereichs')
        if not (0 <= row['heater'] <= 255 and 0 <= row['fan'] <= 255): raise ValueError('PWM außerhalb des zulässigen Bereichs')
        last_time = row['time']
        row['phase'] = str(sample.get('phase',''))[:32]
        row['state'] = str(sample.get('state',''))[:32]
        clean.append(row)
    recipe = payload.get('recipe') if isinstance(payload.get('recipe'), dict) else {}
    metadata = {
        'recipe': {'name': str(recipe.get('name','Unbekannt'))[:120], 'fileName': str(recipe.get('fileName',''))[:160]},
        'note': str(payload.get('note',''))[:1000],
        'firmware': str(payload.get('firmware',''))[:80],
        'protocol': str(payload.get('protocol',''))[:20],
        'hardware': str(payload.get('hardware',''))[:120],
        'clientVersion': str(payload.get('clientVersion','CoffeeRoast V2'))[:80],
        'uploadedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    return metadata, clean

def analyse(samples):
    temps = [s['temperature'] for s in samples]
    errors = [s['temperature'] - s['target'] for s in samples if s['target'] > 0]
    heaters = [s['heater'] for s in samples]
    return {
        'sampleCount': len(samples), 'durationSeconds': samples[-1]['time'],
        'minTemperature': round(min(temps),2), 'maxTemperature': round(max(temps),2),
        'targetRmse': round(math.sqrt(sum(e*e for e in errors)/len(errors)),2) if errors else None,
        'maxAbsoluteTargetError': round(max(map(abs,errors)),2) if errors else None,
        'averageHeaterPwm': round(sum(heaters)/len(heaters),2),
        'states': sorted(set(s['state'] for s in samples if s['state'])),
    }

class Handler(BaseHTTPRequestHandler):
    server_version = 'CoffeeRoastUpload/1.0'
    def json_response(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, separators=(',',':')).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        if self.path != '/api/roasts': return self.json_response(404, {'error':'Nicht gefunden'})
        origin = self.headers.get('Origin','')
        if origin and origin != ALLOWED_ORIGIN: return self.json_response(403, {'error':'Origin nicht erlaubt'})
        ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
        now=time.time(); bucket=requests_by_ip[ip]
        while bucket and bucket[0] < now-RATE_WINDOW: bucket.popleft()
        if len(bucket) >= RATE_LIMIT: return self.json_response(429, {'error':'Zu viele Uploads; bitte später erneut versuchen'})
        try: length=int(self.headers.get('Content-Length','0'))
        except ValueError: length=0
        if length <= 0 or length > MAX_BODY: return self.json_response(413, {'error':'Upload muss zwischen 1 Byte und 1 MB groß sein'})
        try:
            payload=json.loads(self.rfile.read(length)); metadata,samples=validate(payload)
            roast_id='CR-'+time.strftime('%Y%m%d',time.gmtime())+'-'+uuid.uuid4().hex[:12].upper()
            record={'id':roast_id,**metadata,'analysis':analyse(samples),'samples':samples}
            target=self.server.data_dir/(roast_id+'.json')
            fd,tmp=tempfile.mkstemp(prefix='.upload-',dir=self.server.data_dir)
            with os.fdopen(fd,'w',encoding='utf-8') as out: json.dump(record,out,ensure_ascii=False,separators=(',',':')); out.flush(); os.fsync(out.fileno())
            os.chmod(tmp,0o600); os.replace(tmp,target); bucket.append(now)
            self.json_response(201, {'id':roast_id,'analysis':record['analysis']})
        except (ValueError,json.JSONDecodeError) as error: self.json_response(400, {'error':str(error)})
        except Exception: self.json_response(500, {'error':'Upload konnte nicht gespeichert werden'})
    def do_GET(self): self.json_response(405, {'error':'Nur Uploads sind öffentlich erlaubt'})
    def log_message(self, fmt, *args): print('%s %s' % (self.address_string(),fmt%args),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8097);p.add_argument('--data-dir',default='/var/lib/coffeeroast-uploads');a=p.parse_args()
    data=Path(a.data_dir);data.mkdir(parents=True,exist_ok=True);server=ThreadingHTTPServer((a.host,a.port),Handler);server.data_dir=data;server.serve_forever()
if __name__=='__main__': main()
