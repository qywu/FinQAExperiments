from typing import Any, List, Dict, Mapping, Tuple, Union, Optional
import copy
from dataclasses import dataclass, field
import json
import pathlib
from typing import Dict, Optional, Sequence
import pickle

import numpy as np
import torch
import torch.nn.functional as F
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset
import transformers
from transformers import Trainer
from transformers.trainer_pt_utils import LabelSmoother

from transformers import AutoTokenizer, AutoModelForCausalLM

@dataclass
class ModelArguments:
    model_name_or_path: Optional[str] = field(default="empty")

@dataclass
class DataArguments:
    data_path: str = field(
        default=None, metadata={"help": "Path to the training data."}
    )

@dataclass
class TrainingArguments(transformers.TrainingArguments):
    cache_dir: Optional[str] = field(default=None)
    optim: str = field(default="adamw_torch")

local_rank = None

def rank0_print(*args):
    if local_rank == 0:
        print(*args)


class CustomDataCollator:
    def __init__(self, tokenizer) -> None:
        self.tokenizer = tokenizer

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        input_ids = [f["input_ids"] for f in features]
        labels = [f["labels"] for f in features]
        attention_mask = [f["attention_mask"] for f in features]

        input_ids = pad_sequence(input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id)
        labels = pad_sequence(labels, batch_first=True, padding_value=-100)
        attention_mask = pad_sequence(attention_mask, batch_first=True, padding_value=False)

        return dict(
            input_ids=input_ids,
            labels=labels,
            attention_mask=attention_mask,
        )

class FinQAFinetuneDataset(Dataset):
    def __init__(self, data_path, tokenizer):
        self.tokenizer = tokenizer

        with open(data_path, "rb") as f:
            self.data = pickle.load(f)

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        input_ids = self.data[idx]["input_ids"]
        labels = self.data[idx]["labels"]
        attention_mask = self.data[idx]["attention_mask"]
        return dict(
            input_ids=input_ids,
            labels=labels,
            attention_mask=attention_mask,
        )

def make_supervised_data_module(
    tokenizer, data_args
) -> Dict:
    """Make dataset and collator for supervised fine-tuning."""
    rank0_print("Loading data...")
    train_dataset = FinQAFinetuneDataset(data_args.data_path, tokenizer=tokenizer)
    data_collator = CustomDataCollator(tokenizer=tokenizer)
    rank0_print("Done loading data.")
    return dict(train_dataset=train_dataset, data_collator=data_collator)



def train():
    global local_rank

    parser = transformers.HfArgumentParser(
        (ModelArguments, DataArguments, TrainingArguments)
    )
    model_args, data_args, training_args = parser.parse_args_into_dataclasses()
    local_rank = training_args.local_rank

    name = model_args.model_name_or_path
    config = transformers.AutoConfig.from_pretrained(name, trust_remote_code=True)
    config.attn_config['attn_impl'] = 'triton'
    # config.init_device = 'meta'

    model = AutoModelForCausalLM.from_pretrained(
        name,
        config=config,
        torch_dtype=torch.bfloat16, # Load model weights in bfloat16
        trust_remote_code=True
    )
    model.config.use_cache = False
    tokenizer = AutoTokenizer.from_pretrained(
        name,
        trust_remote_code=True
    )
    
    tokenizer.pad_token_id = tokenizer.unk_token_id

    data_module = make_supervised_data_module(tokenizer=tokenizer, data_args=data_args)

    
    trainer = Trainer(
        model=model, tokenizer=tokenizer, args=training_args, **data_module
    )

    if list(pathlib.Path(training_args.output_dir).glob("checkpoint-*")):
        trainer.train(resume_from_checkpoint=True)
    else:
        trainer.train()

if __name__ == "__main__":
    train()
