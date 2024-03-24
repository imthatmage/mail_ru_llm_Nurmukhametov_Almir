import torch
from peft import (
    PeftConfig,
    PeftModel,
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)


class GPTWrapper:

    def __init__(self):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            load_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        PEFT_MODEL = "models/gpt2/checkpoint-2408"

        config = PeftConfig.from_pretrained(PEFT_MODEL)
        self.model = AutoModelForCausalLM.from_pretrained(
            config.base_model_name_or_path,
            return_dict=True,
            quantization_config=bnb_config,
            device_map="auto",
        )

        self.tokenizer = AutoTokenizer.from_pretrained(config.base_model_name_or_path)
        self.model = PeftModel.from_pretrained(self.model, PEFT_MODEL)
        self.tokenizer.pad_token = self.tokenizer.eos_token

    def generate(self, input_text, **generation_params):
        input_text = f"""
        Task: {input_text}
        Input:
        Output:
        """.strip()
        self.device = "cuda:0"
        encoding = self.tokenizer(input_text, return_tensors="pt").to(self.device)
        with torch.inference_mode():
            outputs = self.model.generate(
                input_ids = encoding.input_ids,
                attention_mask = encoding.attention_mask,
                **generation_params,
        )
        pred_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        sequence_start = pred_text.find("Output: ") + 8
        sequence_end = pred_text.rfind("Output:")

        if sequence_start - 8 != sequence_end:
            # временая заглушка, чтобы был один ответ
            pred_text = pred_text[sequence_start:sequence_end]
        else:
            pred_text = pred_text[sequence_start:]
        return pred_text
        

def construct_model():
    model = GPTWrapper()
    generation_params = {
        "max_new_tokens": 200,
        "num_beams": 3,
        "early_stopping": True,
        "no_repeat_ngram_size": 2,
        "eos_token_id": model.tokenizer.eos_token_id,
        "pad_token_id": model.tokenizer.eos_token_id,
    }
    return model, generation_params