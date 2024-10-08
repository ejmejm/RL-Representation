import torch
from torch import nn

class ReshapeLayer(nn.Module):
  """A layer that reshapes the input tensor to a specified shape."""

  def __init__(self, shape):
    """
    Args:
      shape: The desired output shape (excluding batch dimension).
    """
    super().__init__()
    self.shape = shape

  def forward(self, x):
    batch_size = x.shape[0]
    return x.view(batch_size, *self.shape)

def create_simple_1D_encoder(input_dim):
  """Creates a simple 1D encoder network."""
  flat_dim = input_dim[0] * input_dim[1]
  return nn.Sequential(
    nn.Flatten(),
    nn.Linear(flat_dim, 16),
    nn.ReLU(),
    nn.Linear(16, 32),
    nn.ReLU())

def create_simple_1D_decoder(input_dim):
  """Creates a simple 1D decoder network."""
  flat_dim = input_dim[0] * input_dim[1]
  return nn.Sequential(
    nn.Linear(32, 16),
    nn.ReLU(),
    nn.Linear(16, flat_dim),
    ReshapeLayer(input_dim))

def create_gridworld_encoder(n_channels=1):
  """Creates an encoder network for GridWorld environments."""
  return nn.Sequential(
    nn.Conv2d(n_channels, 8, 4, 2),
    nn.ReLU(),
    nn.Conv2d(8, 16, 3, 1),
    nn.ReLU())

def create_gridworld_decoder(n_channels=1):
  """Creates a decoder network for GridWorld environments."""
  return nn.Sequential(
    nn.ConvTranspose2d(16, 8, 3, 1),
    nn.ReLU(),
    nn.ConvTranspose2d(8, n_channels, 4, 2),
    nn.Conv2d(n_channels, n_channels, 3, 1, 1))

def create_atari_encoder(n_channels=4):
  """Creates an encoder network for Atari environments."""
  return nn.Sequential(
    nn.Conv2d(n_channels, 32, 5, 5, 0),
    nn.ReLU(),
    nn.Conv2d(32, 64, 5, 5, 0),
    nn.ReLU())

def create_atari_decoder(n_channels=4):
  """Creates a decoder network for Atari environments."""
  return nn.Sequential(
    nn.ConvTranspose2d(64, 32, 5, 5, 0),
    nn.ReLU(),
    nn.ConvTranspose2d(32, n_channels, 5, 5, 0),
    nn.ReLU(),
    nn.Conv2d(n_channels, n_channels, 3, 1, 1))

GYM_HIDDEN_SIZE = 32
GRIDWORLD_HIDDEN_SIZE = 64
ATARI_HIDDEN_SIZE = 256

def get_hidden_size_from_obs_dim(obs_dim):
  """Determines the appropriate hidden size based on observation dimensions."""
  if len(obs_dim) == 2:
    if obs_dim[0] <= 32:
      return GYM_HIDDEN_SIZE
    else:
      raise Exception('1D observation dimensions this large are not supported!')
  elif obs_dim[1] <= 32:
    return GRIDWORLD_HIDDEN_SIZE
  return ATARI_HIDDEN_SIZE

def create_encoder_from_obs_dim(obs_dim):
  """Creates an appropriate encoder based on observation dimensions."""
  if len(obs_dim) == 2:
    if obs_dim[0] <= 32:
      return create_simple_1D_encoder(obs_dim)
    else:
      raise Exception('1D observation dimensions this large are not supported!')
  elif obs_dim[1] <= 32:
    return create_gridworld_encoder(obs_dim[0])
  return create_atari_encoder(obs_dim[0])

def create_decoder_from_obs_dim(obs_dim):
  """Creates an appropriate decoder based on observation dimensions."""
  if len(obs_dim) == 1:
    if obs_dim[0] <= 32:
      return create_simple_1D_decoder(obs_dim)
    else:
      raise Exception('1D observation dimensions this large are not supported!')
  elif obs_dim[1] <= 32:
    return create_gridworld_decoder(obs_dim[0])
  return create_atari_decoder(obs_dim[0])

class PolicyNetwork(nn.Module):
  """A neural network for policy prediction."""

  def __init__(self, obs_dim, n_acts, encoder=None, hidden_size=None):
    """
    Args:
      obs_dim: Observation dimension.
      n_acts: Number of possible actions.
      encoder: Optional custom encoder network.
      hidden_size: Optional custom hidden layer size.
    """
    super().__init__()
    if encoder is None:
      encoder = create_encoder_from_obs_dim(obs_dim)

    test_input = torch.zeros(1, *obs_dim)
    with torch.no_grad():
      self.encoder_output_size = encoder(test_input).view(-1).shape[0]

    if not hidden_size:
      hidden_size = get_hidden_size_from_obs_dim(obs_dim)
    self.layers = nn.Sequential(
      encoder,
      nn.Flatten(),
      nn.Linear(self.encoder_output_size, hidden_size),
      nn.ReLU(),
      nn.Linear(hidden_size, n_acts))

  def forward(self, x):
    return self.layers(x)

class CriticNetwork(nn.Module):
  """A neural network for value function estimation."""

  def __init__(self, obs_dim, encoder=None, hidden_size=None):
    """
    Args:
      obs_dim: Observation dimension.
      encoder: Optional custom encoder network.
      hidden_size: Optional custom hidden layer size.
    """
    super().__init__()
    if encoder is None:
      encoder = create_encoder_from_obs_dim(obs_dim)

    test_input = torch.zeros(1, *obs_dim)
    with torch.no_grad():
      self.encoder_output_size = encoder(test_input).view(-1).shape[0]

    if not hidden_size:
      hidden_size = get_hidden_size_from_obs_dim(obs_dim)
    self.layers = nn.Sequential(
      encoder,
      nn.Flatten(),
      nn.Linear(self.encoder_output_size, hidden_size),
      nn.ReLU(),
      nn.Linear(hidden_size, 1))

  def forward(self, x):
    return self.layers(x)

class DDDQNNetwork(nn.Module):
  """A neural network for Dueling Double Deep Q-Network."""

  def __init__(self, obs_dim, n_acts, encoder=None, hidden_size=None):
    """
    Args:
      obs_dim: Observation dimension.
      n_acts: Number of possible actions.
      encoder: Optional custom encoder network.
      hidden_size: Optional custom hidden layer size.
    """
    super().__init__()
    if encoder is None:
      encoder = create_encoder_from_obs_dim(obs_dim)
    self.encoder = encoder

    test_input = torch.zeros(1, *obs_dim)
    with torch.no_grad():
      self.encoder_output_size = encoder(test_input).view(-1).shape[0]

    if not hidden_size:
      hidden_size = get_hidden_size_from_obs_dim(obs_dim)
    self.value_layers = nn.Sequential(
      nn.Flatten(),
      nn.Linear(self.encoder_output_size, hidden_size),
      nn.ReLU(),
      nn.Linear(hidden_size, 1))

    self.advantage_layers = nn.Sequential(
      nn.Flatten(),
      nn.Linear(self.encoder_output_size, hidden_size),
      nn.ReLU(),
      nn.Linear(hidden_size, n_acts))

    self._init_weights()

  def _init_weights(self):
    """Initializes the weights of the last layers to zero."""
    self.value_layers[-1].weight.data.fill_(0)
    self.value_layers[-1].bias.data.fill_(0)
    self.advantage_layers[-1].weight.data.fill_(0)
    self.advantage_layers[-1].bias.data.fill_(0)

  def forward(self, x):
    z = self.encoder(x)
    values = self.value_layers(z)
    advantages = self.advantage_layers(z)

    advantage_means = advantages.mean(dim=1, keepdim=True)
    advantages = advantages - advantage_means

    qs = values + advantages

    return qs

class SFNetwork(nn.Module):
  """A neural network for Successor Feature prediction."""

  def __init__(self, obs_dim, embed_dim=256, encoder=None, hidden_size=None):
    """
    Args:
      obs_dim: Observation dimension.
      embed_dim: Embedding dimension.
      encoder: Optional custom encoder network.
      hidden_size: Optional custom hidden layer size.
    """
    super().__init__()
    if encoder is None:
      encoder = create_encoder_from_obs_dim(obs_dim)

    test_input = torch.zeros(1, *obs_dim)
    with torch.no_grad():
      self.encoder_output_size = encoder(test_input).view(-1).shape[0]
    
    self.encoder = nn.Sequential(
      encoder,
      nn.Flatten(),
      nn.Linear(self.encoder_output_size, embed_dim),
      nn.LayerNorm(embed_dim))

    if not hidden_size:
      hidden_size = get_hidden_size_from_obs_dim(obs_dim)
    self.sf_predictor = nn.Sequential(
      nn.Linear(embed_dim, hidden_size),
      nn.ReLU(),
      nn.Linear(hidden_size, hidden_size),
      nn.ReLU(),
      nn.Linear(hidden_size, embed_dim))

  def forward(self, x):
    embeds = self.encoder(x)
    sfs = self.sf_predictor(embeds)
    return embeds, sfs

class StatePredictionModel(nn.Module):
  """A neural network for predicting the next state given the current state and action."""

  def __init__(self, obs_dim, n_acts, hidden_size=None):
    """
    Args:
      obs_dim: Observation dimension.
      n_acts: Number of possible actions.
      hidden_size: Optional custom hidden layer size.
    """
    super().__init__()
    self.downsample_convs = create_encoder_from_obs_dim(obs_dim)

    test_input = torch.zeros([1] + list(obs_dim))
    output_dim = self.downsample_convs(test_input).view(-1).shape[0]

    if not hidden_size:
      hidden_size = get_hidden_size_from_obs_dim(obs_dim)
    self.fc = nn.Sequential(
      nn.Linear(output_dim + n_acts, hidden_size),
      nn.ReLU(),
      nn.Linear(hidden_size, hidden_size),
      nn.ReLU(),
      nn.Linear(hidden_size, output_dim),
      nn.ReLU())

    self.upsample_convs = create_decoder_from_obs_dim(obs_dim)

    self.encoder = nn.Sequential(
      self.downsample_convs,
      nn.Flatten())

  def forward(self, obs, acts):
    conv_out = self.downsample_convs(obs)
    z = conv_out.view(obs.shape[0], -1)
    z = torch.cat([z, acts], dim=1)
    z = self.fc(z)
    z = z.view(*list(conv_out.shape))
    out = self.upsample_convs(z)
    return out