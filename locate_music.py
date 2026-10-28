"""Locate requested phrase using local ASR; estimates need listening review."""
import wave,json,pathlib,argparse
import numpy as np,sherpa_onnx
args=argparse.ArgumentParser();args.add_argument('--start',type=int,default=0);args.add_argument('--end',type=int,default=177);args.add_argument('--chunk',type=int,default=20);args.add_argument('--result',default='song-asr.json');opt=args.parse_args()
r=pathlib.Path(__file__).resolve().parent;p=r/'assets/sherpa-onnx-whisper-small'
a=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=str(p/'small-encoder.int8.onnx'),decoder=str(p/'small-decoder.int8.onnx'),tokens=str(p/'small-tokens.txt'),language='ru',num_threads=4,enable_segment_timestamps=True)
w=wave.open(str(r/'output/song.wav'));x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768;results=[]
for start in range(opt.start,min(opt.end,int(len(x)/16000)),opt.chunk):
 s=a.create_stream();s.accept_waveform(16000,x[start*16000:min(start+opt.chunk,opt.end)*16000]);a.decode_stream(s);d=json.loads(str(s.result));d['source_start']=start;results.append(d);print(json.dumps(d,ensure_ascii=False),flush=True)
 (r/'output'/opt.result).write_text(json.dumps(results,ensure_ascii=False,indent=2))
