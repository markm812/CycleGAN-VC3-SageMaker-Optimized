from scipy.io import wavfile
#import pyworld as pw
import argparse
import os
import numpy as np
import librosa
import matplotlib.pyplot as plt
import librosa.display
import IPython.display as ipd
from os import walk
import IPython.display as display
import torch
from scipy.signal import get_window
import librosa.util as librosa_util
import torch.nn.functional as F
from torch.autograd import Variable
from scipy.signal import get_window
from librosa.util import pad_center, tiny
from librosa.filters import mel as librosa_mel_fn # Create a Filterbank matrix to combine FFT bins into Mel-frequency bins
import glob
import tqdm
import random
import subprocess
from scipy.io.wavfile import read
import yaml
from torch.utils.data.dataset import Dataset
import pickle

n_mel_channels= 80
segment_length= 16000
pad_short= 2000
filter_length= 1024
hop_length= 256 # WARNING: this can't be changed.
win_length= 1024
sampling_rate= 22050
mel_fmin= 0.0
mel_fmax= 8000.0

def normels(wavspath):
  wav_files = glob.glob(os.path.join(wavspath, '**', '*.wav'), recursive=True) #source_path
  vocoder = torch.hub.load('descriptinc/melgan-neurips', 'load_melgan')

  mel_list = list()
  for wavpath in tqdm.tqdm(wav_files, desc='preprocess wav to mel'):
    wav_orig, _ = librosa.load(wavpath, sr=sampling_rate, mono=True)
    spec = vocoder(torch.tensor([wav_orig]))
    mel_list.append(spec.cpu().detach().numpy()[0])

  # Note: np.ma.log() calculating log on masked array (for incomplete or invalid entries in array)
  mel_concatenated = np.ma.log(np.concatenate(mel_list, axis=1)) # 沿时间轴concatenate，各样本时间轴尺寸不同
  mel_mean = np.mean(mel_concatenated, axis=1, keepdims=True)
  mel_std = np.std(mel_concatenated, axis=1, keepdims=True)
  #print(mel_concatenated.shape, mel_mean.shape, mel_std.shape)

  mel_normalized = list()
  for mel in mel_list:
    #print(mel.shape)
    app = (np.ma.log(mel) - mel_mean) / mel_std
    mel_normalized.append(app)
    #print(app.shape, mel_std.shape, mel_mean.shape)

    #denorm_converted = np.ma.exp(app *  mel_std + mel_mean)
    #rev = vocoder.inverse(torch.tensor(np.array([denorm_converted])).float())  # .cuda() torch.Size([1, 80, 399])
    #display.display(display.Audio(rev.cpu().detach().numpy()[0], rate=sampling_rate))

  return mel_normalized, mel_mean, mel_std

def save_pickle(variable, fileName):
    with open(fileName, 'wb') as f:
        pickle.dump(variable, f)

def load_pickle_file(fileName):
    with open(fileName, 'rb') as f:
        return pickle.load(f)

# A training sample consisted of randomly cropped 64 frames
class generatetrainingDataset(Dataset):
    def __init__(self, datasetA, datasetB, n_frames=64):
        self.datasetA = datasetA
        self.datasetB = datasetB
        self.n_frames = n_frames

        num_samples = min(len(datasetA), len(datasetB))

        # Shuffle, first num_samples
        train_data_A_idx = np.arange(len(datasetA)) # numpy.arange([start, ]stop, [step, ]dtype=None)
        train_data_B_idx = np.arange(len(datasetB))
        np.random.shuffle(train_data_A_idx)
        np.random.shuffle(train_data_B_idx)
        train_data_A_idx_subset = train_data_A_idx[:num_samples]
        train_data_B_idx_subset = train_data_B_idx[:num_samples]

        train_data_A = list()
        train_data_B = list()
        for idx_A, idx_B in zip(train_data_A_idx_subset, train_data_B_idx_subset):
            data_A = datasetA[idx_A]
            frames_A_total = data_A.shape[1] # 80, T
            assert frames_A_total >= n_frames
            start_A = np.random.randint(frames_A_total - n_frames + 1)
            end_A = start_A + n_frames
            train_data_A.append(data_A[:, start_A:end_A])

            data_B = datasetB[idx_B]
            frames_B_total = data_B.shape[1]
            assert frames_B_total >= n_frames
            start_B = np.random.randint(frames_B_total - n_frames + 1)
            end_B = start_B + n_frames
            train_data_B.append(data_B[:, start_B:end_B])

        self.train_data_A = np.array(train_data_A)
        self.train_data_B = np.array(train_data_B)

    def __getitem__(self, index):
        return self.train_data_A[index], self.train_data_B[index]

    def __len__(self):
        return min(len(self.datasetA), len(self.datasetB))

def buildTrainset(source_path = './vcc2020_database_training_source/source/SEM1/',target_path = './vcc2020_database_training_target_task1/target_task1/TEM2/',cache_folder = './cache/'):

    print('building training dataset...')

    mel_normalized_A, mel_mean_A, mel_std_A = normels(source_path)
    mel_normalized_B, mel_mean_B, mel_std_B = normels(target_path)

    if not os.path.exists(cache_folder):
      os.makedirs(cache_folder)

    np.savez(os.path.join(cache_folder, 'norm_stats.npz'),
              mean_A=mel_mean_A,
              std_A=mel_std_A,
              mean_B=mel_mean_B,
              std_B=mel_std_B)

    datasetA = mel_normalized_A
    datasetB = mel_normalized_B
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


    dataset = generatetrainingDataset(datasetA=datasetA,
                  datasetB=datasetB,
                  n_frames=64)
    print(dataset.train_data_A.shape, dataset.train_data_B.shape) # (70, 80, 64) (70, 80, 64)

    np.savez(os.path.join(cache_folder, 'train_dataset'), A=dataset.train_data_A, B=dataset.train_data_B)

    print('training dataset constructed and saved!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="generate training dataset and stats")
    
    source_path = './vcc2020_database_training_source/source/SEM1/'
    target_path = './vcc2020_database_training_target_task1/target_task1/TEM2/'
    cache_folder = './cache/'

    parser.add_argument('--source_path', type=str,
                        help="source folder", default=source_path)
    parser.add_argument('--target_path', type=str,
                        help="target folder", default=target_path)
    parser.add_argument('--cache_folder', type=str,
                        help="location to save", default=cache_folder)
    
    argv, unknown = parser.parse_known_args()

    source_path = argv.source_path
    target_path = argv.target_path
    cache_folder = argv.cache_folder

    buildTrainset(source_path=source_path, target_path=target_path, cache_folder=cache_folder)
