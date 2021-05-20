#!/usr/bin/python3

# class used to extract the main notes out of the melody
# instance variables:
#   file: string containing the path to the audio file being compressed
#   voices: int containing the number of voices.
#   rate: data rate of the audio file
#   data: the raw data of the audio file
# TODO: in the case of multiple voices, how do we synchronise the motors

# all imports are here
from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt

class MainNotesExtractor():
  def __init__(self, path_to_file, voices):
    self.lowerFreq = 300
    self.upperFreq = self.lowerFreq * 8 # three octaves
    #self.upperFreq = 300+300
    self.file = path_to_file
    self.voices = voices
    self.rate, self.data = wavfile.read(self.file)
    if len(self.data.shape) == 2:
      self.data = self.data[:,0]

  # returns the top frequency at each time from the spectrogram and their magnitude
  def get_top_freq_per_seg(self):
    spectrum, freqs, t, im = plt.specgram(self.data, Fs = self.rate, NFFT = 4096)
    # plot the spectrogram

    '''
    plt.colorbar()
    plt.ylim([self.lowerFreq, self.upperFreq])
    plt.title("Spectrogram of Audio File Within Frequencies of Interest")
    plt.xlabel('Time(s)')
    plt.ylabel('Frequency (Hz)')
    plt.show()
    '''

    # find the frequency limits
    ind_boundary = (None, None)
    for ind, val in enumerate(freqs):
      if ind_boundary[0] == None and val > self.lowerFreq:
        ind_boundary = (ind, None)
      if ind_boundary[1] == None and val > self.upperFreq:
        ind_boundary = (ind_boundary[0], ind-1)

    # get the max frequency at each segment and their magnitudes
    trimmed_spectrum = spectrum[ind_boundary[0]:ind_boundary[1], :]
    trimmed_freqs = freqs[ind_boundary[0]:ind_boundary[1]]
    max_freq = []
    max_magn = []
    for i in range(len(t)):
      seg = trimmed_spectrum[:,i]
      max_ind = np.argmax(seg)
      max_val = seg[max_ind]

      if(max_val < 300000):
        max_freq.append(0)
        max_magn.append(0)
        continue

      max_freq.append(trimmed_freqs[max_ind])
      max_magn.append(max_val)

    # plot the max frequency graph over time
    max_freq = np.array(max_freq)
    '''
    plt.scatter(t, max_freq)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title("Most Prominent Frequency over Time")
    plt.show()
    '''
    # plot the magnitude of the max frequency graph
    max_magn = np.array(max_magn)
    '''
    plt.xlabel("Time (s)")
    plt.ylabel("Magnitude")
    plt.title("Magnitude of Most Prominent Frequency over Time")
    plt.yscale('log')
    plt.scatter(t, max_magn)
    plt.show()
    '''
    return max_freq, max_magn, t

  def clean_frequencies(freqs, magn):
    # get the magnitude of the most prominent signal
    pass

  # output the audio file in the following format:
  # [(note_freq, duration_in_ms)]
  def extract(self):
    # generate and extract data from spectrogram
    freqs, magn, time = self.get_top_freq_per_seg()
    return freqs, magn, time
    # get rid of the noise (frequencies with small magnitude in fft)


class FrequencyToCode():
  def __init__(self, freqs, time):
    self.freqs = freqs
    self.time = time

  def getCode(self):
    template = "#ifndef DATA_H\n#define DATA_H\nint FREQUENCIES[]=^{}$;\n"
    template += "int DURATION[]=^{}$;\n#endif\n"

    frequencies = str([int(i) for i in self.freqs])[1:-1]
    duration = str([int(i) for i in self.time])[1:-1]

    code = template.format(frequencies, duration)
    code = code.replace('^', '{').replace('$','}')
    return code

  def writeCode(self):
    f = open('musicplayer/data.h', 'w+')
    f.write(self.getCode())
    f.close()

######################################################
path = "./audio/test5.wav"
extractor = MainNotesExtractor(path, 1)
freqs, magn, time = extractor.extract()
encoder = FrequencyToCode(freqs, time)
encoder.writeCode();

