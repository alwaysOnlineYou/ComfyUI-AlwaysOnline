[中文阅读](./README.md)

# 🚬 This toolkit was developed with the assistance of deepseek. Some features still require more testing and refinement. Interested friends can download and install the plugin themselves. For any issues encountered during use, please submit detailed reports to the issue tracker. I will address them as soon as possible upon receiving feedback. Thank you!

## Plugin Installation
|Method 1|
|------|
|Search in ComfyUI Manager: ComfyUI-AlwaysOnline > install|

|Method 2|
|------|
|Git clone into ComfyUI's custom_nodes folder > Restart ComfyUI after cloning|
```
git clone https://github.com/alwaysOnlineYou/ComfyUI-AlwaysOnline.git
```


## GLM-4V Inference Nodes (Two Types): One for image reverse inference, another for pure text reverse inference (supports system role and user input)
|Required Installation|
|------|
|First, install transformers from source:|
```
pip install git+https://github.com/huggingface/transformers.git
```


|Optional Installation|
|------|
|Pure text reverse inference supports inference modes: sdpa, flash_attention_2. To use flash_attention_2, first install its dependencies:
```
pip install flash-attn --no-build-isolation|
```

# For detailed node usage, see below. After installation, you can browse example workflows under Templates > ComfyUI-AlwaysOnline in the workflow browser, or download them from the exampl_workflows folder in this repository.

## 🚬 Dynamic Watermark Generator Instructions

### Core Features
Add movable text watermarks to images/video frames, supports text-to-video/image-to-video workflows. Watermark position updates automatically based on frame index.

### Custom Parameters
| Parameter | Description |
|------|------|
| `text` | Watermark text content |
| `font_size` | Font size (8-256px) |
| `font_color` | Text color (supports HEX/RGB formats) |
| `opacity` | Transparency (0.0-1.0) |
| `speed` | Movement speed (0.1-10x) |
| `trajectory` | Movement pattern |
| `font_path` | Custom font file path |
| `custom_trajectory` | Custom path in JSON format |
| `rotation` | Text rotation angle (-360°-360°) |
| `dynamic_size` | Enable dynamic font size |
| `min_size`/`max_size` | Dynamic font size range |
| `stroke_width` | Text outline width |
| `stroke_color` | Outline color |
| `shadow` | Enable shadow effect |
| `shadow_color` | Shadow color |
| `shadow_offset` | Shadow offset |
| `blur_radius` | Blur radius |

### Trajectory Patterns
- `horizontal`: Horizontal movement
- `vertical`: Vertical movement
- `circular`: Circular motion
- `diagonal`: Diagonal movement
- `random`: Random position jumping
- `spiral`: Spiral motion
- `wave`: Wave motion
- `bounce`: Bouncing motion
- Custom path: Defined by JSON coordinates

### Advanced Effects
- Auto-rotation: Text automatically rotates with circular/spiral paths
- Dynamic sizing: Text size fluctuates over time
- Outline effect: Enhances text readability
- Shadow effect: Adds depth
- Blur effect: Creates soft watermarks

### Custom Trajectory Examples

#### Example 1: Simple Rectangle Path
```json
[

[0.1, 0.1], // Top-left

[0.9, 0.1], // Top-right

[0.9, 0.9], // Bottom-right

[0.1, 0.9], // Bottom-left

[0.1, 0.1] // Return to start

]
```

Watermark moves along rectangle edges, suitable for periodic looping paths.

#### Example 2: Bezier Curve Path
```json
[

[0.1, 0.5],

[0.3, 0.1],

[0.7, 0.9],

[0.9, 0.5]

]
```

Creates smooth curved motion, ideal for elegant brand watermarks.

#### Example 3: Random Scatter Path
```json
[

[0.2, 0.3], [0.8, 0.4], [0.5, 0.7],

[0.3, 0.8], [0.7, 0.2], [0.4, 0.5]

]
```

Creates seemingly random but controlled motion, good for background watermarks.

### Usage Tips
1. **Number of Path Points**:
   - Minimum 5 points recommended for smooth motion
   - Complex paths can use 20-50 points

2. **Path Closure**:
   - For looping paths, start/end points should match

3. **Coordinate Range**:
   - X: 0.0(left) → 1.0(right)
   - Y: 0.0(top) → 1.0(bottom)

4. **Speed Coordination**:
   - Lower speed (0.5-2.0): For complex paths
   - Higher speed (3.0-5.0): For simple paths

5. **Effect Enhancement**:
   - Enable auto-rotation for path-aligned text
   - Dynamic sizing adds visual interest

### Notes
1. Match path points to frame count:
   - 100-frame video: 50-100 path points
   - Use `len(custom_path) ≈ total_frames / 2` formula

2. Off-screen handling:
   - Coordinates can exceed [0,1] for entrance/exit effects
   - Example: `[-0.1, 0.5] → [1.1, 0.5]` for screen-crossing

3. JSON Validation:
   - Use standard JSON format
   - Verify with online JSON validators

> Custom trajectories offer maximum flexibility, especially for brand promotions or artistic projects requiring precise watermark movement. Well-designed paths can create professional-grade dynamic watermarks.

---

## GLM-4V Image Caption Generator

### Description
ComfyUI node specialized for generating image descriptions using GLM-4V multimodal model

### Model Information

#### Download Links

| Model                   | Download Sources                                                                                                                                               | Type |
|----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|------|
| GLM-4.1V-9B-Thinking | [🤗hf-mirror](https://hf-mirror.com/THUDM/GLM-4.1V-9B-Thinking)<br> [🤗Hugging Face](https://huggingface.co/THUDM/GLM-4.1V-9B-Thinking)<br> [🤖 ModelScope](https://modelscope.cn/models/ZhipuAI/GLM-4.1V-9B-Thinking) | Inference |

### Hardware Requirements
- **VRAM**: Minimum 24GB for H20 GPUs
- **Location**: Must be placed in `models/LLM` directory

### Installation
1. Download GLM-4V model to `models/LLM`
2. Verify directory structure: `ComfyUI/models/LLM/GLM-4.1V-9B-Thinking`

### Input Parameters

#### Required
| Parameter | Type | Default | Range | Description |
|--------|------|--------|------|------|
| Image | IMAGE | - | - | Input image for description |
| Model Path | Dropdown | GLM-4.1V-9B-Thinking | Auto-scanned models | Select installed model version |
| User Input | Multiline | "Briefly describe this image" | - | Prompt guiding description generation |

#### Generation
| Parameter | Type | Default | Range | Description |
|--------|------|--------|------|------|
| Temperature | FLOAT | 0.8 | 0.0-1.0 | Higher values increase randomness |
| top_p | FLOAT | 0.6 | 0.0-1.0 | Nucleus sampling threshold |
| top_k | INT | 2 | 1-200 | Candidate token limit |
| Max New Tokens | INT | 8192 | 512-16384 | Controls output length |
| Repetition Penalty | FLOAT | 1.0 | 0.0-2.0 | Prevents repetitive content |
| Unload Model | BOOL | True | - | Free VRAM after inference |

### Output
| Output | Type | Description |
|--------|------|------|
| Description | STRING | Generated image caption |

### Workflow
1. Connect input image
2. Select model version (auto-detected)
3. Modify prompt (optional)
4. Adjust generation parameters (default recommended)
5. Execute to get description

### Use Cases
- Automated image labeling
- Visual content analysis
- Multimodal dataset processing

---

## GLM-4V Text Reverse Inference Generator

### Description
ComfyUI node using GLM-4V for image description or pure text inference

### Requirements
- **VRAM**: Minimum 24GB for H20 GPUs
- **Location**: Must be in `models/LLM` directory

### Installation
1. Download model to `models/LLM`
2. Verify structure: `ComfyUI/models/LLM/GLM-4.1V-9B-Thinking`

### Input Parameters

#### Required
| Parameter | Type | Default | Range | Description |
|--------|------|--------|------|------|
| Model Path | Dropdown | GLM-4.1V-9B-Thinking | Auto-scanned models | Model selection |
| System Role | Multiline | "You are a helpful assistant." | - | AI role definition |
| User Input | Multiline | "Briefly describe this image" | - | User prompt |
| Temperature | FLOAT | 0.8 | 0.0-1.0 | Generation randomness |
| top_p | FLOAT | 0.6 | 0.0-1.0 | Nucleus sampling |
| top_k | INT | 2 | 1-200 | Top-k sampling |
| Max New Tokens | INT | 8192 | 512-16384 | Output length limit |
| Repetition Penalty | FLOAT | 1.0 | 0.0-2.0 | Repeat prevention |
| Unload Model | BOOL | True | - | VRAM management |
| Inference Mode | Dropdown | sdpa | MyOptions enum | Inference backend |

#### Optional
| Parameter | Type | Description |
|--------|------|------|
| Image | IMAGE | Optional input image |

### Output
| Output | Type | Description |
|--------|------|------|
| Description | STRING | Generated text |

### Example Usage
1. Select model
2. Set system role and user input
3. (Optional) Add image
4. Adjust generation parameters
5. Generate to get results


---

## Text Processing Toolkit

### Overview
ComfyUI node collection offering professional text processing:
1. **Multiline Text Merger** - Multiple merge modes with custom separators
2. **Text Replacer** - Advanced replacement functions
3. **JSON Key Extractor** - Complex path parsing

---

### 1. MultilineTextMerger

#### Description
Intelligently merges multiple text inputs with 5 sources and various merge methods

#### Inputs
| Parameter | Type | Options/Default | Description |
|--------|------|------------|------|
| Merge Mode | Dropdown | Newline/Double newline/Space/Comma/Custom | Merge method |
| Skip Empty | BOOL | True | Ignore empty inputs |
| text1-5 | Multiline | - | 1-5 text sources |
| Custom Separator | String | - | User-defined delimiter |

#### Features
- Auto-fixes incomplete Markdown code blocks
- Smart extra newline cleanup

#### Output
| Output | Type | Description |
|--------|------|------|
| Merged Text | STRING | Formatted combined text |

---

### 2. TextReplacer

#### Description
Advanced text replacement supporting regex and case sensitivity

#### Inputs
| Parameter | Type | Default | Description |
|--------|------|--------|------|
| text | Multiline | - | Source text |
| find | String | - | Search term |
| replace | String | - | Replacement |
| replace_all | BOOL | True | Global/single replacement |
| case_sensitive | BOOL | False | Case matching |

#### Output
| Output | Type | Description |
|--------|------|------|
| Modified Text | STRING | Post-replacement text |

---

### 3. JsonKeyExtractor

#### Description
Complex JSON path parsing including:
- Nested objects (user.address.city)
- Array indices (items[0].name)
- Mixed paths (users[1].scores[0])

#### Inputs
| Parameter | Type | Example | Description |
|--------|------|------|------|
| JSON Text | Multiline | {"user": {"name": "John"}} | Source JSON |
| Key | String | user.name | Extraction path |

#### Path Examples
- `data.users[0].name`
- `items[1].price`
- `status` (direct key)
- Empty path returns full JSON

#### Output
| Output | Type | Description |
|--------|------|------|
| Value | STRING | Extracted result or empty string |

---

### Installation & Usage
1. Place nodes in ComfyUI custom_nodes directory
2. Find under "🚬Cigarette's Toolkit✅" category
3. Connect inputs/outputs to use