"""Decode complete exports and inspect contract; save measured loudness/black events."""
import json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent
cfg=json.loads((R/'edit.json').read_text()); expected=sum(s['out']-s['in'] for s in cfg['segments'])
reports=[]
for path in sorted((R/'output').glob('sber_merch*.mp4')):
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)])); v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
 assert (v['width'],v['height'],v['avg_frame_rate'],v['pix_fmt'])==(1080,1920,'30/1','yuv420p')
 assert a['sample_rate']=='48000' and a['channels']==2
 assert abs(float(probe['format']['duration'])-expected)<.1
 result=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-vf','blackdetect=d=0.08:pix_th=0.03','-af','loudnorm=I=-15:TP=-1:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 log=result.stderr; stats=json.loads(log[log.rfind('{'):log.rfind('}')+1]); black=[l for l in log.splitlines() if 'black_start:' in l]
 reports.append({'file':path.name,'duration':probe['format']['duration'],'frames':v.get('nb_frames'),'audio_measurement':stats,'black_events':black,'complete_decode':'passed'})
(R/'output/validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2));print(json.dumps(reports,ensure_ascii=False,indent=2))
