# -*- coding: utf-8 -*-
"""train.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KGuqWhuGA_N2ijObR7vmzzYk1UMo8NXs
"""

import numpy as np
import os
import argparse
import time
import librosa
import pickle
from tqdm import tqdm
import torch
import re
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.utils.spectral_norm as spectral_norm
import IPython.display as display
import gc
from torch.utils.data.dataset import Dataset

from trainclass import trainingDataset, CycleGANTraining

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Train CycleGAN-VC3 using training dataset")
    
    cache_folder = './cache/'
    model_checkpoint = './model_checkpoint/'
    restart_training_at= None
    validation_A_dir = './vcc2020_database_evaluation/vcc2020_database_evaluation/SEM1'
    output_A_dir = './vcc2020_database_evaluation/vcc2020_database_evaluation/A2B_M1toM2'
    validation_B_dir = './vcc2020_database_evaluation/vcc2020_database_evaluation/SEM2'
    output_B_dir = './vcc2020_database_evaluation/vcc2020_database_evaluation/B2A_M2toM1'
    

    parser.add_argument('--cache_folder', type=str,
                        help="Cached location training dataset and stats", default=cache_folder)
    parser.add_argument('--model_checkpoint', type=str,
                        help="location where you want to save the model", default=model_checkpoint)
    parser.add_argument('--restart_training_at', type=str,
                        help="Location of the pre-trained model to restart training", default=restart_training_at)
    parser.add_argument('--validation_A_dir', type=str,
                        help="validation set for sound source A", default=validation_A_dir)
    parser.add_argument('--output_A_dir', type=str,
                        help="output for converted Sound Source A", default=output_A_dir)
    parser.add_argument('--validation_B_dir', type=str,
                        help="Validation set for sound source B", default=validation_B_dir)
    parser.add_argument('--output_B_dir', type=str,
                        help="Output for converted sound Source B", default=output_B_dir)

   # argv = parser.parse_args()
    argv, unknown = parser.parse_known_args()

    cache_folder = argv.cache_folder
    model_checkpoint = argv.model_checkpoint
    restart_training_at = argv.restart_training_at
    validation_A_dir = argv.validation_A_dir
    output_A_dir = argv.output_A_dir
    validation_B_dir = argv.validation_B_dir
    output_B_dir = argv.output_B_dir

    # Check whether following cached files exists
    if not os.path.exists(os.path.join(cache_folder, 'norm_stats.npz')):
        print(
            "Cached files do not exist, please run the program preprocess_training.py first")

    cycleGAN = CycleGANTraining(cache_folder = cache_folder,
               model_checkpoint = model_checkpoint,
               restart_training_at=restart_training_at,
              validation_A_dir = validation_A_dir,          
              output_A_dir = output_A_dir,
              validation_B_dir = validation_B_dir,      
              output_B_dir = output_B_dir
              )
    gc.collect()
    cycleGAN.train()
