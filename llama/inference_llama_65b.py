# %%
import os
import re
import json
import tqdm
import torch
from torch.nn.utils.rnn import pad_sequence
import numpy as np
import ray
import openai
import ast
import time

os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"

time.sleep(120)

torch.backends.cuda.matmul.allow_tf32 = True

from transformers import LlamaTokenizer, LlamaForCausalLM

# %%
class RedundantParenthesesRemover(ast.NodeTransformer):
    def visit_Expr(self, node):
        self.generic_visit(node)
        if isinstance(node.value, ast.BinOp):
            return node.value
        return node

def remove_redundant_parentheses(expression):
    # Parse the expression
    parsed_expression = ast.parse(expression)

    # Remove redundant parentheses
    transformer = RedundantParenthesesRemover()
    transformed_expression = transformer.visit(parsed_expression)

    # Convert the transformed expression back to a string
    simplified_expression = ast.unparse(transformed_expression)

    return simplified_expression
    
def divide(a, b):
    return f"({a} / {b})"

def subtract(a, b):
    return f"({a} - {b})"

def multiply(a, b):
    return f"({a} * {b})"

def add(a, b):
    return f"({a} + {b})"

def exp(a, b):
    return f"({a} ** {b})"

def greater(a, b):
    return f"({a} > {b})"

def translate_expr(expr):
    if "table" in expr:
        return expr
    
    # replace const_m1
    expr = re.sub(r'const_m1', r'-1', expr)

    # change % to / 100
    expr = re.sub(r'([0-9]*\.?[0-9]+)%', r'divide(\1 , 100)', expr)
    
    expr = re.sub(r'const_([0-9]*\.?[0-9]+)', r'\1', expr)
    try:
        new_expr = eval(expr)
        new_expr = remove_redundant_parentheses(new_expr)
    except Exception as e:
        print(e, expr)
        new_expr = expr
    
    return new_expr

def convert_to_markdown(data):
    markdown = "|"
    
    # Add table headers
    for header in data[0]:
        markdown += header + "|"
    markdown += "\n|"
    
    # Add table header separators
    for _ in data[0]:
        markdown += "---|"
    markdown += "\n"
    
    # Add table rows
    for row in data[1:]:
        markdown += "|"
        for cell in row:
            markdown += cell + "|"
        markdown += "\n"
        
    return markdown

def extract_answer(response):
    # extract content inside Calculate()
    matches = re.findall(r"Calculate\(([\(\)0-9 ><,\.\/\+\-\*]*)\)", response)
    if len(matches) == 0:
        if "Yes" in response:
            return "Yes"
        elif "No" in response:
            return "No"
        else:
            return ""
    else:
        output = matches[0].replace(",", "")
        return output
    
def if_exec_correct(t_prog, g_prog):
    try:
        t_exec = eval(t_prog)

        if type(t_exec) == bool and g_prog in ["Yes", "No"]:
            t_exec = "Yes" if t_exec else "No"

            if t_exec == g_prog:
                return True
            
        g_exec = eval(g_prog)

        if t_exec == g_exec:
            return True
        elif t_exec * 100 == g_exec:
            return True
        elif t_exec * 100 == -g_exec:
            return True
        elif t_exec == g_exec * 100:
            return True
        elif t_exec == -g_exec * 100:
            return True
        elif t_exec * 1000000 == g_exec:
            return True
        elif t_exec * 1000000 == -g_exec:
            return True
        elif t_exec == g_exec * 1000000:
            return True
        elif t_exec == -g_exec * 1000000:
            return True
        elif t_exec == -g_exec:
            return True
    except:
        return False

    return False

# %%
tokenizer = LlamaTokenizer.from_pretrained("decapoda-research/llama-65b-hf")

# %%
state_dict = torch.load("./llama-65b-2/checkpoint-564/hf_llama.pth", map_location="cpu")
model = LlamaForCausalLM.from_pretrained("decapoda-research/llama-65b-hf", device_map="auto", torch_dtype=torch.bfloat16)
model.load_state_dict(state_dict)

# %%
system_prompt = (
                "You need to answer the user's question in the ### Question ### section.\n" \
                "You need to provide the answer in the format 'Calculate(a + b)', where the expression needs to be python excutable." \
                # "You can calculate the average of a column by using the function 'Average(table_column_name)'.\n" \
                # "Similarly, you can calculate the sum, the maximum, the minimum, the count of a column by using the functions "\
                # "'Sum(table_column_name)', 'Max(table_column_name)', 'Min(table_column_name)', 'Count(table_column_name)' respectively.\n" \
                # "You only use the table's column name inside those operations\n" \
                "For example, if the question is 'What is the sum of 1 + 2?', you need to answer 'Calc(1 + 2)'." \
                "if the question is 'Is 123 greater than 231?', you need to answer 'Calc(123 > 231)'." \
                # "|Age|\n|---|\n|12|\n|15|\n|16|\n\n What is the average age? The answer is 'Calculate(Average(Age))'" \
                "DO NOT give anything else other than'Calculate()'."
                )

# user_example1 = '"""debt maturities 2013 the following table presents aggregate debt maturities as of december 31 , 2007 , excluding market value adjustments .\nmillions of dollars .\n\n|2008|$ 689|\n|---|---|\n|2009|542|\n|2010|462|\n|2011|550|\n|2012|720|\n|Thereafter|4,717|\n|Total debt|$ 7,680|\n\n\nat december 31 , 2007 , we reclassified as long-term debt approximately $ 550 million of debt due within one year that we intend to refinance .\nthis reclassification reflected our ability and intent to refinance any short- term borrowings and certain current maturities of long-term debt on a long-term basis .\nat december 31 , 2006 , we did not reclassify any short-term debt as long-term debt as we did not intend to refinance at that mortgaged properties 2013 equipment with a carrying value of approximately $ 2.8 billion at both december 31 , 2007 and 2006 serves as collateral for capital leases and other types of equipment obligations in accordance with the secured financing arrangements utilized to acquire such railroad equipment .\nas a result of the merger of missouri pacific railroad company ( mprr ) with and into uprr on january 1 , 1997 , and pursuant to the underlying indentures for the mprr mortgage bonds , uprr must maintain the same value of assets after the merger in order to comply with the security requirements of the mortgage bonds .\nas of the merger date , the value of the mprr assets that secured the mortgage bonds was approximately $ 6.0 billion .\nin accordance with the terms of the indentures , this collateral value must be maintained during the entire term of the mortgage bonds irrespective of the outstanding balance of such bonds .\ncredit facilities 2013 on december 31 , 2007 , $ 1.9 billion of credit was available under our revolving credit facility ( the facility ) , which we entered into on april 20 , 2007 .\nthe facility is designated for general corporate purposes and supports the issuance of commercial paper .\nwe did not draw on the facility during 2007 .\ncommitment fees and interest rates payable under the facility are similar to fees and rates available to comparably rated , investment-grade borrowers .\nthe facility allows for borrowings at floating rates based on london interbank offered rates , plus a spread , depending upon our senior unsecured debt ratings .\nthe facility requires the maintenance of a debt to net worth coverage ratio .\nat december 31 , 2007 , we were in compliance with this covenant .\nthe facility does not include any other financial restrictions , credit rating triggers ( other than rating-dependent pricing ) , or any other provision that could require us to post collateral .\nthe facility , which expires in april 2012 , replaced two $ 1 billion , 5-year facilities with terms ending in march 2009 and march 2010 .\nthe facility includes terms that are comparable with those of the prior facilities , although the minimum net worth requirement of $ 7.5 billion in prior facilities was removed , and the facility includes a change-of-control provision .\nin addition to our revolving credit facility , a $ 75 million uncommitted line of credit was available .\nthe line of credit expires in april 2008 , and was not used in 2007 .\nwe must have equivalent credit available under our five-year facility to draw on this $ 75 million line .\ndividend restrictions 2013 our revolving credit facility includes a debt-to-net worth covenant that , under certain circumstances , would restrict the payment of cash dividends to our shareholders .\nthe amount of retained earnings available for dividends was $ 11.5 billion and $ 7.8 billion at december 31 , 2007 and december 31 , 2006 , respectively .\nthis facility replaced two credit facilities that had minimum net worth covenants that were more restrictive with respect to the amount of retained earnings available for dividends at december 31 , 2006. ."""\n\nQ:what percentage of total debt is due after 2012?'
# assistant_example1 = "Calculate(4717 / 7680)"

# %%
filepath = "../FinQA/dataset/test.json"

with open(filepath) as f:
    data = json.load(f)

programs = []
translated_programs = []
answers = []

for item in tqdm.tqdm(data):
    table_md = convert_to_markdown(item["table_ori"])
    question = item["qa"]["question"]
    
    pre_text = "\n".join(item["pre_text"])
    post_text = "\n".join(item["post_text"])

    programs.append(item["qa"]["program_re"])
    translated_programs.append(translate_expr(item["qa"]["program_re"]))
    answers.append(item["qa"]["answer"])

# %%
model = model.eval()
model = torch.compile(model)

# %%
tokenizer.pad_token_id = tokenizer.unk_token_id

# %%
all_input_ids = []

for item in tqdm.tqdm(data):
    table_md = convert_to_markdown(item["table_ori"])
    question = item["qa"]["question"]
    
    pre_text = "\n".join(item["pre_text"])
    post_text = "\n".join(item["post_text"])
    
    context = f"{pre_text}\n\n{table_md}\n\n{post_text}\n\n"
    user_prompt = f"### Context ###\n\n{context}### Question ###\n\n{question}"
    input_prompt = f"### Instruction ###\n\n{system_prompt}\n\n{user_prompt}\n\n### Answer ###\n\n"

    input_ids = tokenizer.encode(input_prompt, add_special_tokens=False)

    input_ids_length = len(input_ids) 
    max_seq_length = 1984 
    while input_ids_length > max_seq_length:
        # truncate the first input_ids_length - max_seq_length tokens
        context = context.split(" ")[input_ids_length - max_seq_length:]
        context = " ".join(context)
        # recreate the input_text
        user_prompt = f"### Context ###\n\n{context}### Question ###\n\n{question}"
        input_prompt = f"### Instruction ###\n\n{system_prompt}\n\n{user_prompt}\n\n### Answer ###\n\n"

        input_ids = tokenizer.encode(input_prompt, add_special_tokens=False)

        input_ids_length = len(input_ids)

    input_ids = torch.tensor(input_ids)

    all_input_ids.append(input_ids)

# %%
batch_size = 4

responses = []

for i in tqdm.tqdm(range(0, len(all_input_ids), batch_size)):
    batch_input_ids = all_input_ids[i:i+batch_size]
    batch_input_ids = [item.flip(0) for item in batch_input_ids]
    batch_input_ids = pad_sequence(batch_input_ids, 
                                   batch_first=True,
                                   padding_value=tokenizer.pad_token_id).to(model.device)
    batch_input_ids = batch_input_ids.flip(1)

    attention_mask = (batch_input_ids != tokenizer.pad_token_id).bool().to(model.device)

    output = model.generate(batch_input_ids,
                            attention_mask=attention_mask,
                            do_sample=True, 
                            top_p=0.9, 
                            temperature=0.1, 
                            max_new_tokens=128, 
                            eos_token_id=tokenizer.eos_token_id, 
                            pad_token_id=tokenizer.eos_token_id, 
                            early_stopping=True)

    for j in range(output.shape[0]):
        input_ids_length = batch_input_ids.shape[1]
        response = tokenizer.decode(output[j][input_ids_length:], skip_special_tokens=True)

        responses.append(response)

# %%
result = {
    "responses": responses,
    "model_name": "llama65b2-finetune-564",
}

with open("results/llama65b2-finetune-564.json", "w") as f:
    json.dump(result, f, indent=4)

# %%


# %%


# %%



