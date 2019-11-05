import pyaudio
import wave
import numpy as np
import curses
from audiolazy import lazy_lpc
from scipy import signal

N=13#Para un filtro de orden 12
a = np.array([1])
b = np.zeros(N)
b[0] = 1
zi = signal.lfilter_zi(a, b) #Estados iniciales

buffer_count = 0# Cuenta de cuantas veces se llamo al callback
BUFFER_SIZE = 2048# Tamaño del ventaneo
freq = 110#frecuencia inicial

prevIn=np.array(np.zeros((int(BUFFER_SIZE/2)),))
prevOut=np.array(np.zeros((int(BUFFER_SIZE/2)),))

def wav2Float(dataIn): #Del formato del wav (buffer de bytes en codif int16) a array de floats
    dataOut = np.frombuffer(dataIn, dtype=np.int16)
    dataOut = [float(val) / pow(2, 15) for val in dataOut]
    return np.asarray(dataOut)

def float2wav(dataIn):
    dataOut = [val * pow(2, 15) for val in dataIn]
    dataOut = np.int16(dataOut)
    dataR = bytes(dataOut)
    return dataR

# Callback se llama cuando hay "frames_per_buffer" nuevos samples en el wav abierto, y toma tambien esa cantiad de
# muestras de audio del microfono.
def callback(in_data, frame_count, time_info, flag):
    global zi, buffer_count, BUFFER_SIZE, freq,prevIn,prevOut
    voice = wav2Float(in_data) #Se pasan a float los samples de la voz
    aM = np.asarray(lazy_lpc.lpc.autocor(voice, 12).numerator)# Se obtienen los coeficientes LPC de la voz

    duty = 0.5 # Duty de la onda cuadrada
    Av = 0.1# Amplitud
    glotalPulse = np.zeros((frame_count,))
    T = int(wf.getframerate() / freq)# Período
    # Se construye un tren de pulsos de frecuencia determinada
    for j in range(glotalPulse.shape[0]):
        # ex es la cantidad de muestras por encima de donde deberia comenzar la delta
        ex = ((j + BUFFER_SIZE * buffer_count) % T)
        if (ex / T) < duty:
            glotalPulse[j] = Av
    #glotalPulse = wav2Float(wf.readframes(frame_count)) #Si se quiere usar música como input

    input=np.multiply(np.concatenate((prevIn,glotalPulse)),np.hamming(int(BUFFER_SIZE)))

    out4Gain, zn = signal.lfilter(np.array([1]), aM, input, zi=zi) #Filtrado previo para aplicar control de ganancia
    gain=np.std(out4Gain)/np.std(input);
    out, zi = signal.lfilter(np.array([1/gain]), aM, input, zi=zi) #Filtrado final

    FinaulOut = prevOut + out[0:frame_count]
    prevIn = glotalPulse
    prevOut = out[frame_count:]
    buffer_count += 1

    return float2wav(FinaulOut), pyaudio.paContinue


wf = wave.open("GH3-SGB.wav", 'rb') # Archivo de música que va a leer
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                frames_per_buffer=int(BUFFER_SIZE/2),
                output=True,
                input=True,
                stream_callback=callback)
stdscr = curses.initscr()
k=0
d = {
    'a': 110,
    's': 123.5,
    'd': 130.8,
    'f': 146.8,
    'g': 164.8,
    'h': 174.6,
    'j': 196,
    'k': 220
}
while k != ord('q'):
    k = stdscr.getch()
    for i in d:
        if k == ord(i):
            freq = d[i]
stream.close()