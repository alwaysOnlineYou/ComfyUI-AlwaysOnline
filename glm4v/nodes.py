import os
import re
import torch
from transformers import AutoProcessor, Glm4vForConditionalGeneration
import comfy
import folder_paths
from PIL import Image
import numpy as np
import json
from enum import Enum

# 获取当前ComfyUI根目录
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
models_path = os.path.join(current_dir, 'models/LLM')

class GLM4VImageDescription_V2:
    DESCRIPTION = """
    GLM-4V 图像描述生成器
    功能：使用GLM-4V模型生成图像描述
    使用说明：**注意：原模型在H20显卡上测试需至少有24G显存才可跑**
    1. 将模型下载放置在models/LLM目录下
    2. 选择模型路径和输入图像
    3. 设置生成参数（温度、top_p等）
    4. 输入用户输入（默认为"简单描述这张图片内容"）
    5. 点击生成获取描述结果
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 扫描/models/LLM目录下可用的模型
        models = []
        if os.path.exists(models_path):
            models = [d for d in os.listdir(models_path) if os.path.isdir(os.path.join(models_path, d))]
        
        return {
            "required": {
                "图像": ("IMAGE",),
                "模型路径": (models, {"default": "GLM-4.1V-9B-Thinking"} if models else {}),
                # "模型路径": ("STRING", {"default": "", "multiline": False, "display_name": "模型路径"}),
                "用户输入": ("STRING", {"multiline": True, "default": "简单描述这张图片内容"}),
                "温度": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_p": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_k": ("INT", {"default": 2, "min": 1, "max": 200, "step": 1}),
                "最大新token数": ("INT", {"default": 8192, "min": 512, "max": 16384, "step": 1}),
                "重复惩罚": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "卸载模型": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("描述",)
    FUNCTION = "describe_image"
    CATEGORY = "🚬香烟的工具箱✅/3️⃣提示词反推📝"
    
    def __init__(self):
        self.model = None
        self.processor = None
    
    def describe_image(self, 图像, 模型路径, 用户输入, 温度, top_p, top_k, 最大新token数, 重复惩罚, 卸载模型):
        # 如果模型已加载且需要卸载，则先卸载
        if 卸载模型 and self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            torch.cuda.empty_cache()
        
        # 将ComfyUI图像张量转换为PIL图像
        # 图像张量格式为[N, H, W, C]，其中N=1, C=3 (RGB)
        image_np = 图像[0].numpy() * 255.0
        image_np = np.clip(image_np, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(image_np)
        
        # 保存图像到临时文件
        temp_image_path = os.path.join(folder_paths.get_temp_directory(), "glm4v_temp_image.png")
        pil_image.save(temp_image_path)
                
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "url": temp_image_path},
                    {"type": "text", "text": 用户输入}
                ]
            }
        ]
        
        # 如果模型未加载，则加载模型
        if self.model is None:
            full_model_path = os.path.join(models_path, 模型路径)
            self.processor = AutoProcessor.from_pretrained(full_model_path, use_fast=True)
            self.model = Glm4vForConditionalGeneration.from_pretrained(
                full_model_path,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                attn_implementation="sdpa"
            )
        
        # 处理输入
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
            padding=True
        ).to(self.model.device)
                
        # 生成输出
        output = self.model.generate(
            **inputs,
            max_new_tokens=最大新token数,
            repetition_penalty=重复惩罚,
            do_sample=温度 > 0,
            top_k=top_k,
            top_p=top_p,
            temperature=温度 if 温度 > 0 else None,
        )
        
        # 解码输出
        raw = self.processor.decode(
            output[0][inputs["input_ids"].shape[1]:-1],
            skip_special_tokens=True
        )
        
        # 尝试解析JSON格式的输出
        json_data = None
        json_match = None
        if raw.startswith('{') or raw.startswith('['):
            json_data = json.loads(raw)
            json_match = re.search(r'<answer>(.*)', json.dumps(json_data), re.DOTALL)
        
        # 匹配答案
        original_match = re.search(r"<answer>(.*)", raw, re.DOTALL)
        match = json_match if json_match else original_match
        answer = match.group(1).strip() if match else raw.strip()
        
        print(f"[GLM4V] Prompt: {answer}")
        
        # 清理临时文件
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        
        # 如果需要卸载模型，则立即卸载
        if 卸载模型:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            torch.cuda.empty_cache()
        
        return (answer,)

class MyOptions(Enum):
    flash_attention_2 = "flash_attention_2"
    sdpa = "sdpa"

class GLM4VTextToDescription:
    DESCRIPTION = """
    GLM-4V 文本反推描述生成器
    功能：使用GLM-4V模型生成图像描述或纯文本推理
    使用说明：**注意：原模型在H20显卡上测试需至少有24G显存才可跑**
    1. 将模型下载放置在models/LLM目录下
    2. 选择模型路径
    3. 可选择输入图像或仅使用系统角色和用户输入
    4. 设置生成参数（温度、top_p等）
    5. 点击生成获取结果
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取当前ComfyUI根目录
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        models_path = os.path.join(current_dir, 'models/LLM')
        
        # 扫描/models/LLM目录下可用的模型
        models = []
        if os.path.exists(models_path):
            models = [d for d in os.listdir(models_path) if os.path.isdir(os.path.join(models_path, d))]
        
        # option = True

        return {
            "required": {
                "模型路径": (models, {"default": "GLM-4.1V-9B-Thinking"} if models else {}),
                "系统角色": ("STRING", {"multiline": True, "default": "You are a helpful assistant."}),
                "用户输入": ("STRING", {"multiline": True, "default": "简单描述这张图片内容"}),
                "温度": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_p": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_k": ("INT", {"default": 2, "min": 1, "max": 200, "step": 1}),
                "最大新token数": ("INT", {"default": 8192, "min": 512, "max": 16384, "step": 1}),
                "重复惩罚": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "卸载模型": ("BOOLEAN", {"default": True}),
                "推理模式": (list(MyOptions._member_names_), {"default": "sdpa"}),
            },
            "optional": {
                "图像": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("描述",)
    FUNCTION = "describe_image"
    CATEGORY = "🚬香烟的工具箱✅/3️⃣提示词反推📝"
    
    def __init__(self):
        self.model = None
        self.processor = None
    
    def describe_image(self, 模型路径, 系统角色, 用户输入, 温度, top_p, top_k, 最大新token数, 重复惩罚, 卸载模型, 推理模式, 图像=None):
        # 如果模型已加载且需要卸载，则先卸载
        if 卸载模型 and self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            torch.cuda.empty_cache()
        
        # 构建消息
        messages = []
        
        # 如果有图像输入，则处理图像
        if 图像 is not None:
            # 将ComfyUI图像张量转换为PIL图像
            # 图像张量格式为[N, H, W, C]，其中N=1, C=3 (RGB)
            image_np = 图像[0].numpy() * 255.0
            image_np = np.clip(image_np, 0, 255).astype(np.uint8)
            pil_image = Image.fromarray(image_np)
            
            # 保存图像到临时文件
            temp_image_path = os.path.join(folder_paths.get_temp_directory(), "glm4v_temp_image.png")
            pil_image.save(temp_image_path)

            # print(f"临时图片路径: {temp_image_path}")
            
            messages.append(
                [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "content": 系统角色
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "url": temp_image_path},
                            {"type": "text", "text": 用户输入}
                        ]
                    }
                ]
            )
        else:
            messages.append(
                [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "content": 系统角色
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": 用户输入}
                        ]
                    }
                ]
            )
        
        print(f"推理模式>>>>>>: {推理模式}")

        # 如果模型未加载，则加载模型
        if self.model is None:
            full_model_path = os.path.join(models, 模型路径)
            self.processor = AutoProcessor.from_pretrained(full_model_path, use_fast=True)
            self.model = Glm4vForConditionalGeneration.from_pretrained(
                full_model_path,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                attn_implementation= 推理模式
            )
        
        # 处理输入
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
            padding=True
        ).to(self.model.device)
                
        # 生成输出
        output = self.model.generate(
            **inputs,
            max_new_tokens=最大新token数,
            repetition_penalty=重复惩罚,
            do_sample=温度 > 0,
            top_k=top_k,
            top_p=top_p,
            temperature=温度 if 温度 > 0 else None,
        )
        
        # 解码输出
        raw = self.processor.decode(
            output[0][inputs["input_ids"].shape[1]:-1],
            skip_special_tokens=True
        )
        
        # 尝试解析JSON格式的输出
        json_data = None
        json_match = None
        if raw.startswith('{') or raw.startswith('['):
            json_data = json.loads(raw)
            json_match = re.search(r'<answer>(.*)', json.dumps(json_data), re.DOTALL)
        
        # 匹配答案
        original_match = re.search(r"<answer>(.*)", raw, re.DOTALL)
        match = json_match if json_match else original_match
        answer = match.group(1).strip() if match else raw.strip()
        
        print(f"[GLM4V] Prompt: {answer}")
        
        # 清理临时文件
        if 图像 is not None and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        
        # 如果需要卸载模型，则立即卸载
        if 卸载模型:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            torch.cuda.empty_cache()
        
        return (answer,)


NODE_CLASS_MAPPINGS = {
    "GLM4VImageDescription_V2": GLM4VImageDescription_V2,
    "GLM4VTextToDescription": GLM4VTextToDescription
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GLM4VImageDescription_V2": "🚬GLM-4V图像反推提示词V2.0✅",
    "GLM4VTextToDescription": "🚬GLM-4V文本反推提示词✅"
}