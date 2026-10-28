"""Burn supplied dialogue captions; optionally mix a user-provided music excerpt.
Timing is estimated, not certified alignment. Never downloads commercial audio.
"""
import argparse,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent; O=R/'output'
def run(args):subprocess.run([str(a) for a in args],check=True)
def stamp(t,ass=False):
 ms=round(t*1000); h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f'{h}:{m:02}:{s:02}.{ms//10:02}' if ass else f'{h:02}:{m:02}:{s:02},{ms:03}'
def main():
 p=argparse.ArgumentParser();p.add_argument('--music',type=pathlib.Path);p.add_argument('--music-start',type=float);a=p.parse_args()
 if a.music and (a.music_start is None or a.music_start<0):p.error('--music requires non-negative --music-start')
 c=json.loads((R/'captions.json').read_text())['cues'];cfg=json.loads((R/'edit.json').read_text());duration=sum(x['out']-x['in'] for x in cfg['segments'])
 srt='\n\n'.join(f'{i}\n{stamp(s)} --> {stamp(e)}\n{text}' for i,(s,e,text) in enumerate(c,1))+'\n';(O/'sber_merch_reels.srt').write_text(srt)
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,52,&H00FFFFFF,&H00FFFFFF,&H00141414,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,90,180,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 for s,e,text in c:
  escaped=text.replace('\n',r'\N');header+=f'Dialogue: 0,{stamp(s,True)},{stamp(e,True)},Default,,0,0,0,,{escaped}\n'
 (O/'captions.ass').write_text(header)
 video=O/'sber_merch_reels_captioned_review.mp4'
 run(['ffmpeg','-y','-v','warning','-i',O/'sber_merch_reels_clean.mp4','-vf',f'ass={O}/captions.ass','-c:v','libx264','-threads','4','-preset','fast','-b:v','12M','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',video])
 if a.music:
  delay=round(cfg['music_entry']*1000);length=duration-cfg['music_entry'];fade=max(0,length-.25)
  graph=f'[1:a]atrim=duration={length},asetpts=PTS-STARTPTS,loudnorm=I=-18:TP=-2:LRA=7,afade=t=out:st={fade}:d=0.25,adelay={delay}|{delay}[m];[0:a]volume=if(lt(t\\,{cfg["music_entry"]})\\,1\\,0.18):eval=frame[d];[d][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=7[mix]'
  run(['ffmpeg','-y','-v','warning','-i',video,'-ss',a.music_start,'-i',a.music.resolve(),'-filter_complex',graph,'-map','0:v','-map','[mix]','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-t',duration,'-movflags','+faststart',O/'sber_merch_reels_music_review.mp4'])
if __name__=='__main__':main()
