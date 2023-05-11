
# GPU Stats


### FSDP
```
torchrun --nproc_per_node=8 --master_port=22100 finetune_llama.py \
    --model_name_or_path decapoda-research/llama-30b-hf \
    --bf16 True \
    --output_dir test \
    --num_train_epochs 3 \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 8 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 100 \
    --save_total_limit 1 \
    --learning_rate 2e-5 \
    --weight_decay 0. \
    --warmup_ratio 0.03 \
    --fsdp "full_shard auto_wrap offload" \
    --fsdp_transformer_layer_cls_to_wrap 'LlamaDecoderLayer' \
    --gradient_checkpointing True \
    --tf32 True
```


### Deepspeed
```
torchrun --nproc_per_node=8 --master_port=22100 finetune_llama.py \
    --model_name_or_path decapoda-research/llama-30b-hf \
    --bf16 True \
    --output_dir test \
    --num_train_epochs 3 \
    --per_device_train_batch_size 8 \
    --gradient_accumulation_steps 2 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 100 \
    --save_total_limit 1 \
    --learning_rate 2e-5 \
    --weight_decay 0. \
    --warmup_ratio 0.03 \
    --deepspeed "configs/deepspeed_config.json" \
    --gradient_checkpointing True \
    --tf32 True
```

We have 6000 example, each with 2048 tokens.


| Model | Parallel Method | Grad Ckp | Batch size | #GPUs | GPU Memory |    Time |
| ---   | ---    | --- | --- |   ---     | ---   | --- |
| LLaMA-7B  | FSDP | yes | 1 | 2 |  81GB | 3:16:00 |
| LLaMA-7B  | FSDP + offload | yes | 1 | 2 |  60GB | 19:03:00 |
| LLaMA-7B  | FSDP | yes | 1 | 4 | 59GB | 1:32:00  |
| LLaMA-7B  | FSDP | yes | 1 | 8 | 45GB  | 0:52:10 |
| LLaMA-7B  | FSDP | yes | 4 | 8 | 56GB | 0:38:00 |
| ---   | ---    | --- |  --- |  ---     | ---   | --- |
| LLaMA-13B | FSDP | yes | 1 | 4 | 81GB | 7:46:01 |
| LLaMA-13B | FSDP + offload | yes | 1 | 4 | 77GB | 10:58:56 |
| LLaMA-13B | Deepspeed + Zero 3 + Offload | yes | 1 | 4 |  14GB | 8:41:00 |
| LLaMA-13B | Deepspeed + Zero 3 + Offload | no | 1 | 4 |  OOM | X |
| LLaMA-13B | Deepspeed + Zero 3 + Offload | yes | 8 | 4 |  55GB | 4:40:05 |
| LLaMA-13B | Deepspeed + Zero 3 + Offload | yes | 16 | 4 | OOM  | X |
| LLaMA-13B | Deepspeed + Zero 3 + Offload | yes | 32 | 4 | OOM  | X |
| LLaMA-13B | FSDP | yes | 1 | 8 | 78GB  | 1:21:00 |
| ---   | ---    | --- |    ---     | ---   | --- | --- |
| LLaMA-30B | FSDP | yes | 1 | 4 |  OOM | X |
| LLaMA-30B | Deepspeed + Zero 3 + Offload | yes | 1 | 4 | 18GB  | 39:33:19 |
| LLaMA-30B | Deepspeed + Zero 3 + Offload | yes | 4 | 4 |  58GB | 12:02:28 |
| LLaMA-30B | Deepspeed + Zero 3 + Offload | yes | 6 | 4 |  67GB | 9:42:04 |
| LLaMA-30B | Deepspeed + Zero 3 + Offload | yes | 8 | 4 |  80GB | 8:10:45 |
| LLaMA-30B | FSDP | yes | 1 | 8 |  OOM | X |
| LLaMA-30B | FSDP + offload | yes | 1 | 8 |  80GB | 24:51:02 |
| LLaMA-30B | Deepspeed + Zero 3 + Offload | yes | 1 | 8 | 36GB  |  7:39:30 |
| LLaMA-30B | Deepspeed + Zero 3 + Offload | yes | 4 | 8 | 55GB  |  5:51:16 |
| LLaMA-30B | Deepspeed + Zero 3 + Offload | yes | 8 | 8 | 55GB  |  3:25:42 |
| ---   | ---    | --- | --- |    ---     | ---   | --- |
| LLaMA-65B | FSDP + offload | yes | 1 | 8 |  OOM | X |
| LLaMA-65B | Deepspeed + Zero 3 + Offload | yes | 1 | 8 |  50GB | 33:37:16 |
| LLaMA-65B | Deepspeed + Zero 3 + Offload | yes | 2 | 8 | 58GB  | 19:16:41  |
| LLaMA-65B | Deepspeed + Zero 3 + Offload | yes | 4 | 8 | 77GB  | 11:37:33 |