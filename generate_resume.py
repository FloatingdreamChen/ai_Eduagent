from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Flowable
import os

# ── Colors ──
PRIMARY = HexColor("#1a237e")
SECONDARY = HexColor("#283593")
ACCENT = HexColor("#3949ab")
LIGHT_BG = HexColor("#e8eaf6")
DARK_TEXT = HexColor("#212121")
GRAY_TEXT = HexColor("#616161")
LIGHT_GRAY = HexColor("#f5f5f5")
DIVIDER = HexColor("#c5cae9")

# ── Try to register a CJK font for Chinese support ──
FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
CN_FONT = "Helvetica"
CN_BOLD = "Helvetica-Bold"

for font_path, fname, fbname in [
    ("/System/Library/Fonts/PingFang.ttc", "PingFang", "PingFang-Bold"),
    ("/System/Library/Fonts/STHeiti Light.ttc", "STHeiti", "STHeiti-Bold"),
    ("/System/Library/Fonts/Supplemental/Songti.ttc", "Songti", "Songti-Bold"),
]:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont(fname, font_path))
            CN_FONT = fname
            CN_BOLD = fname
        except Exception:
            pass
        break

# ── Styles ──
styles = getSampleStyleSheet()

def make_style(name, parent="Normal", font=None, size=10, color=DARK_TEXT, align=TA_LEFT, space_before=0, space_after=0, leading=None, bold=False):
    f = font or (CN_BOLD if bold else CN_FONT)
    return ParagraphStyle(name, parent=styles[parent], fontName=f, fontSize=size, textColor=color, alignment=align, spaceBefore=space_before, spaceAfter=space_after, leading=leading or size * 1.4)

s_name = make_style("s_name", size=26, color=PRIMARY, align=TA_CENTER, bold=True, space_after=2)
s_title = make_style("s_title", size=12, color=GRAY_TEXT, align=TA_CENTER, space_after=6)
s_contact = make_style("s_contact", size=9, color=DARK_TEXT, align=TA_CENTER, space_after=2)
s_section = make_style("s_section", size=14, color=PRIMARY, bold=True, space_before=10, space_after=4)
s_sub = make_style("s_sub", size=11, color=DARK_TEXT, bold=True, space_before=6, space_after=1)
s_sub2 = make_style("s_sub2", size=10, color=GRAY_TEXT, space_after=1)
s_body = make_style("s_body", size=9.5, color=DARK_TEXT, leading=15, space_after=2)
s_body_sm = make_style("s_body_sm", size=9, color=DARK_TEXT, leading=14, space_after=1)
s_bullet = make_style("s_bullet", size=9.5, color=DARK_TEXT, leading=15, space_after=1)

# ── Helper ──
def section(title):
    return [
        Paragraph(title, s_section),
        HRFlowable(width="100%", thickness=0.8, color=DIVIDER, spaceBefore=0, spaceAfter=4),
    ]

def bullet(text):
    return Paragraph(f"  \u2022  {text}", s_bullet)

def sub_header(left, right):
    return Table(
        [[Paragraph(left, s_sub), Paragraph(right, s_sub2)]],
        colWidths=[12*cm, 5*cm],
        style=TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("ALIGN", (1,0), (1,0), "RIGHT"),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ])
    )

# ── Build PDF ──
output_path = "/Volumes/XD20/py_project/EduAgent/AI_大模型算法工程师_简历.pdf"
doc = SimpleDocTemplate(
    output_path, pagesize=A4,
    topMargin=1.8*cm, bottomMargin=1.8*cm,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
)

story = []

# ── Header ──
story.append(Paragraph("张明远", s_name))
story.append(Paragraph("AI / 大模型算法工程师", s_title))
story.append(Paragraph(
    "male | 28 years old | +86-138-0000-1234 | zhangmy@email.com | github.com/zhangmy",
    s_contact
))
story.append(Paragraph("Beijing, China", s_contact))
story.append(Spacer(1, 6))

# ── Education ──
story.extend(section("Education"))
story.append(sub_header("Peking University", "Sep 2020 - Jun 2023"))
story.append(Paragraph("Master of Computer Science (NLP Direction), GPA: 3.8/4.0", s_body))
story.append(Spacer(1, 2))
story.append(sub_header("Tsinghua University", "Sep 2016 - Jun 2020"))
story.append(Paragraph("Bachelor of Computer Science and Technology, GPA: 3.7/4.0", s_body))
story.append(Spacer(1, 6))

# ── Skills ──
story.extend(section("Technical Skills"))
skills_data = [
    [Paragraph("Languages", s_sub), Paragraph("Python (proficient), C++ (proficient), CUDA (skilled)", s_body_sm)],
    [Paragraph("Frameworks / Libs", s_sub), Paragraph("PyTorch, TensorFlow, DeepSpeed, Megatron-LM, Transformers, vLLM, LangChain, LlamaIndex", s_body_sm)],
    [Paragraph("Models", s_sub), Paragraph("GPT / LLaMA / ChatGLM / Qwen series, LoRA / QLoRA, PPO / DPO, MoE, FlashAttention, Speculative Decoding", s_body_sm)],
    [Paragraph("Infra", s_sub), Paragraph("Docker, Kubernetes, Slurm, WandB, MLflow, ONNX, TensorRT, Triton Inference Server", s_body_sm)],
]
t = Table(skills_data, colWidths=[3*cm, 14*cm])
t.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 1),
    ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ("LEFTPADDING", (0,0), (-1,-1), 0),
    ("RIGHTPADDING", (0,0), (-1,-1), 0),
]))
story.append(t)
story.append(Spacer(1, 6))

# ── Work Experience ──
story.extend(section("Work Experience"))

# Job 1
story.append(sub_header("Senior Algorithm Engineer  @  ByteDance (AI Lab)", "Jun 2023 - Present"))
story.append(bullet("Led the SFT + RLHF training of a 70B-scale LLM; achieved a 12% improvement on the Chinese benchmark (C-Eval) compared to the baseline."))
story.append(bullet("Designed and implemented a distributed training pipeline based on DeepSpeed ZeRO-3 + Megatron-LM, supporting 1024 A100-80G GPUs with 90%+ MFU."))
story.append(bullet("Built an online RLHF system with 1000+ QPS, including reward model, PPO training, and safety alignment modules."))
story.append(bullet("Developed a long-context extension solution (YaRN + NTK-aware scaling), extending the LLaMA model's context window from 4K to 128K tokens."))
story.append(bullet("Optimized the inference engine via FlashAttention-2, continuous batching, and INT8 quantization, reducing latency by 3x and cost by 60%."))
story.append(Spacer(1, 4))

# Job 2
story.append(sub_header("Algorithm Intern  @  Microsoft Research Asia (MSRA)", "Jun 2022 - Feb 2023"))
story.append(bullet("Researched efficient fine-tuning methods for LLMs; proposed an Adapter-based cross-lingual transfer approach, published at ACL 2023."))
story.append(bullet("Built a data-centric pipeline for instruction data construction (quality filtering, diversity sampling, decontamination), processing 10M+ samples."))
story.append(bullet("Implemented the Speculative Decoding algorithm, accelerating autoregressive generation by 2-3x without quality degradation."))
story.append(Spacer(1, 6))

# ── Projects ──
story.extend(section("Key Projects"))

story.append(sub_header("Large Model Reasoning Enhancement - 'ChainThought'", ""))
story.append(bullet("Collected and synthesized 500K+ Chain-of-Thought reasoning data; trained a 13B model using rejection sampling + DPO, achieving 15% gain on GSM8K and MATH."))
story.append(bullet("Designed a multi-agent debate and self-consistency mechanism, improving the accuracy of complex mathematical reasoning tasks to 78%."))
story.append(Spacer(1, 3))

story.append(sub_header("Multimodal Understanding Model - 'SeeThink'", ""))
story.append(bullet("Built a vision-language model based on Qwen-VL + CLIP, supporting image understanding, table / chart analysis, and document VQA."))
story.append(bullet("Used query-based cross-attention to fuse visual features, reducing the number of visual tokens by 70% while maintaining accuracy."))
story.append(Spacer(1, 6))

# ── Publications ──
story.extend(section("Publications & Patents"))
story.append(bullet("<b>Zhang M.</b>, et al. \"Cross-Adapter: Parameter-Efficient Cross-Lingual Transfer for LLMs.\" ACL 2023."))
story.append(bullet("<b>Zhang M.</b>, et al. \"Efficient Speculative Decoding with Dynamic Drafting.\" EMNLP 2023."))
story.append(bullet("Patent: \"A Distributed Training System Based on Hybrid Parallel Strategies\" (Patent No. CN2024XXXXXXX.1)"))
story.append(Spacer(1, 6))

# ── Honors ──
story.extend(section("Honors & Awards"))
story.append(bullet("National Scholarship for Graduate Students (top 2%), 2022"))
story.append(bullet("First Prize, ByteDance AI Competition - LLM Track, 2023"))
story.append(bullet("Outstanding Graduate of Beijing (Master's), 2023"))

# Build
doc.build(story)
print(f"PDF generated: {output_path}")
print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")
