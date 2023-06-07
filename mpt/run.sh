#!/bin/bash

# DeepSpeed launcher
torchrun --nproc_per_node=4 --master_port=22110 finetune.py \
    --model_name_or_path mosaicml/mpt-7b \
    --data_path mpt_finetune_dataset.pkl \
    --bf16 True \
    --output_dir mpt-7b \
    --num_train_epochs 3 \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 1 \
    --evaluation_strategy "no" \
    --save_strategy "epoch" \
    --save_total_limit 3 \
    --learning_rate 3e-5 \
    --weight_decay 0. \
    --warmup_ratio 0.1 \
    --tf32 True

# FSDP 
torchrun --nproc_per_node=4 --master_port=22200 finetune.py \
--model_name_or_path mosaicml/mpt-7b \
--data_path mpt_finetune_dataset.pkl \
--bf16 True \
--output_dir mpt-7b \
--num_train_epochs 3 \
--per_device_train_batch_size 4 \
--gradient_accumulation_steps 1 \
--evaluation_strategy "no" \
--save_strategy "epoch" \
--save_total_limit 3 \
--learning_rate 3e-5 \
--weight_decay 0. \
--warmup_ratio 0.1 \
--fsdp "full_shard auto_wrap" \
--fsdp_transformer_layer_cls_to_wrap 'MPTBlock' \
--gradient_checkpointing True \
--tf32 True

python inference_llama_65b.py

