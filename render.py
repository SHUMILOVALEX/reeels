#!/usr/bin/env python3
"""Reproducible non-destructive Reels edit. Python stdlib + ffmpeg only."""
import argparse, json, math, pathlib, subprocess, wave, array
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
def run(args):
    subprocess.run([str(a) for a in args],check=True)
def cue(style, duration):
    rate=48000; data=array.array('h'); bpm=[116,140,128][style]; beat=60/bpm
    melody=[[48,55,60,63,62,55,58,54],[60,64,67,72,69,65,62,67],[36,36,43,46,48,43,41,38]][style]
    for i in range(math.ceil(duration*rate)):
        t=i/rate; k=int(t/(beat/2)); phase=t%(beat/2); f=440*2**((melody[k%len(melody)]-69)/12)
        env=(1-math.exp(-phase*120))*math.exp(-phase*[18,12,9][style])
        v=(math.sin(2*math.pi*f*phase)+.25*math.sin(4*math.pi*f*phase))*env*.20
        p=t%beat
        if style==2: v+=.14*math.sin(2*math.pi*(70*p-35*p*p))*math.exp(-p*30)
        fade=min(1,t/.015,max(0,(duration-t)/.18)); sample=int(max(-.9,min(.9,v*fade))*32767)
        data.extend([sample,sample])
    dest=OUT/f'cue_{style+1}.wav'
    with wave.open(str(dest),'wb') as w: w.setparams((2,2,rate,0,'NONE','not compressed'));w.writeframes(data.tobytes())
    return dest
def render():
    cfg=json.loads((ROOT/'edit.json').read_text()); seg=cfg['segments']; duration=sum(s['out']-s['in'] for s in seg)
    filters=[]; inputs=[]
    for i,s in enumerate(seg):
        if not 0<=s['in']<s['out']: raise ValueError('Invalid source range')
        inputs+=['-ss',s['in'],'-t',s['out']-s['in'],'-i',ROOT/'assets'/s['source']]
        filters += [f'[{i}:v]setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,setsar=1,fps=30[v{i}]',f'[{i}:a]asetpts=PTS-STARTPTS,aresample=48000,apad,atrim=duration={s["out"]-s["in"]}[a{i}]']
    filters+=[''.join(f'[v{i}][a{i}]' for i in range(len(seg)))+f'concat=n={len(seg)}:v=1:a=1[v][raw]', '[raw]highpass=f=75,loudnorm=I=-16:TP=-1.5:LRA=11[a]']
    clean=OUT/'sber_merch_reels_clean.mp4'
    run(['ffmpeg','-y','-v','warning',*inputs,'-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-threads','4','-b:v','12M','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-movflags','+faststart',clean])
    for style,name in enumerate(['spy','chase','funk']):
        music=cue(style,duration-cfg['music_entry']); delay=round(cfg['music_entry']*1000)
        graph=f'[1:a]loudnorm=I=-20:TP=-3:LRA=7,adelay={delay}|{delay}[m];[0:a]volume=1[a];[a][m]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[mix]'
        target=OUT/f'sber_merch_reels_review_{name}.mp4'
        run(['ffmpeg','-y','-v','warning','-i',clean,'-i',music,'-filter_complex',graph,'-map','0:v','-map','[mix]','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-t',duration,'-movflags','+faststart',target])
        run(['ffmpeg','-y','-v','error','-ss',max(0,cfg['music_entry']-.6),'-i',target,'-t',duration-cfg['music_entry']+.6,'-vf','scale=540:960','-c:v','libx264','-preset','fast','-threads','2','-crf','22','-c:a','aac','-movflags','+faststart',OUT/f'preview_{name}.mp4'])
    timeline=[]; cursor=0
    for s in seg:
        length=s['out']-s['in']; timeline.append({**s,'timeline_in':round(cursor,6),'timeline_out':round(cursor+length,6),'speed':1}); cursor+=length
    (OUT/'timeline.json').write_text(json.dumps({'duration':duration,'music_entry':cfg['music_entry'],'edit':timeline},ensure_ascii=False,indent=2))
if __name__=='__main__': render()
