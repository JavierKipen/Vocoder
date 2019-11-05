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

BUFFER_SIZE = 512# Tamaño del ventaneo

freq = 100#frecuencia inicial

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
    global zi, buffer_count, BUFFER_SIZE, freq
    voice = wav2Float(in_data) #Se pasan a float los samples de la voz
    aM = np.asarray(lazy_lpc.lpc.autocor(voice, 12).numerator)# Se obtienen los coeficientes LPC de la voz

    duty = 0.5 # Duty de la onda cuadrada
    Av = 0.1# Amplitud
    zeros = np.zeros((BUFFER_SIZE,))
    T = int(wf.getframerate() / freq)# Período
    # Se construye un tren de pulsos de frecuencia determinada
    for j in range(zeros.shape[0]):
        # ex es la cantidad de muestras por encima de donde deberia comenzar la delta
        ex = ((j + BUFFER_SIZE * buffer_count) % T)
        if (ex / T) < duty:
            zeros[j] = Av


    outPrev, zn = signal.lfilter(np.array([1]), aM, zeros, zi=zi) #Filtrado previo para aplicar control de ganancia
    gain=np.std(outPrev)/np.std(zeros);
    out, zi = signal.lfilter(np.array([1/gain]), aM, zeros, zi=zi) #Filtrado final

    buffer_count += 1

    return float2wav(out), pyaudio.paContinue


wf = wave.open("GH3-SGB.wav", 'rb') # Archivo de música que va a leer
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                frames_per_buffer=BUFFER_SIZE,
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