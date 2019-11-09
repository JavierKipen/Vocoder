import pyaudio
import wave
import numpy as np
import curses
from audiolazy import lazy_lpc
from scipy import signal

N = 13                          # Para un filtro de orden 12
a = np.array([1])
b = np.zeros(N)
b[0] = 1
zi = signal.lfilter_zi(a, b)    # Estados iniciales
flag = 0

buffer_count = 0                # Cuenta de cuantas veces se llamo al callback
BUFFER_SIZE = 1024              # Tamaño del ventaneo
freq = 110                      # Frecuencia inicial

# Para guardar la voz en el frame anterior
prev_in = np.array(np.zeros((int(BUFFER_SIZE/2)),))
# Para guardar la salida en el frame anterior
prev_out = np.array(np.zeros((int(BUFFER_SIZE/2)),))
# Para guardar los pulsos glotales en el frame anterior
glotal_pulse_prev = np.array(np.zeros((int(BUFFER_SIZE/2)),))


# Del formato del wav (buffer de bytes en codif int16) a array de floats
def wav_to_float(data_in):
    data_out = np.frombuffer(data_in, dtype=np.int16)
    data_out = [float(val) / pow(2, 15) for val in data_out]
    return np.asarray(data_out)


def float_to_wav(data_in):
    data_out = [val * pow(2, 15) for val in data_in]
    data_out = np.int16(data_out)
    data_ret = bytes(data_out)
    return data_ret


# Callback se llama cuando hay "frames_per_buffer" nuevos samples en el wav abierto, y toma tambien esa cantiad de
# muestras de audio del microfono.
def callback(in_data, frame_count, time_info, flag2):
    global zi, buffer_count, BUFFER_SIZE, freq, prev_in, prev_out, glotal_pulse_prev, flag
    voice = wav_to_float(in_data)      # Se pasan a float los samples de la voz
    # aM = np.asarray(lazy_lpc.lpc.autocor(voice, 12).numerator)      # Se obtienen los coeficientes LPC de la voz

    glotal_duty = 0.2                       # Duty de la onda cuadrada
    glotal_amplitude = 0.1                  # Amplitud
    glotal_pulse = np.zeros((frame_count,))
    glotal_period = int(16000 / freq)       # Período
    # Se construye un tren de pulsos de frecuencia determinada
    for j in range(glotal_pulse.shape[0]):
        # ex es la cantidad de muestras por encima de donde deberia comenzar la delta
        ex = ((j + (BUFFER_SIZE / 2) * buffer_count) % glotal_period)
        if (ex / glotal_period) < glotal_duty:
            glotal_pulse[j] = glotal_amplitude
    # glotalPulse = wav2Float(wf.readframes(frame_count)) #Si se quiere usar música como input

    voice_full = np.multiply(np.concatenate((prev_in, voice)), np.hamming(int(BUFFER_SIZE)))

    lpcs = np.asarray(lazy_lpc.lpc.autocor(voice_full, 12).numerator)

    glotal_pulse_full = np.concatenate((glotal_pulse_prev, glotal_pulse))

    # Filtrado previo para aplicar control de ganancia
    out_before_gain, zn = signal.lfilter(np.array([1]), lpcs, glotal_pulse_full, zi=zi)
    gain = np.std(out_before_gain)/np.std(voice_full)
    out, zi = signal.lfilter(np.array([1/gain]), lpcs, glotal_pulse_full, zi=zi)    # Filtrado final

    out = np.multiply(out, np.hamming(int(BUFFER_SIZE)))

    final_out = prev_out + out[0:frame_count]
    prev_in = voice
    prev_out = out[frame_count:]
    glotal_pulse_prev = glotal_pulse
    buffer_count += 1

    # final_out=voice
    return float_to_wav(final_out), pyaudio.paContinue


wf = wave.open("Jazz.wav", 'rb')    # Archivo de música que va a leer
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=16000,
                #rate=wf.getframerate(),
                frames_per_buffer=int(BUFFER_SIZE/2),
                output=True,
                input=True,
                stream_callback=callback)
stdscr = curses.initscr()
k=0
d = {
    'z': 1,
    's': 2,
    'x': 3,
    'd': 4,
    'c': 5,
    'v': 6,
    'g': 7,
    'b': 8,
    'h': 9,
    'n': 10,
    'j': 11,
    'm': 12,
}

while k != ord('q'):
    k = stdscr.getch()
    for i in d:
        if k == ord(i):
            freq = 261.626 * (2 ** ((d[i] - 1) / 12))
    if k == ord('o'):
        flag = 1
    else:
        flag = 0
stream.close()
