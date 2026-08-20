import streamlit as st
from groq import Groq
import sys
import os
import re
import json
import time
from gtts import gTTS
import io
import PyPDF2
from PIL import Image
import base64
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from streamlit_mic_recorder import mic_recorder

# --- 1. اسٹریم لٹ پیج سیٹ اپ ---
st.set_page_config(
    page_title="EduGuide AI: Learning & Assessment Assistant",
    page_icon="🎓",
    layout="wide"
)

# --- 2. انکوڈنگ فکس ---
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- 3. سیشن اسٹیٹ کی ترتیب (بشمول لینگویج) ---
if "language" not in st.session_state:
    st.session_state.language = "Urdu" # بائی ڈیفالٹ اردو
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_total" not in st.session_state:
    st.session_state.quiz_total = 0
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""
if "dynamic_quizzes" not in st.session_state:
    st.session_state.dynamic_quizzes = []
if "flashcards_data" not in st.session_state:
    st.session_state.flashcards_data = []
if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = {}

# --- 🎨 CSS اور فونٹس (زبان کے مطابق RTL / LTR ڈائریکشن) ---
current_lang = st.session_state.language
text_direction = "rtl" if current_lang == "Urdu" else "ltr"
text_align = "right" if current_lang == "Urdu" else "left"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');

h1, h2, h3, h4, h5, h6, p, div:not([data-testid="stFileUploader"] *) {{
    font-family: {'\'Noto Nastaliq Urdu\', \'Jameel Noori Nastaliq\', sans-serif' if current_lang == 'Urdu' else '\'Segoe UI\', sans-serif'} !important;


/* ڈائنامک الائنمنٹ (اردو کے لیے RTL اور انگلش کے لیے LTR) */
.dynamic-text-box {{
    direction: {text_direction};
    text-align: {text_align};
}}

.stButton > button {{
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
}}

[data-testid="stFileUploader"] label {{
    display: none !important;
}}

[data-testid="stFileUploader"] section {{
    background-color: #ffffff !important;
    border: 2px dashed #198754 !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    min-height: 120px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.3s ease !important;
}}

[data-testid="stFileUploader"] section:hover {{
    border-color: #0d6efd !important;
    background-color: #f8f9fa !important;
}}

[data-testid="stFileUploader"] button {{
    background-color: #198754 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.2rem !important;
    font-family: 'Segoe UI', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
}}

[data-testid="stFileUploader"] button:hover {{
    background-color: #146c43 !important;
    color: white !important;
}}

[data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] p {{
    display: none !important;
}}

.flashcard-box {{
    background: linear-gradient(135deg, #ffffff, #f0fdf4);
    border: 1.5px solid #198754;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 4px 12px rgba(25, 135, 84, 0.08);
}}
.flashcard-title {{
    color: #198754;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
    border-bottom: 1px dashed #198754;
    padding-bottom: 4px;
}}
</style>
""", unsafe_allow_html=True)

# --- 4. Groq API Key حاصل کرنا ---
MY_GROQ_KEY = None
try:
    if "GROQ_API_KEY" in st.secrets:
        MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not MY_GROQ_KEY:
    MY_GROQ_KEY = os.getenv("GROQ_API_KEY", "YOUR_LOCAL_GROQ_KEY_HERE")

# --- 🎯 مددگار فنکشنز ---
def remove_foreign_characters(text):
    if not text:
        return ""
    if st.session_state.language == "English":
        return text.strip()
    pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\u0900-\u097f]+'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text.strip()

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.read().decode('utf-8')
    except Exception as e:
        err_msg = f"Error reading file: {str(e)}" if st.session_state.language == "English" else f"فائل پڑھنے میں مسئلہ آیا: {str(e)}"
        st.error(err_msg)
    return text

def generate_audio(text, lang_code):
    try:
        clean_speech_text = re.sub(r'[*#\_`~$]', '', text)
        tts = gTTS(text=clean_speech_text, lang=lang_code)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception:
        return None

def create_pdf_report(text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=10, leading=14)
    story = [Paragraph("EduGuide AI - Educational Report", styles['Heading1']), Spacer(1, 12)]
    
    clean_text = re.sub(r'[*#\_`~$]', '', text)
    
    for line in clean_text.split('\n'):
        line_clean = line.strip()
        if line_clean:
            safe_line = html.escape(line_clean)
            try:
                story.append(Paragraph(safe_line, style))
                story.append(Spacer(1, 6))
            except Exception:
                plain_safe = re.sub(r'[<>&]', '', line_clean)
                story.append(Paragraph(plain_safe, style))
                story.append(Spacer(1, 6))
                
    doc.build(story)
    buffer.seek(0)
    return buffer

def transcribe_audio(audio_bytes, lang_code):
    try:
        client = Groq(api_key=MY_GROQ_KEY)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "input_voice.wav"
        
        transcription = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3-turbo",
            language=lang_code
        )
        return transcription.text
    except Exception as e:
        err_msg = f"Audio processing error: {str(e)}" if st.session_state.language == "English" else f"آواز پروسیسنگ میں مسئلہ آیا: {str(e)}"
        st.error(err_msg)
        return None

# --- سائڈ بار ---
with st.sidebar:
    st.title("🚀 EduGuide AI")
    st.caption("Learning & Assessment Assistant")
    st.divider()
    
    # --- 🌐 انٹرنیشنل لینگویج ٹوگل بٹن ---
    st.subheader("🌐 Language / زبان")
    lang_btn_label = "Switch to English 🇺🇸" if st.session_state.language == "Urdu" else "اردو میں تبدیل کریں 🇵🇰"
    if st.button(lang_btn_label, use_container_width=True):
        st.session_state.language = "English" if st.session_state.language == "Urdu" else "Urdu"
        st.rerun()
        
    st.divider()
    st.subheader("🎨 تھیم اور نیٹ ورک سیٹ اپ" if st.session_state.language == "Urdu" else "🎨 Theme & Network Setup")
    alkhidmat_theme = st.toggle("🟢 الخدمت برانڈنگ تھیم (Green/Blue)" if st.session_state.language == "Urdu" else "🟢 Alkhidmat Branding Theme", value=True)
    low_bandwidth = st.toggle("⚡ لو بینڈوڈتھ / دیہاتی موڈ (2G Mode)" if st.session_state.language == "Urdu" else "⚡ Low Bandwidth / 2G Mode", value=False)
    socratic_mode = st.toggle("🧠 سقراطی استاد موڈ (Socratic Tutor)" if st.session_state.language == "Urdu" else "🧠 Socratic Tutor Mode", value=False)
    
    if alkhidmat_theme:
        st.markdown("""
        <style>
        .stApp { background-color: #f4f9f5; }
        h1, h2, h3 { color: #0d6efd !important; }
        .stButton > button { background-color: #198754 !important; color: white !important; }
        </style>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("🏛️ 1️⃣ تعلیمی بورڈ کی سلیکشن (Board)" if st.session_state.language == "Urdu" else "🏛️ 1️⃣ Educational Board")
    selected_board = st.selectbox(
        "اپنا تعلیمی بورڈ منتخب کریں:" if st.session_state.language == "Urdu" else "Select your Educational Board:",
        [
            "سندھ بورڈ (BIEK / BSEK Karachi)" if st.session_state.language == "Urdu" else "Sindh Board (BIEK / BSEK Karachi)",
            "پنجاب بورڈ (BISE Lahore / Rawalpindi etc.)" if st.session_state.language == "Urdu" else "Punjab Board (BISE Lahore / Rawalpindi etc.)",
            "فیڈرل بورڈ (FBISE Islamabad)" if st.session_state.language == "Urdu" else "Federal Board (FBISE Islamabad)",
            "آغا خان بورڈ (AKU-EB)" if st.session_state.language == "Urdu" else "Aga Khan Board (AKU-EB)",
            "O / A Levels (Cambridge System)" if st.session_state.language == "Urdu" else "O / A Levels (Cambridge System)",
            "عام / عمومی (General Education)" if st.session_state.language == "Urdu" else "General Education"
        ]
    )
    
    st.subheader("🎯 2️⃣ مضمون کا انتخاب (Subject)" if st.session_state.language == "Urdu" else "🎯 2️⃣ Subject Selection")
    selected_subject = st.selectbox(
        "اپنا متعلقہ مضمون منتخب کریں:" if st.session_state.language == "Urdu" else "Select your subject:",
        [
            "عمومی / دیگر (General)" if st.session_state.language == "Urdu" else "General / Other",
            "💻 کمپیوٹر سائنس / آئی ٹی" if st.session_state.language == "Urdu" else "💻 Computer Science / IT",
            "⚛️ فزکس (Physics)" if st.session_state.language == "Urdu" else "⚛️ Physics",
            "🧪 کیمسٹری (Chemistry)" if st.session_state.language == "Urdu" else "🧪 Chemistry",
            "🧬 بائیولوجی (Biology)" if st.session_state.language == "Urdu" else "🧬 Biology",
            "📐 ریاضی (Mathematics)" if st.session_state.language == "Urdu" else "📐 Mathematics",
            "📜 تاریخ / مطالعہ پاکستان / معلومات عامہ" if st.session_state.language == "Urdu" else "📜 History / Pakistan Studies / General Knowledge"
        ]
    )
    
    st.subheader("📊 3️⃣ سطح کا انتخاب (Difficulty)" if st.session_state.language == "Urdu" else "📊 3️⃣ Difficulty Level")
    selected_level = st.select_slider(
        "لیول منتخب کریں:" if st.session_state.language == "Urdu" else "Select level:",
        options=["ابتدائی (Primary/Middle)" if st.session_state.language == "Urdu" else "Primary/Middle", "میٹرک / انٹرمیڈیٹ (High School)" if st.session_state.language == "Urdu" else "High School", "یونیورسٹی / ایڈوانسڈ (Undergrad)" if st.session_state.language == "Urdu" else "Undergrad"],
        value="میٹرک / انٹرمیڈیٹ (High School)" if st.session_state.language == "Urdu" else "High School"
    )
    
    st.divider()
    st.subheader("📈 اسٹوڈنٹ پرفارمنس ڈیش بورڈ" if st.session_state.language == "Urdu" else "📈 Student Performance Dashboard")
    st.metric(label="کل پوچھے گئے سوالات" if st.session_state.language == "Urdu" else "Total Questions", value=st.session_state.total_questions)
    col_q1, col_q2 = st.columns(2)
    col_q1.metric(label="کوئز اسکور" if st.session_state.language == "Urdu" else "Quiz Score", value=st.session_state.quiz_score)
    col_q2.metric(label="کل کوئز" if st.session_state.language == "Urdu" else "Total Quiz", value=st.session_state.quiz_total)
    if st.session_state.quiz_total > 0:
        accuracy = int((st.session_state.quiz_score / st.session_state.quiz_total) * 100)
        st.progress(accuracy / 100, text=f"کوئز ایکوریسی: {accuracy}%" if st.session_state.language == "Urdu" else f"Quiz Accuracy: {accuracy}%")
    
    st.divider()
    st.subheader("🤝 معاون و سرپرست" if st.session_state.language == "Urdu" else "🤝 Supporters & Partners")
    st.markdown("""
    * 🌟 **الخدمت فاؤنڈیشن (Alkhidmat Foundation)**
    * 🚀 **بنو قابل 3.0 (Bano Qabil)**
    * ☁️ **علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026)**
    """)
    st.divider()
    st.write("👤 **ڈویلپر:** ارسلان مصطفیٰ (Arsalan Mustafa)" if st.session_state.language == "Urdu" else "👤 **Developer:** Arsalan Mustafa")
    st.write("🎓 AI & Software Development")

# --- DYNAMIC SYSTEM PROMPT ---
active_lang = st.session_state.language
lang_instruction = "All answers must be written in PURE, FLUENT URDU SCRIPT." if active_lang == "Urdu" else "All answers must be written in PURE, PROFESSIONAL, ACADEMIC ENGLISH."

socratic_instruction = ""
if socratic_mode:
    socratic_instruction = "\n🧠 Socratic Tutor Mode is active: Do not give direct complete solutions; instead, guide the student with leading questions and hints." if active_lang == "English" else "\n🧠 سقراطی طریقہ تدریس موڈ فعال ہے: طالب علم کو براہ راست حتمی جواب مت دیں بلکہ تعمیری رہنمائی والے سوالات پوچھیں۔"

SYSTEM_PROMPT = f"""
You are 'EduGuide AI', a smart educational assistant built for students.
This project is developed for Alkhidmat Foundation, Bano Qabil 3.0, and Alibaba Cloud AI Hackathon 2026.

Current Configuration:
- Language Mode: "{active_lang}" ({lang_instruction})
- Selected Board/Curriculum: "{selected_board}"
- Selected Subject: "{selected_subject}"
- Selected Level: "{selected_level}"

{socratic_instruction}

🛑 STRICT SUBJECT & LANGUAGE RULES:
1. Ensure responses strictly match the selected language ("{active_lang}").
2. If the user's query does not match the selected subject, reject it politely with a mismatch notice in "{active_lang}".
3. Keep formatting clean, precise, and structured.
"""

# --- مین انٹرفیس ---
if active_lang == "Urdu":
    st.title("🚀 EduGuide AI: Urdu Learning & Assessment Assistant")
    st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کا خصوصی پروجیکٹ**")
else:
    st.title("🚀 EduGuide AI: International Learning & Assessment Assistant")
    st.markdown("##### **Special Project for Alkhidmat Foundation, Bano Qabil & Alibaba Cloud Hackathon 2026**")

# --- AI کال کرنے کا فنکشن ---
def fetch_ai_response(prompt_text, img_data=None, custom_sys_prompt=None):
    if not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key is missing! Please configure your API key.")
        return None
    
    client = Groq(api_key=MY_GROQ_KEY)
    active_sys_prompt = custom_sys_prompt if custom_sys_prompt else SYSTEM_PROMPT

    text_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b"
    ]
    
    last_error_msg = None
    
    try:
        if img_data and not low_bandwidth:
            vision_models = ["llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"]
            for v_model in vision_models:
                try:
                    base64_img = encode_image(img_data)
                    messages = [
                        {"role": "system", "content": active_sys_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                            ]
                        }
                    ]
                    res = client.chat.completions.create(model=v_model, messages=messages, temperature=0.1)
                    return remove_foreign_characters(res.choices[0].message.content)
                except Exception as e:
                    last_error_msg = str(e)
                    time.sleep(1)
                    continue
            st.error(f"Vision processing failed: {last_error_msg}")
            return None
        
        for model_name in text_models:
            try:
                res = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": active_sys_prompt},
                        {"role": "user", "content": prompt_text}
                    ],
                    temperature=0.1
                )
                return remove_foreign_characters(res.choices[0].message.content)
            except Exception as e:
                last_error_msg = str(e)
                time.sleep(1)
                continue
                
        st.error(f"All AI requests failed. Last error: {last_error_msg}")
        return None
            
    except Exception as e:
        st.error(f"Connection or API error: {str(e)}")
        return None

# --- ڈائنامک کوئز جنریٹر ---
def generate_dynamic_quiz_data(topic_content):
    lang_instruction_json = "in Urdu" if active_lang == "Urdu" else "in English"
    quiz_sys_prompt = f"""You are an exam generator. Return strictly valid JSON array of 3 MCQs based on the topic {lang_instruction_json}.
Format:
[
  {{
    "question": "Question text",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct_index": 0,
    "explanation": "Short explanation of correct answer"
  }}
]
Only return raw JSON array."""
    
    quiz_prompt = f"Generate 3 MCQs {lang_instruction_json} based on this content:\n\n{topic_content}"
    res = fetch_ai_response(quiz_prompt, custom_sys_prompt=quiz_sys_prompt)
    if res:
        try:
            cleaned_json = res.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            return json.loads(cleaned_json)
        except Exception:
            return []
    return []

# --- فلیش کارڈز جنریٹر ---
def generate_flashcards_data(topic_content):
    lang_instruction_fc = "in Urdu" if active_lang == "Urdu" else "in English"
    fc_sys_prompt = f"""You are a revision card builder. Return strictly valid JSON array of 4 key revision flashcards {lang_instruction_fc}.
Format:
[
  {{
    "term": "Key term or concept",
    "definition": "Concise definition or summary"
  }}
]
Only return raw JSON array."""
    
    fc_prompt = f"Generate 4 revision flashcards {lang_instruction_fc} for this topic:\n\n{topic_content}"
    res = fetch_ai_response(fc_prompt, custom_sys_prompt=fc_sys_prompt)
    if res:
        try:
            cleaned_json = res.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            return json.loads(cleaned_json)
        except Exception:
            return []
    return []

# --- 📁 فائل، تصویر اور وائس ان پٹ ---
st.subheader("📄 File, Image or Voice Input:" if active_lang == "English" else "📄 فائل، تصویر یا وائس ان پٹ (اختیاری):")
tab_file, tab_voice = st.tabs(["📁 PDF / TXT / Image Upload" if active_lang == "English" else "📁 PDF / TXT / تصویر اپ لوڈ", "🎙️ Voice Query" if active_lang == "English" else "🎙️ صوتی سوال (Voice Query)"])

file_extracted_text = ""
image_bytes = None

with tab_file:
    uploaded_file = st.file_uploader(
        "",
        type=['pdf', 'txt', 'png', 'jpg', 'jpeg'],
        label_visibility="collapsed"
    )
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_bytes = uploaded_file.read()
            if not low_bandwidth:
                st.image(uploaded_file, caption="Uploaded Image" if active_lang == "English" else "اپ لوڈ کی گئی تصویر", width=350)
            st.success("Image uploaded successfully!" if active_lang == "English" else "تصویر کامیابی سے اپ لوڈ ہو گئی ہے!")
        else:
            file_extracted_text = extract_text_from_file(uploaded_file)
            if file_extracted_text:
                st.success(f"File '{uploaded_file.name}' read successfully!" if active_lang == "English" else f"فائل '{uploaded_file.name}' کامیابی سے پڑھ لی گئی ہے!")

with tab_voice:
    st.markdown('<div dir="ltr" style="text-align: left;">', unsafe_allow_html=True)
    st.write("🎙️ Click **Start Recording** to speak your query:" if active_lang == "English" else "🎙️ ریکارڈنگ شروع کرنے کے لیے **Start Recording** پر کلک کریں:")
    audio_data = mic_recorder(
        start_prompt="🔴 Start Recording",
        stop_prompt="⏹️ Stop Recording",
        key='custom_mic_recorder'
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if audio_data is not None:
        audio_bytes = audio_data['bytes']
        
        # ایک یونیک کیش چیک تاکہ ایک ہی آڈیو بار بار پروسیس نہ ہو
        audio_hash = hash(audio_bytes)
        if "last_processed_audio" not in st.session_state:
            st.session_state.last_processed_audio = None
            
        if st.session_state.last_processed_audio != audio_hash:
            st.session_state.last_processed_audio = audio_hash
            
            st.audio(audio_bytes, format='audio/wav')
            
            with st.spinner("Processing voice input..." if active_lang == "English" else "آواز کو ٹیکسٹ میں بدلا جا رہا ہے..."):
                lang_code_whisper = "ur" if active_lang == "Urdu" else "en"
                recognized_text = transcribe_audio(audio_bytes, lang_code_whisper)
                
                if recognized_text:
                    st.session_state.voice_text = recognized_text
                    st.success(f"🗣️ Recognized: **\"{recognized_text}\"**" if active_lang == "English" else f"🗣️ پہچان لیا گیا: **\"{recognized_text}\"**")
                    st.rerun()
# --- ان پٹ باکس ---
default_text = st.session_state.voice_text if st.session_state.voice_text else file_extracted_text
user_input = st.text_area(
    "Enter your educational question, topic or prompt here:" if active_lang == "English" else "اپنا تعلیمی سوال، ٹاپک یا ہدایت یہاں درج کریں:", 
    value=default_text,
    height=140,
    placeholder="Type your question or paste notes here..." if active_lang == "English" else "یہاں اپنا سوال، ریاضی کا فارمولا، یا نوٹس درج کریں..."
)

# --- 🚀 مرکزی جواب حاصل کرنے کا بٹن ---
btn_label = "🚀 Get Answer" if active_lang == "English" else "🚀 جواب حاصل کریں (Get Answer)"
if st.button(btn_label, use_container_width=True, type="primary"):
    clean_input_text = user_input.strip()
    
    if not clean_input_text and image_bytes is None:
        st.warning("Please enter a question or upload a file/image first!" if active_lang == "English" else "پہلے اپنا سوال درج کریں یا کوئی فائل/تصویر اپ لوڈ کریں!")
    else:
        with st.spinner('EduGuide AI is generating the answer...' if active_lang == "English" else 'EduGuide AI جواب تیار کر رہا ہے...'):
            main_prompt = f"Please provide a comprehensive answer in {active_lang} based on the curriculum for '{selected_board}', subject '{selected_subject}':\n\n{clean_input_text}"
            ans = fetch_ai_response(main_prompt, image_bytes)
            if ans:
                st.session_state.last_answer = ans
                st.session_state.total_questions += 1
                st.session_state.dynamic_quizzes = []
                st.session_state.flashcards_data = []
                st.session_state.quiz_state = {}

# --- 📋 جواب اور ایجوکیشنل AI ٹولز ---
if st.session_state.last_answer:
    st.divider()
    
    st.markdown("##### 🔊 Audio Response:" if active_lang == "English" else "##### 🔊 فوری آڈیو سنیں (Audio Response):")
    tts_lang_code = "ur" if active_lang == "Urdu" else "en"
    audio_fp_auto = generate_audio(st.session_state.last_answer[:600], tts_lang_code)
    if audio_fp_auto:
        st.audio(audio_fp_auto, format='audio/mp3')
    
    st.subheader("📋 EduGuide AI Response:" if active_lang == "English" else "📋 EduGuide AI کا تعلیمی جواب:")
    st.markdown(f'<div class="dynamic-text-box">{st.session_state.last_answer}</div>', unsafe_allow_html=True)
    
    if "Subject Mismatch" not in st.session_state.last_answer and "مضمون میں عدم مطابقت" not in st.session_state.last_answer:
        st.divider()
        st.subheader("🎓 Educational AI Tools:" if active_lang == "English" else "🎓 اس جواب پر مزید ایجوکیشنل AI ٹولز استعمال کریں:")
        
        r1_c1, r1_c2, r1_c3 = st.columns(3)
        r2_c1, r2_c2, r2_c3 = st.columns(3)
        r3_c1, r3_c2 = st.columns(2)
        
        tool_prompt = None
        
        with r1_c1:
            btn_t1 = "🔍 1. Simplify Explanation" if active_lang == "English" else "🔍 1. مزید آسان اردو میں سمجھائیں"
            if st.button(btn_t1, use_container_width=True):
                tool_prompt = f"Explain this simpler in {active_lang}:\n\n{st.session_state.last_answer}"
        
        with r1_c2:
            btn_t2 = "📅 2. AI Study Roadmap" if active_lang == "English" else "📅 2. AI اسٹڈی پلانر بنائیں"
            if st.button(btn_t2, use_container_width=True):
                tool_prompt = f"Create a 15-day study roadmap in {active_lang} for this topic:\n\n{st.session_state.last_answer}"
        
        with r1_c3:
            btn_t3 = "📝 3. Generate Model Paper" if active_lang == "English" else "📝 3. مکمل ماڈل پیپر جنریٹ کریں"
            if st.button(btn_t3, use_container_width=True):
                tool_prompt = f"Generate a model test paper with MCQs and short questions in {active_lang} based on:\n\n{st.session_state.last_answer}"
        
        with r2_c1:
            btn_t4 = "🧪 4. Step-by-Step Solution" if active_lang == "English" else "🧪 4. Step-by-Step فارمولا حل"
            if st.button(btn_t4, use_container_width=True):
                tool_prompt = f"Break down the formulas or concepts step-by-step in {active_lang}:\n\n{st.session_state.last_answer}"
        
        with r2_c2:
            btn_t5 = "💡 5. Socratic Hint" if active_lang == "English" else "💡 5. سوچنے کے لیے اشارہ (Hint) دیں"
            if st.button(btn_t5, use_container_width=True):
                tool_prompt = f"Provide a guiding hint or question in {active_lang} to test the student:\n\n{st.session_state.last_answer}"
        
        with r2_c3:
            btn_t6 = "🔤 6. Technical Glossary" if active_lang == "English" else "🔤 6. اہم تکنیکی الفاظ کی لغت"
            if st.button(btn_t6, use_container_width=True):
                tool_prompt = f"List key technical terms and definitions in {active_lang} from:\n\n{st.session_state.last_answer}"

        with r3_c1:
            btn_t7 = "📜 7. Past Papers Focus" if active_lang == "English" else "📜 7. پاسٹ پیپرز اینالیٹکس"
            if st.button(btn_t7, use_container_width=True):
                tool_prompt = f"Analyze past paper importance for this topic in {active_lang}:\n\n{st.session_state.last_answer}"

        with r3_c2:
            btn_t8 = "🎮 8. Gamified Quiz Mode" if active_lang == "English" else "🎮 8. فارم بائیٹ کوئز گیم"
            if st.button(btn_t8, use_container_width=True):
                tool_prompt = f"Create a 3-question MCQ quiz in {active_lang} with answer key based on:\n\n{st.session_state.last_answer}"

        if tool_prompt:
            with st.spinner('Processing tool request...' if active_lang == "English" else 'EduGuide AI منتخب کردہ ٹول کا پروسیس چلا رہا ہے...'):
                processed_ans = fetch_ai_response(tool_prompt, image_bytes)
                if processed_ans:
                    st.session_state.last_answer = processed_ans
                    st.rerun()

        # --- فلیش کارڈز UI ---
        st.divider()
        st.subheader("🎴 Smart Revision Flashcards" if active_lang == "English" else "🎴 کسٹم اسمارٹ فلیش کارڈز (Quick Revision Cards)")
        fc_btn_text = "⚡ Generate Flashcards" if active_lang == "English" else "⚡ اس ٹاپک کے ریویژن فلیش کارڈز تیار کریں"
        if st.button(fc_btn_text, use_container_width=True):
            with st.spinner("Building flashcards..." if active_lang == "English" else "EduGuide AI فلیش کارڈز تیار کر رہا ہے..."):
                fcs = generate_flashcards_data(st.session_state.last_answer)
                if fcs:
                    st.session_state.flashcards_data = fcs

        if st.session_state.flashcards_data:
            fc_cols = st.columns(len(st.session_state.flashcards_data))
            for idx, card in enumerate(st.session_state.flashcards_data):
                with fc_cols[idx]:
                    st.markdown(f"""
                    <div class="flashcard-box dynamic-text-box">
                        <div class="flashcard-title">📌 {card.get('term', f'Card {idx+1}')}</div>
                        <p style="font-size: 14px; color: #333;">{card.get('definition', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)

        # --- ڈائنامک کوئز UI ---
        st.divider()
        st.subheader("🎯 Dynamic AI Quiz Engine" if active_lang == "English" else "🎯 ڈائنامک AI کوئز انجن (رئیل ٹائم اسسمنٹ)")
        quiz_btn_text = "🔄 Generate Live Quiz" if active_lang == "English" else "🔄 موجودہ ٹاپک سے لائیو ٹیسٹ بنائیں"
        if st.button(quiz_btn_text, use_container_width=True):
            with st.spinner("Generating fresh MCQs..." if active_lang == "English" else "AI اسی ٹاپک کے 3 فریش سوالات تیار کر رہا ہے..."):
                quiz_data = generate_dynamic_quiz_data(st.session_state.last_answer)
                if quiz_data:
                    st.session_state.dynamic_quizzes = quiz_data
                    st.session_state.quiz_state = {}
                else:
                    st.error("Failed to generate quiz. Try again." if active_lang == "English" else "کوئز تیار نہیں ہو سکا۔ دوبارہ کلک کریں۔")

        if st.session_state.dynamic_quizzes:
            st.markdown("##### 📝 Solve questions and view instant score:" if active_lang == "English" else "##### 📝 سوالات حل کریں اور فوری رزلٹ دیکھیں:")
            for q_idx, q in enumerate(st.session_state.dynamic_quizzes):
                q_key = f"quiz_{q_idx}"
                options = q.get('options', [])
                correct_idx = q.get('correct_index', 0)
                
                if q_key not in st.session_state.quiz_state:
                    st.session_state.quiz_state[q_key] = {
                        "submitted": False,
                        "is_correct": False,
                        "selected_idx": 0
                    }
                
                q_state = st.session_state.quiz_state[q_key]
                st.markdown(f'<div class="dynamic-text-box"><strong>Q{q_idx + 1}: {q.get("question")}</strong></div>', unsafe_allow_html=True)
                
                user_choice = st.radio(
                    f"Select option (Q{q_idx+1}):", 
                    options, 
                    index=q_state["selected_idx"],
                    key=f"dyn_q_{q_idx}", 
                    label_visibility="collapsed",
                    disabled=q_state["submitted"]
                )
                
                if not q_state["submitted"]:
                    check_btn_lbl = f"Check Answer (Q{q_idx + 1})" if active_lang == "English" else f"سوال {q_idx + 1} کا جواب چیک کریں"
                    if st.button(check_btn_lbl, key=f"dyn_btn_{q_idx}"):
                        chosen_idx = options.index(user_choice)
                        is_correct = (chosen_idx == correct_idx)
                        
                        q_state["submitted"] = True
                        q_state["selected_idx"] = chosen_idx
                        q_state["is_correct"] = is_correct
                        
                        st.session_state.quiz_total += 1
                        if is_correct:
                            st.session_state.quiz_score += 1
                        st.rerun()
                else:
                    if q_state["is_correct"]:
                        success_msg = f"🎉 Correct! {q.get('explanation', '')}" if active_lang == "English" else f"🎉 بالکل درست! {q.get('explanation', '')}"
                        st.success(success_msg)
                    else:
                        err_msg = f"❌ Incorrect! You chose '{options[q_state['selected_idx']]}'. Correct was: '{options[correct_idx]}' | Explanation: {q.get('explanation', '')}" if active_lang == "English" else f"❌ غلط جواب! آپ نے '{options[q_state['selected_idx']]}' منتخب کیا۔ درست آپشن تھا: '{options[correct_idx]}' | وضاحت: {q.get('explanation', '')}"
                        st.error(err_msg)
                
                st.write("---")

    # --- 🚀 ڈاؤن لوڈ اور ایکسپورٹ ٹولز ---
    st.divider()
    st.subheader("🛠️ Export Tools:" if active_lang == "English" else "🛠️ اضافی ٹولز (Extra Features):")
    
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    
    with feat_col1:
        st.markdown("##### 🔊 Full Audio:" if active_lang == "English" else "##### 🔊 مکمل آڈیو سنیں:")
        audio_fp = generate_audio(st.session_state.last_answer, tts_lang_code)
        if audio_fp:
            st.audio(audio_fp, format='audio/mp3')
    
    with feat_col2:
        st.markdown("##### 📥 Text Download:" if active_lang == "English" else "##### 📥 ٹیکسٹ ڈاؤن لوڈ:")
        st.download_button(
            label="📄 Download Response (.txt)" if active_lang == "English" else "📄 جواب (.txt) ڈاؤن لوڈ کریں",
            data=st.session_state.last_answer,
            file_name="EduGuide_AI_Response.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with feat_col3:
        st.markdown("##### 📄 PDF Report:" if active_lang == "English" else "##### 📄 PDF پورٹل ایکسپورٹ:")
        pdf_file = create_pdf_report(st.session_state.last_answer)
        st.download_button(
            label="📕 Download PDF Report" if active_lang == "English" else "📕 PDF رپورٹ ڈاؤن لوڈ کریں",
            data=pdf_file,
            file_name="EduGuide_AI_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.code(st.session_state.last_answer, language=None)

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Learning & Assessment Assistant | Developed by Arsalan Mustafa for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")
