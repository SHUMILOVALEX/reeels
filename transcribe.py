import wave,json,pathlib
import numpy as np
import sherpa_onnx
root=pathlib.Path(__file__).resolve().parent
p=root/'assets/sherpa-onnx-whisper-small'
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=str(p/'small-encoder.int8.onnx'),decoder=str(p/'small-decoder.int8.onnx'),tokens=str(p/'small-tokens.txt'),language='ru',num_threads=4,enable_segment_timestamps=True)
w=wave.open(str(root/'output/dialogue.wav'));x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
results=[]
for start,end in [(0,7),(6.5,12),(11.5,17.615)]:
 s=r.create_stream();s.accept_waveform(16000,x[int(start*16000):int(end*16000)]);r.decode_stream(s)
 result=json.loads(str(s.result));result['source_start']=start;result['source_end']=end;results.append(result);print(result,flush=True)
(root/'output/transcript-asr.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
