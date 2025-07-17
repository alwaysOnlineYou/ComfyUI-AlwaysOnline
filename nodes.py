import re
import json
import comfy
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
import math
import os
import random
from typing import Any, Optional, Union, Dict, List

class RemoveSceneText:
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "remove_scene"
    CATEGORY = "🚬香烟的工具箱✅/1️⃣文本处理📝"

    def remove_scene(self, text):
        # 从后向前查找第一个匹配的"The scene"
        last_match = None
        for match in re.finditer(r'\bThe scene\b', text, flags=re.IGNORECASE):
            last_match = match
        
        if last_match:
            # 直接截取匹配位置之前的内容
            result = text[:last_match.start()]
        else:
            result = text
            
        return (result.strip(),)

class MultilineTextMerger:
    """合并多个文本并支持自定义分隔符"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "合并选项": (["换行", "双换行", "空格", "逗号", "自定义"], 
                             {"default": "换行"}),
                "忽略空文本": ("BOOLEAN", {"default": True, "display_name": "忽略空文本"}),
            },
            "optional": {
                "text1": ("STRING", {"multiline": True, "default": "", "display_name": "文本1"}),
                "text2": ("STRING", {"multiline": True, "default": "", "display_name": "文本2"}),
                "text3": ("STRING", {"multiline": True, "default": "", "display_name": "文本3"}),
                "text4": ("STRING", {"multiline": True, "default": "", "display_name": "文本4"}),
                "text5": ("STRING", {"multiline": True, "default": "", "display_name": "文本5"}),
                "自定义分隔符": ("STRING", {"default": "", "multiline": False, "display_name": "自定义分隔符"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("合并后的文本",)
    FUNCTION = "merge_multiline"
    CATEGORY = "🚬香烟的工具箱✅/1️⃣文本处理📝"

    def merge_multiline(self, 合并选项, 忽略空文本, **kwargs):
        # 收集所有文本输入
        texts = [kwargs.get(f"text{i}", "") for i in range(1, 6)]
        
        # 处理空文本
        if 忽略空文本:
            texts = [t for t in texts if t.strip()]
        
        # 处理Markdown格式冲突
        processed_texts = []
        for text in texts:
            # 确保代码块完整
            if "```" in text and text.count("```") % 2 != 0:
                text += "\n```"
            processed_texts.append(text)
        
        # 选择分隔符
        separator_map = {
            "换行": "\n",
            "双换行": "\n\n",
            "空格": " ",
            "逗号": ", ",
            "自定义": kwargs.get("自定义分隔符", "")
        }
        sep = separator_map[合并选项]
        
        # 合并文本并保留格式
        merged = sep.join(processed_texts)
        
        # 清理多余的换行
        merged = re.sub(r'\n{3,}', '\n\n', merged)
        
        return (merged,)

class TextReplacer:
    """简单文本替换工具"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "", "display_name": "输入文本"}),
                "find": ("STRING", {"default": "", "multiline": False, "display_name": "查找内容"}),
                "replace": ("STRING", {"default": "", "multiline": False, "display_name": "替换内容"}),
                "replace_all": ("BOOLEAN", {"default": True, "display_name": "全部替换"}),
                "case_sensitive": ("BOOLEAN", {"default": False, "display_name": "区分大小写"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("修改后的文本",)
    FUNCTION = "replace_text"
    CATEGORY = "🚬香烟的工具箱✅/1️⃣文本处理📝"

    def replace_text(self, text, find, replace, replace_all, case_sensitive):
        if not find:
            return (text,)
            
        flags = 0 if case_sensitive else re.IGNORECASE
        
        if replace_all:
            return (re.sub(re.escape(find), replace, text, flags=flags),)
        else:
            return (re.sub(re.escape(find), replace, text, count=1, flags=flags),)

class JsonKeyExtractor:
    DESCRIPTION = """从JSON文本中提取指定路径的值（支持嵌套对象和数组索引）
    
    功能说明：
    1. 支持点号分隔的路径：如 'user.name'
    2. 支持数组索引：如 'data.items[0]'
    3. 支持混合路径：如 'users[0].address.city'
    4. 路径为空时返回整个JSON内容
    
    使用示例：
    - 提取用户名：'user.name'
    - 提取第一个地址的城市：'user.addresses[0].city'
    - 提取第二个分数：'user.scores[1]'
    - 提取状态：'user.active'
    - 空路径返回完整JSON
    
    错误处理：
    - 无效路径返回空字符串
    - 无效JSON返回空字符串
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "required": {
                "json文本": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "display": "JSON文本"
                }),
                "键": ("STRING", {
                    "default": "key",
                    "display": "键",
                    "description": "支持点号和数组索引，如: data.users[0].name"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("值",)
    FUNCTION = "extract_value"
    CATEGORY = "🚬香烟的工具箱✅/1️⃣文本处理📝"

    def extract_value(self, json文本: str, 键: str) -> tuple[str]:
        try:
            # 解析JSON数据
            数据 = json.loads(json文本)
            
            # 如果路径为空，返回整个JSON
            if not 键.strip():
                return (json.dumps(数据, ensure_ascii=False),)
            
            # 解析路径并获取值
            结果 = self._解析路径(数据, 键)
            return (str(结果) if 结果 is not None else "",)
            
        except Exception:
            return ("",)

    def _解析路径(self, 数据: Any, 路径: str) -> Any:
        """解析路径并获取对应的值"""
        if not 路径:
            return 数据
            
        # 分割路径为各个部分
        部分列表 = []
        当前部分 = ""
        在括号中 = False
        
        for 字符 in 路径:
            if 字符 == '[':
                if 当前部分:
                    部分列表.append(当前部分)
                    当前部分 = ""
                在括号中 = True
            elif 字符 == ']':
                if 当前部分:
                    部分列表.append(当前部分)
                    当前部分 = ""
                在括号中 = False
            elif 字符 == '.' and not 在括号中:
                if 当前部分:
                    部分列表.append(当前部分)
                    当前部分 = ""
            else:
                当前部分 += 字符
                
        if 当前部分:
            部分列表.append(当前部分)
        
        # 遍历路径获取值
        结果 = 数据
        for 部分 in 部分列表:
            if 结果 is None:
                break
                
            # 处理数组索引
            if 部分.isdigit():
                if isinstance(结果, list):
                    索引 = int(部分)
                    if 0 <= 索引 < len(结果):
                        结果 = 结果[索引]
                    else:
                        return None
                else:
                    return None
            # 处理字典键
            else:
                if isinstance(结果, dict):
                    结果 = 结果.get(部分)
                else:
                    return None
                    
        return 结果

class MovingWatermark:
    DESCRIPTION = """
    🚬 动态水印生成器 - 为图像/视频帧添加可自定义的移动水印
    完整功能说明
    1. **核心功能**：，在图像/视频帧上添加可移动的文字水印，支持文生视频/图生视频工作流，水印位置根据帧索引自动更新
    2. **自定义参数**：，`text`: 水印文字内容，`font_size`: 字体大小 (8-256px)，`font_color`: 文字颜色 (支持HEX/RGB格式)，`opacity`: 透明度 (0.0-1.0)，`speed`: 移动速度 (0.1-10倍速)，`trajectory`: 移动轨迹模式，`font_path`: 自定义字体文件路径，`custom_trajectory`: JSON格式的自定义路径，`rotation`: 文字旋转角度 (-360°-360°)，`dynamic_size`: 启用动态字体大小，`min_size`/`max_size`: 动态字体大小范围，`stroke_width`: 文字描边宽度，`stroke_color`: 描边颜色，`shadow`: 启用阴影效果，`shadow_color`: 阴影颜色，`shadow_offset`: 阴影偏移量，`blur_radius`: 模糊半径
    3. **轨迹模式**：，`horizontal`: 水平移动，`vertical`: 垂直移动，`circular`: 圆形运动，`diagonal`: 对角线移动，`random`: 随机位置跳动，`spiral`: 螺旋运动，`wave`: 波浪运动，`bounce`: 弹跳运动，自定义路径: 通过JSON坐标点定义
    4. **高级效果**：，自动旋转：圆形/螺旋轨迹自动跟随路径旋转，动态大小：文字大小随时间波动变化，描边效果：增强文字可读性，阴影效果：增加立体感，模糊效果：创建柔和的水印
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", {"default": None}),
                "text": ("STRING", {"default": "水印", "multiline": False}),
                "font_size": ("INT", {"default": 36, "min": 8, "max": 256}),
                "font_color": ("STRING", {"default": "#FFFFFF"}),
                "opacity": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.01}),
                "speed": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "trajectory": (["水平", "垂直", "圆形", "对角线", "随机", "螺旋", "波浪", "弹跳", "心形", "自定义路径"], {"default": "水平"}),
                "frame_index": ("INT", {"default": 0, "min": 0}),
                "total_frames": ("INT", {"default": 1, "min": 1}),
            },
            "optional": {
                "font_path": ("STRING", {"default": ""}),
                "custom_trajectory": ("STRING", {"default": "[]", "multiline": True}),
                "rotation": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0}),
                "dynamic_size": ("BOOLEAN", {"default": False}),
                "min_size": ("INT", {"default": 24, "min": 8, "max": 256}),
                "max_size": ("INT", {"default": 48, "min": 8, "max": 256}),
                "stroke_width": ("INT", {"default": 0, "min": 0, "max": 10}),
                "stroke_color": ("STRING", {"default": "#000000"}),
                "shadow": ("BOOLEAN", {"default": False}),
                "shadow_color": ("STRING", {"default": "#000000"}),
                "shadow_offset": ("INT", {"default": 2, "min": 0, "max": 10}),
                "blur_radius": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 5.0, "step": 0.1}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_watermark"
    CATEGORY = "🚬香烟的工具箱✅/2️⃣水印处理🎬"
    
     # 添加属性描述（ComfyUI会使用这些作为悬浮提示）
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")
    
    # 添加属性描述（ComfyUI会使用这些作为悬浮提示）
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True
    
    def __init__(self):
        self.last_random_pos = (0, 0)
        self.last_size = 36
        self.last_rotation = 0
        self.font_cache = {}
        # 预计算心形轨迹点
        self.heart_points = self.generate_heart_points(100)
    
    def generate_heart_points(self, num_points):
        """生成心形轨迹的归一化坐标点"""
        import math
        points = []
        for i in range(num_points):
            t = 2 * math.pi * i / num_points
            # 心形参数方程
            x = 16 * (math.sin(t) ** 3)
            y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            # 归一化到0-1范围
            x_norm = (x + 16) / 32 * 0.5 + 0.25  # 水平居中
            y_norm = (y + 18) / 31 * 0.5 + 0.25  # 垂直居中
            points.append((x_norm, y_norm))
        return points
    
    def get_font(self, font_path, font_size):
        """获取字体对象并缓存以提高性能"""
        import os
        from PIL import ImageFont
        
        cache_key = f"{font_path}_{font_size}"
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 尝试加载系统字体
                try:
                    # 尝试常见系统字体
                    for font_name in ["Arial", "Helvetica", "DejaVuSans", "FreeSans"]:
                        try:
                            font = ImageFont.truetype(font_name, font_size)
                            break
                        except:
                            continue
                    else:
                        # 所有尝试失败后使用默认字体
                        font = ImageFont.load_default()
                        # 调整默认字体大小
                        font.size = font_size
                except:
                    # 回退到默认字体
                    font = ImageFont.load_default()
                    font.size = font_size
        except Exception as e:
            print(f"字体加载错误: {e}")
            font = ImageFont.load_default()
            font.size = font_size
        
        self.font_cache[cache_key] = font
        return font
		
    def calculate_position(self, width, height, text_width, text_height, frame_idx, total_frames, trajectory, speed, custom_path):
        """计算水印位置，支持多种轨迹模式"""
        import math
        import random
        
        # 确保进度计算正确，避免除以零
        if total_frames <= 0:
            total_frames = 1
            
        # 计算基于速度和帧索引的进度
        progress = (frame_idx * speed) % total_frames / total_frames
        normalized_progress = progress * 2 * math.pi  # 用于周期性运动
        
        # 优先处理自定义路径
        if trajectory == "自定义路径" and custom_path and isinstance(custom_path, list) and len(custom_path) > 0:
            # 自定义轨迹路径
            idx = min(int(progress * len(custom_path)), len(custom_path) - 1)
            point = custom_path[idx]
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                x = point[0] * width
                y = point[1] * height
            else:
                x = width * 0.5
                y = height * 0.5
            return x, y
        
        # 处理水平和垂直轨迹 - 确保第一帧可见
        if trajectory == "水平":
            # 从左侧开始，移动到右侧
            x = progress * (width + text_width) - text_width * 0.5
            y = height * 0.5
            return x, y
            
        elif trajectory == "垂直":
            # 从顶部开始，移动到底部
            x = width * 0.5
            y = progress * (height + text_height) - text_height * 0.5
            return x, y
            
        # 其他轨迹模式
        elif trajectory == "圆形":
            radius = min(width, height) * 0.3
            x = width * 0.5 + radius * math.cos(normalized_progress)
            y = height * 0.5 + radius * math.sin(normalized_progress)
            
        elif trajectory == "对角线":
            # 从左上角移动到右下角
            x = progress * (width + text_width) - text_width * 0.5
            y = progress * (height + text_height) - text_height * 0.5
            
        elif trajectory == "随机":
            if frame_idx == 0 or frame_idx % max(1, int(10/speed)) == 0:
                self.last_random_pos = (
                    random.uniform(text_width * 0.5, width - text_width * 0.5),
                    random.uniform(text_height * 0.5, height - text_height * 0.5)
                )
            x, y = self.last_random_pos
            
        elif trajectory == "螺旋":
            # 螺旋轨迹：半径随时间增加
            spiral_factor = 0.1 + 0.4 * progress
            radius = min(width, height) * spiral_factor
            x = width * 0.5 + radius * math.cos(normalized_progress * 4)
            y = height * 0.5 + radius * math.sin(normalized_progress * 4)
            
        elif trajectory == "波浪":
            # 波浪轨迹：水平移动+垂直波动
            x = progress * (width + text_width) - text_width * 0.5
            wave_height = height * 0.1
            y = height * 0.5 + wave_height * math.sin(normalized_progress * 4)
            
        elif trajectory == "弹跳":
            # 弹跳轨迹：模拟弹跳球
            bounce_progress = progress * 2
            if bounce_progress > 1:
                bounce_progress = 2 - bounce_progress  # 反弹
            height_factor = 1 - (bounce_progress - 1)**2  # 抛物线运动
            x = progress * (width + text_width) - text_width * 0.5
            y = height * (0.1 + 0.8 * height_factor)
            
        elif trajectory == "心形":
            # 使用预计算的心形轨迹点
            idx = min(int(progress * len(self.heart_points)), len(self.heart_points) - 1)
            point = self.heart_points[idx]
            x = point[0] * width
            y = point[1] * height
            
        else:
            # 默认居中
            x = width * 0.5
            y = height * 0.5
            
        return x, y

    def apply_watermark(self, image, text, font_size, font_color, opacity, speed, trajectory, 
                    frame_index, total_frames, font_path="", custom_trajectory="[]", 
                    rotation=0.0, dynamic_size=False, min_size=24, max_size=48,
                    stroke_width=0, stroke_color="#000000", shadow=False, 
                    shadow_color="#000000", shadow_offset=2, blur_radius=0.0):
        import numpy as np
        import json
        import math
        from PIL import Image, ImageDraw, ImageFilter, ImageColor
        
        # 转换为PIL图像处理
        batch_size, height, width, channels = image.shape
        result = torch.zeros_like(image)
        
        # 解析自定义轨迹
        try:
            custom_path = json.loads(custom_trajectory)
            if not isinstance(custom_path, list):
                custom_path = []
        except:
            custom_path = []
        
        # 处理颜色和透明度
        try:
            rgb = ImageColor.getrgb(font_color)
            rgba = tuple(list(rgb) + [int(255 * opacity)])
        except:
            rgba = (255, 255, 255, int(255 * opacity))
            
        # 处理描边颜色
        try:
            stroke_rgb = ImageColor.getrgb(stroke_color)
            stroke_rgba = tuple(list(stroke_rgb) + [int(255 * opacity)])
        except:
            stroke_rgba = (0, 0, 0, int(255 * opacity))
            
        # 处理阴影颜色
        try:
            shadow_rgb = ImageColor.getrgb(shadow_color)
            shadow_rgba = tuple(list(shadow_rgb) + [int(255 * opacity)])
        except:
            shadow_rgba = (0, 0, 0, int(255 * opacity))
        
        # 确保总帧数有效
        if total_frames <= 0:
            total_frames = 1
        
        # 处理每张图像
        for i in range(batch_size):
            img = image[i].numpy() * 255.0
            pil_img = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
            
            # 计算动态字体大小
            current_size = font_size
            if dynamic_size:
                size_progress = (frame_index + i) * speed / total_frames
                size_factor = (math.sin(size_progress * 2 * math.pi) + 1) / 2
                current_size = int(min_size + size_factor * (max_size - min_size))
            
            # 计算动态旋转
            current_rotation = rotation
            if rotation == 0 and trajectory in ["圆形", "螺旋", "心形"]:
                angle_progress = (frame_index + i) * speed / total_frames
                current_rotation = angle_progress * 360
            
            # 获取字体
            font = self.get_font(font_path, current_size)
            
            # 创建水印层
            watermark = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # 计算文字边界框
            try:
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
            except:
                # 回退估算
                text_width = len(text) * current_size * 0.6
                text_height = current_size
            
            # 计算水印位置 - 现在传递text_width和text_height
            x, y = self.calculate_position(
                pil_img.width, pil_img.height, 
                text_width, text_height,
                frame_index + i, total_frames, 
                trajectory, speed, custom_path
            )
            
            # 调整位置为中心点
            x -= text_width / 2
            y -= text_height / 2
            
            # 确保位置在图像范围内
            x = max(0, min(pil_img.width - text_width, x))
            y = max(0, min(pil_img.height - text_height, y))
            
            # 如果是单张图片且使用水平轨迹，调整到右下角
            if total_frames == 1 and trajectory == "水平" and not custom_path:
                # 调整到右下角位置
                x = pil_img.width - text_width - 20  # 右边距20像素
                y = pil_img.height - text_height - 20  # 下边距20像素
            
            # 绘制阴影
            if shadow:
                shadow_pos = (x + shadow_offset, y + shadow_offset)
                draw.text(shadow_pos, text, font=font, fill=shadow_rgba)
            
            # 绘制描边
            if stroke_width > 0:
                # 在多个方向上绘制描边
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y + dy), text, font=font, fill=stroke_rgba)
                
            # 绘制主文字
            draw.text((x, y), text, font=font, fill=rgba)
            
            # 应用模糊效果
            if blur_radius > 0:
                watermark = watermark.filter(ImageFilter.GaussianBlur(blur_radius))
            
            # 应用旋转
            if current_rotation != 0:
                # 创建临时画布用于旋转
                temp_canvas = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
                temp_canvas.paste(watermark, (0, 0))
                rotated = temp_canvas.rotate(current_rotation, expand=True, resample=Image.BICUBIC)
                
                # 重新定位旋转后的水印
                watermark = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
                rot_x = int(x + text_width/2 - rotated.width/2)
                rot_y = int(y + text_height/2 - rotated.height/2)
                watermark.paste(rotated, (rot_x, rot_y))
            
            # 合并图层
            result_img = Image.alpha_composite(pil_img, watermark).convert("RGB")
            result[i] = torch.from_numpy(np.array(result_img).astype(np.float32) / 255.0)
                        
        return (result,)
                
# 节点映射
NODE_CLASS_MAPPINGS = {
    "MultilineTextMerger": MultilineTextMerger,
    "TextReplacer": TextReplacer,
    "RemoveSceneText": RemoveSceneText,
    "JsonKeyExtractor": JsonKeyExtractor,
    "MovingWatermark": MovingWatermark
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MultilineTextMerger": "🚬多行文本合并器✅",
    "TextReplacer": "🚬文本替换器✅",
    "RemoveSceneText": "🚬删除结尾场景语句V2.0✅",
    "JsonKeyExtractor": "🚬JSON键值提取器✅",
    "MovingWatermark": "🚬动态水印生成器✅"
}