import asyncio, base64, json, struct, subprocess, sys, os
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=sys.argv[1]
IDS=['r1','r2','r3','b1','b2','b3','m1','m2','m3','v1','v2','v3','x1']
def wav(path,b64):
    pcm=base64.b64decode(b64)
    with open(path,'wb') as f:
        f.write(b'RIFF'+struct.pack('<I',36+len(pcm))+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,1,41600,83200,2,16)+b'data'+struct.pack('<I',len(pcm))+pcm)
def mp3(name,b64,kbps):
    w=os.path.join(HERE,name+'.wav'); wav(w,b64)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',w,'-ac','1','-af','aresample=44100:resampler=soxr','-c:a','libmp3lame','-b:a',f'{kbps}k',os.path.join(OUT,name+'.mp3')],check=True)
    os.remove(w)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        await pg.goto('file://'+os.path.join(HERE,'render.html'))
        hits={}; peaks={}
        for i in IDS+['drone']:
            for h in ([True] if i=='drone' else [False,True]):
                r=await pg.evaluate(f"renderLoop('{i}',{str(h).lower()})")
                name=f"{i}_{'h' if h else 'n'}"; mp3(name,r['b64'],80)
                peaks[name]=round(r['peak'],3)
                if i!='drone': hits[name]=r['hits']
        for on in [True,False]:
            r=await pg.evaluate(f"renderSting({str(on).lower()})"); name='sting_'+('on' if on else 'off')
            mp3(name,r['b64'],80); peaks[name]=round(r['peak'],3)
        json.dump(hits,open(os.path.join(HERE,'hits.json'),'w'),separators=(',',':'))
        print(json.dumps(peaks))
        await b.close()
asyncio.run(main())
