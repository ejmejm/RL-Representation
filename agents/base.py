#import abc and abstractmethod
from abc import ABC, abstractmethod

import numpy as np
import torch
from torch import nn

from ..envs import TransitionData


class BaseAgent(ABC):
  @abstractmethod
  def sample_act(self, obs):
    pass

  def process_step_data(self, data: TransitionData):
    pass

  def end_step(self):
    pass

  def end_episode(self):
    pass

  def start_task(self, n_steps):
    pass

  def end_task(self):
    pass


class BaseRepresentationLearner(ABC):
  def __init__(self, model=None, batch_size=32, update_freq=32):
    if model is None:
      self._init_model()
    else:
      self.model = model

    self.batch_size = batch_size
    self.update_freq = update_freq
    
  @abstractmethod
  def _init_model(self, *args, **kwargs):
    pass

  @abstractmethod
  def train(self, batch_data):
    pass

# # Decorator for methods to support representation
# def representation_training()


class TestRL(BaseRepresentationLearner):
  def __init__(self, agent):
    super().__init__(agent)
    self.a = None

  def train(self, data):
    self.a = data



class ExperienceBufferMixin():
  def __init__(self, max_size=int(1e6)):
    self.buffer = []
    self.max_size = max_size

  def _fix_size(self):
    self.buffer = self.buffer[-self.max_size:]

  def append_data(self, data):
    self.buffer.append(data)
    self._fix_size()

  def extend_data(self, data):
    self.buffer.extend(data)
    self._fix_size()

  def sample(self, n, replace=False):
    # Sample indices
    data_idxs = np.random.choice(range(len(self.buffer)),
                                 size=n, replace=replace)
    batch_data = []
    for i in data_idxs:
      batch_data.append(self.buffer[i])

    # Create separate np arrays for each element
    batch_data = np.array(batch_data)
    element_tensors = \
      [torch.from_numpy(np.stack(batch_data[:, i])) \
      for i in range(batch_data.shape[1])]
    
    return element_tensors


def create_basic_fe_model(layer_type='conv', input_dim=None):
  """
  Initializes a basic feature extractor
  
  Args:
    layer_type: 'conv' or 'linear'
    input_dim: (int) size of input (or number of channels)
    
  Returns:
    model: torch.nn.Module
  """
  if layer_type == 'linear':
    return nn.Sequential(
      nn.Linear(input_dim, 256),
      nn.ReLU(),
      nn.Linear(256, 128),
      nn.ReLU(),
      nn.Linear(128, 64))
  elif layer_type == 'conv':
    return nn.Sequential(
          nn.Conv2d(input_dim, 8, 4, 2),
          nn.ReLU(),
          nn.Conv2d(8, 16, 3, 1),
          nn.ReLU(),
          nn.Flatten())
  raise Exception('Invalid layer type!')