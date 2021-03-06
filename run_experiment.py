import sys

import wandb

sys.path.append('..')

from src.experiments.argument_handling import make_and_parse_args
from src.experiments.training import train_loop
from src.utils.constants import WANDB_PROJECT, WANDB_ENTITY

if __name__ == '__main__':
    args = make_and_parse_args()
    for _ in range(args.n_runs):
        wandb.init(project=WANDB_PROJECT, entity=WANDB_ENTITY, config=args)
        train_loop(args)
        wandb.finish()