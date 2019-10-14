import pyaudio
import wave
import numpy as np
from scipy import signal
import time
from audiolazy import lazy_lpc

N=13
b = np.array([1]);
a = np.ones(N)/N;
zi = signal.lfilter_zi(b, a)


def wav2Float(dataIn): #Del formato del wav (buffer de bytes en codif int16) a array de floats
    dataOut = np.frombuffer(dataIn, dtype=np.int16)
    dataOut = [float(val) / pow(2, 15) for val in dataOut]
    return np.asarray(dataOut)

def float2wav(dataIn):
    dataOut = [val * pow(2, 15) for val in dataIn];
    dataOut = np.int16(dataOut);
    dataR = bytes(dataOut)
    return dataR

def callback(in_data, frame_count, time_info, flag): #Función que se llama cuando hay (framerate) samples nuevos de inputs
    ##Obtiene en array de floats la música del .wav y el mic.
    global zi
    music = wav2Float(wf.readframes(frame_count));
    voice = wav2Float(in_data);
    ##procesamiento
    coefs=lazy_lpc.lpc(voice,12);
    a= np.asarray(coefs.numlist)
    out,zi = signal.lfilter(np.array([1]),a, music, zi=zi )
    ##Envía output
    return float2wav(out), pyaudio.paContinue



wf = wave.open("GH3-SGB.wav", 'rb') ##Archivo de música que va a leer
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),channels=wf.getnchannels(),rate=wf.getframerate(), output=True, input=True,stream_callback=callback)
while stream.is_active():
    time.sleep(0.1)
stream.close()
p.terminate()