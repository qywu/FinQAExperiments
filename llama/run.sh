#!/bin/bash

# DeepSpeed launcher
# torchrun --nproc_per_node=8 --master_port=22100 finetune_llama.py \
#     --model_name_or_path decapoda-research/llama-65b-hf \
#     --data_path llama_finetune_dataset.pkl \
#     --bf16 True \
#     --output_dir llama-65b \
#     --num_train_epochs 3 \
#     --per_device_train_batch_size 4 \
#     --gradient_accumulation_steps 1 \
#     --evaluation_strategy "no" \
#     --save_strategy "steps" \
#     --save_steps 100 \
#     --save_total_limit 3 \
#     --learning_rate 2e-5 \
#     --weight_decay 0. \
#     --warmup_ratio 0.1 \
#     --deepspeed "configs/deepspeed_config.json" \
#     --gradient_checkpointing True \
#     --tf32 True

# FSDP 
torchrun --nproc_per_node=4 --master_port=22100 finetune_llama.py \
--model_name_or_path decapoda-research/llama-7b-hf \
--data_path llama_finetune_dataset.pkl \
--bf16 True \
--output_dir llama-7b \
--num_train_epochs 3 \
--per_device_train_batch_size 2 \
--gradient_accumulation_steps 2 \
--evaluation_strategy "no" \
--save_strategy "epoch" \
--save_total_limit 3 \
--learning_rate 3e-5 \
--weight_decay 0. \
--warmup_ratio 0.1 \
--fsdp "full_shard auto_wrap" \
--fsdp_transformer_layer_cls_to_wrap 'LlamaDecoderLayer' \
--gradient_checkpointing True \
--tf32 True

python inference_llama_65b.py

