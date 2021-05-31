#!/usr/bin/python3

'''
Usage: convert_code.py [options]

Options:
  -h, --help            show this help message and exit
  -p, --plot            create plots under /graphs
  -f AUDIOFILE, --file=AUDIOFILE
                        path to wav file
'''

# all imports are here
from scipy.io import wavfile
from optparse import OptionParser
import numpy as np
import matplotlib.pyplot as plt
import ntpath
import os

# class used to extract the main notes out of the melody
# instance variables:
#   file: string containing the audio file's name without extension
#   voices: int containing the number of voices. TODO: incomplete
#   rate: data rate of the audio file
#   data: the raw data of the audio file
#   graph_path: the path storing the graphs generated
#   lowerFreq: lowest frequency (131Hz, C3)
#   upperFreq: three octaves above lowerFreq (C6)
#   plot: whether we are generating the graphs for the music file
# TODO: in the case of multiple voices, how do we synchronise the motors
class MainNotesExtractor():
  def __init__(self, path_to_file, voices, generate_plot):
    self.lowerFreq = 131
    self.upperFreq = self.lowerFreq * 8 # three octaves
    #self.upperFreq = 300+300
    file_name = MainNotesExtractor.path_leaf(path_to_file)
    self.file = os.path.splitext(file_name)[0]
    self.voices = voices
    self.rate, self.data = wavfile.read(path_to_file)
    self.plot = generate_plot
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
    if(self.plot):
      plt.colorbar()
      plt.ylim([self.lowerFreq, self.upperFreq])
      plt.title("Spectrogram of Audio File Within Frequencies of Interest")
      plt.xlabel('Time(s)')
      plt.ylabel('Frequency (Hz)')
      self.save_plot_with_name("spectrogram")
      plt.clf()

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

    if(self.plot):
      plt.scatter(t, max_freq)
      plt.xlabel("Time (s)")
      plt.ylabel("Frequency (Hz)")
      plt.title("Most Prominent Frequency over Time")
      plt.ylim([0, self.upperFreq])
      self.save_plot_with_name("raw_freq_over_time")
      plt.clf()
      #plt.show()
    
    # plot the magnitude of the max frequency graph
    max_magn = np.array(max_magn)

    if(self.plot):
      plt.xlabel("Time (s)")
      plt.ylabel("Magnitude")
      plt.title("Magnitude of Most Prominent Frequency over Time")
      plt.yscale('log')
      plt.scatter(t, np.ma.masked_equal(max_magn, 0)) # mask all 0 magnitude values
      self.save_plot_with_name("raw_magn_over_time")
      plt.clf()
      #plt.show()
    return max_freq, max_magn, t

  # takes in the raw freqs and magn and then clean them (get rid of noise)
  # and maybe do some clustering (group similar notes together)
  # time is passed in for plotting
  def clean_frequencies(self, freqs, magn, time):
    # get the magnitude of the most prominent signal
    # get the mean log_10 magnitude for all non-zero magnitudes
    mean_log_10_magnitude = np.mean(np.log10(magn[magn != 0]))
    #print(mean_log_10_magnitude)
    # magic cutoff threshold
    # all frequency whose log_10 fft magnitude < mean_log_10_magnitude + magic_cutoff is omitted
    magic_cutoff = -1
    filtered_freqs = np.array([freqs[ind] if val != 0 and np.log10(val)-mean_log_10_magnitude > magic_cutoff else 0 for ind, val in np.ndenumerate(magn)])
    filtered_magn = np.array([magn[ind] if val > 0 else 0 for ind, val in np.ndenumerate(filtered_freqs)])

    if(self.plot):
      # plot the filtered frequencies
      plt.scatter(time, filtered_freqs)
      plt.title("Most Prominent Frequency over time Filtered with Avg Log Magnitude")
      plt.xlabel("Time (s)")
      plt.ylabel("Frequency (Hz)")
      plt.ylim([0, self.upperFreq])
      self.save_plot_with_name("freq_over_time_avg_magn_filtered")
      plt.clf()
      #plt.show()
      # plot the magnitude of the filtered frequencies
      plt.scatter(time, np.ma.masked_equal(filtered_magn, 0))
      plt.title("Magnitude of Prominent Frequency over time Filtered with Avg Log Magnitude")
      plt.xlabel("Time (s)")
      plt.ylabel("Magnitude")
      plt.yscale('log')
      #plt.ylim(bottom= 10**-3)
      self.save_plot_with_name("magn_over_time_avg_magn_filtered")
      plt.clf()
      #plt.show()

    # try to do some clustering
    # go through the frequency lists and group them together
    prev_freq = None
    freq_groups = [] # will hold tuples in the form of (number_of_recurrence, frequency)
    counter = None
    for ind, val in enumerate(filtered_freqs):
      if prev_freq == None and counter == None: #first run
        prev_freq = val
        counter = 1
        continue
      if val != prev_freq:
        freq_groups.append((counter, prev_freq))
        prev_freq = val
        counter = 1
      else:
        counter += 1
    if prev_freq != freq_groups[-1][1]:
      freq_groups.append((counter, prev_freq))

    # go through the groups, if there are outliers that last too short, group them to nearby notes, or zero them
    half_note_ratio = 1.05946309436
    magic_clustering_cutoff = 2
    freq_clusters = [] # same format as freq_groups
    for ind, val in enumerate(freq_groups):
      recurrence, freq = val
      if recurrence <= magic_clustering_cutoff:
        left_neighbor_freq = freq_groups[ind-1][1]
        right_neighbor_freq = freq_groups[ind+1][1]
        left_ratio = None if left_neighbor_freq == 0 or ind == 0 or freq == 0 else abs(left_neighbor_freq-freq)/min(left_neighbor_freq, freq)
        right_ratio = None if right_neighbor_freq == 0 or ind == len(freq_groups)-1 or freq == 0 else abs(right_neighbor_freq-freq)/min(right_neighbor_freq, freq)

        # if there's no note to group with on the right nor on the left, we zero this note
        if (right_ratio == None or right_ratio > half_note_ratio) and (left_ratio == None or left_ratio > half_note_ratio):
          freq_clusters.append((recurrence, 0))
        else:
          if left_ratio == None: # if the left note doesn't work, we group it with the right note
            freq_clusters.append((recurrence, right_neighbor_freq))
          elif right_ratio == None: #if the right_note doesn't work, we group it with the left one
            freq_clusters.append((recurrence, left_neighbor_freq))
          else: #if both of left and right ratio are defined, we group it with the closer one
            freq_clusters.append((recurrence, right_neighbor_freq if right_ratio < left_ratio else left_neighbor_freq))
      else:
        freq_clusters.append(val)
    
    if(self.plot):
      # generate the full frequency list again from the cluster
      plot_freq_list = []
      for recurrence, freq in freq_clusters:
        for i in range(recurrence):
          plot_freq_list.append(freq)
      plot_freq_list = np.array(plot_freq_list)
      # plot the filtered frequencies
      plt.scatter(time, plot_freq_list)
      plt.title("Most Prominent Frequency over time after Clustering")
      plt.xlabel("Time (s)")
      plt.ylabel("Frequency (Hz)")
      plt.ylim([0, self.upperFreq])
      self.save_plot_with_name("freq_over_time_clustered")
      plt.clf()

    return [i[0] for i in freq_clusters], filtered_magn, [i[1] for i in freq_clusters]


  # output the audio file in the following format:
  # [(note_freq, duration_in_ms)]
  def extract(self):
    # generate and extract data from spectrogram
    freqs, magn, time = self.get_top_freq_per_seg()
    filtered_freqs, filtered_magn, clustered_time = self.clean_frequencies(freqs, magn, time)
    #self.movingAverage(filtered_freqs)
    return filtered_freqs, filtered_magn, clustered_time
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
    #duration = "0"

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

# main routine
def main():
  parser = OptionParser()
  parser.add_option("-p", "--plot", dest="plot", action="store_true",
                    help="create plots under /graphs", metavar="GRAPHS", default=False)
  parser.add_option("-f", "--file",
                    dest="audiofile", default="./audio/test5.wav",
                    help="path to wav file")

  (options, _) = parser.parse_args()
  fname = options.audiofile
  path = os.path.abspath(fname)
  extractor = MainNotesExtractor(path, 1, options.plot)
  freqs, magn, time = extractor.extract()
  encoder = FrequencyToCode(freqs, time)
  encoder.writeCode()

if __name__ == "__main__":
  main()
