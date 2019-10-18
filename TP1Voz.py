import pyaudio
import wave
import numpy as np
from scipy import signal
import time
from audiolazy import lazy_lpc
import matplotlib.pyplot as plt

N=13
a = np.array([1])
b = np.zeros(N)
b[0] = 1
ziSignalA = signal.lfilter_zi(b, a)
ziSignalB = signal.lfilter_zi(a, b)
ncalls=0

def wav2Float(dataIn): #Del formato del wav (buffer de bytes en codif int16) a array de floats
    dataOut = np.frombuffer(dataIn, dtype=np.int16)
    dataOut = [float(val) / pow(2, 15) for val in dataOut]
    return np.asarray(dataOut)

def float2wav(dataIn):
    dataOut = [val * pow(2, 15) for val in dataIn]
    dataOut = np.int16(dataOut)
    dataR = bytes(dataOut)
    return dataR

def callback(in_data, frame_count, time_info, flag): #Función que se llama cuando hay (framerate) samples nuevos de inputs
    ##Obtiene en array de floats la música del .wav y el mic.
    global ziSignalA, ziSignalB
    global ncalls
    retVal = pyaudio.paContinue
    signalA = wav2Float(wf.readframes(frame_count))
    signalB = wav2Float(in_data)
    ##procesamiento
    ncalls=ncalls+1

    #aMSignalA=np.asarray(lazy_lpc.lpc.autocor(signalA, 12).numerator)
    aMSignalB=np.asarray(lazy_lpc.lpc.autocor(signalB, 12).numerator)

    #eSignalA, ziSignalA = signal.lfilter(aMSignalA, np.array([1]), signalA, zi=ziSignalA)
    out, ziSignalB = signal.lfilter(np.array([1]), aMSignalB, signalA, zi=ziSignalB)
    out *= 0.01

    # out = music
    # if (ncalls>80): ## Luego de 2 segundos para
    #    plt.plot(music)
    #    plt.show
    #    retVal=pyaudio.paAbort
    ##Envía output
    return float2wav(out), retVal


wf = wave.open("GH3-SGB.wav", 'rb') ##Archivo de música que va a leer
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                frames_per_buffer=512,
                output=True,
                input=True,
                stream_callback=callback)
while stream.is_active():
    time.sleep(0.1)
stream.close()