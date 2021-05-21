#!/usr/bin/python3


# all imports are here
from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt
import ntpath
import os

# class used to extract the main notes out of the melody
# instance variables:
#   file: string containing the audio file's name without extension
#   voices: int containing the number of voices.
#   rate: data rate of the audio file
#   data: the raw data of the audio file
#   graph_path: the path storing the graphs generated
#   lowerFreq: lowest frequency (131Hz, C3)
#   upperFreq: three octaves above lowerFreq (C6)
# TODO: in the case of multiple voices, how do we synchronise the motors
class MainNotesExtractor():
  def __init__(self, path_to_file, voices):
    self.lowerFreq = 131
    self.upperFreq = self.lowerFreq * 8 # three octaves
    #self.upperFreq = 300+300
    file_name = MainNotesExtractor.path_leaf(path_to_file)
    self.file = os.path.splitext(file_name)[0]
    self.voices = voices
    self.rate, self.data = wavfile.read(path_to_file)
    if len(self.data.shape) == 2:
      self.data = self.data[:,0]
    # make a directory to save the graphs in
    os.makedirs(os.path.abspath("./graphs/{}-graphs".format(self.file)), exist_ok= True)
    self.graph_path = os.path.abspath("./graphs/{}-graphs/{}.png")
    
  # courtesy of stackoverflow
  def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

  # save whatever plot we have on plt at self.graph_path with name.png
  def save_plot_with_name(self, name):
    plt.savefig(self.graph_path.format(self.file, name))

  # returns the top frequency at each time from the spectrogram and their magnitude
  def get_top_freq_per_seg(self):
    spectrum, freqs, t, im = plt.specgram(self.data, Fs = self.rate, NFFT = 3000)

    # plot the spectrogram
    plt.colorbar()
    plt.ylim([self.lowerFreq, self.upperFreq])
    plt.title("Spectrogram of Audio File Within Frequencies of Interest")
    plt.xlabel('Time(s)')
    plt.ylabel('Frequency (Hz)')
    self.save_plot_with_name("spectrogram")
    #plt.show()

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
      max_freq.append(trimmed_freqs[max_ind])
      max_magn.append(max_val)

    # plot the max frequency graph over time
    max_freq = np.array(max_freq)
    plt.scatter(t, max_freq)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title("Most Prominent Frequency over Time")
    plt.ylim([0, self.upperFreq])
    self.save_plot_with_name("raw_freq_over_time")
    #plt.show()
    
    # plot the magnitude of the max frequency graph
    max_magn = np.array(max_magn)
    plt.xlabel("Time (s)")
    plt.ylabel("Magnitude")
    plt.title("Magnitude of Most Prominent Frequency over Time")
    plt.yscale('log')
#    plt.ylim(bottom=10**-3)
    plt.scatter(t, np.ma.masked_equal(max_magn, 0)) # mask all 0 magnitude values
    self.save_plot_with_name("raw_magn_over_time")
    #plt.show()
    return max_freq, max_magn, t

  # takes in the raw freqs and magn and then clean them (get rid of noise)
  # and maybe do some clustering (group similar notes together)
  # time is passed in for plotting
  def clean_frequencies(self, freqs, magn, time):
    # get the magnitude of the most prominent signal
    # get the mean log_10 magnitude for all non-zero magnitudes
    mean_log_10_magnitude = np.mean(np.log10(magn[magn != 0]))
    print(mean_log_10_magnitude)
    # magic cutoff threshold
    # all frequency whose log_10 fft magnitude < mean_log_10_magnitude + magic_cutoff is omitted
    magic_cutoff = -1
    filtered_freqs = np.array([freqs[ind] if val != 0 and np.log10(val)-mean_log_10_magnitude > magic_cutoff else 0 for ind, val in np.ndenumerate(magn)])
    filtered_magn = np.array([magn[ind] if val > 0 else 0 for ind, val in np.ndenumerate(filtered_freqs)])
    # plot the filtered frequencies
    plt.scatter(time, filtered_freqs)
    plt.title("Most Prominent Frequency over time Filtered with Avg Log Magnitude")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.ylim([0, self.upperFreq])
    self.save_plot_with_name("freq_over_time_avg_magn_filtered")
    #plt.show()
    # plot the magnitude of the filtered frequencies
    plt.scatter(time, np.ma.masked_equal(filtered_magn, 0))
    plt.title("Magnitude of Prominent Frequency over time Filtered with Avg Log Magnitude")
    plt.xlabel("Time (s)")
    plt.ylabel("Magnitude")
    plt.yscale('log')
    #plt.ylim(bottom= 10**-3)
    self.save_plot_with_name("magn_over_time_avg_magn_filtered")
    #plt.show()
    return filtered_freqs, filtered_magn


  # output the audio file in the following format:
  # [(note_freq, duration_in_ms)]
  def extract(self):
    # generate and extract data from spectrogram
    freqs, magn, time = self.get_top_freq_per_seg()
    filtered_freqs, filtered_magn = self.clean_frequencies(freqs, magn, time)
    #self.movingAverage(filtered_freqs)
    return filtered_freqs, filtered_magn, time
    # get rid of the noise (frequencies with small magnitude in fft)


class FrequencyToCode():
  def __init__(self, freqs, time):
    self.freqs = freqs
    self.time = time

  def getCode(self):
    template = "#ifndef DATA_H\n#define DATA_H\nint FREQUENCIES[]=^{}$;\n"
    template += "float DURATION[]=^{}$;\nint LENGTH={};\n#endif\n"

    frequencies = str([float(i) for i in self.freqs])[1:-1]
    duration = str([int(i) for i in self.time])[1:-1]
    duration = "0"

    if(len(frequencies) > 8000):
      frequencies = frequencies[0:8000]

    code = template.format(frequencies, duration, len(frequencies))
    code = code.replace('^', '{').replace('$','}')
    return code

  def writeCode(self):
    f = open('musicplayer/data.h', 'w+')
    f.write(self.getCode())
    f.close()

######################################################
path = os.path.abspath("./audio/test4.wav")
extractor = MainNotesExtractor(path, 1)
freqs, magn, time = extractor.extract()
encoder = FrequencyToCode(freqs, time)
encoder.writeCode()

