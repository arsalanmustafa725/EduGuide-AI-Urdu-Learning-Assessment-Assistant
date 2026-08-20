import streamlit as st
from groq import Groq
import sys
import os
import re
import json
from gtts import gTTS
import io
import PyPDF2
from PIL import Image
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from streamlit_mic_recorder import mic_recorder

# --- 1. اسٹریم لٹ پیج سیٹ اپ ---
st.set_page_config(
    page_title="EduGuide AI: Urdu Learning & Assessment Assistant",
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

# --- 🎨 CSS اور اردو فونٹس ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');

h1, h2, h3, h4, h5, h6, p, div:not([data-testid="stFileUploader"] *) {
    font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaliq', 'Segoe UI', sans-serif !important;
}

.stButton > button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
}

[data-testid="stFileUploader"] label {
    display: none !important;
}

[data-testid="stFileUploader"] section {
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
}

[data-testid="stFileUploader"] section:hover {
    border-color: #0d6efd !important;
    background-color: #f8f9fa !important;
}

[data-testid="stFileUploader"] button {
    background-color: #198754 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.2rem !important;
    font-family: 'Segoe UI', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
}

[data-testid="stFileUploader"] button:hover {
    background-color: #146c43 !important;
    color: white !important;
}

[data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] p {
    display: none !important;
}

.flashcard-box {
    background: linear-gradient(135deg, #ffffff, #f0fdf4);
    border: 1.5px solid #198754;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 4px 12px rgba(25, 135, 84, 0.08);
}
.flashcard-title {
    color: #198754;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
    border-bottom: 1px dashed #198754;
    padding-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# --- 3. Groq API Key حاصل کرنا ---
MY_GROQ_KEY = None
try:
    if "GROQ_API_KEY" in st.secrets:
        MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not MY_GROQ_KEY:
    MY_GROQ_KEY = os.getenv("GROQ_API_KEY", "YOUR_LOCAL_GROQ_KEY_HERE")

# --- 4. سیشن سٹیٹ ---
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

# --- 🎯 مددگار فنکشنز ---
def remove_foreign_characters(text):
    if not text:
        return ""
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
        st.error(f"فائل پڑھنے میں مسئلہ آیا: {str(e)}")
    return text

def generate_urdu_audio(text):
    try:
        clean_speech_text = re.sub(r'[*#\_`~$]', '', text)
        tts = gTTS(text=clean_speech_text, lang='ur')
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
    story = [Paragraph("EduGuide AI Urdu - Educational Report", styles['Heading1']), Spacer(1, 12)]
    clean_text = re.sub(r'[*#\_`~$]', '', text)
    for line in clean_text.split('\n'):
        if line.strip():
            story.append(Paragraph(line, style))
            story.append(Spacer(1, 6))
    doc.build(story)
    buffer.seek(0)
    return buffer

def transcribe_urdu_audio(audio_bytes):
    try:
        client = Groq(api_key=MY_GROQ_KEY)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "input_voice.wav"
        
        transcription = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3-turbo",
            language="ur"
        )
        return transcription.text
    except Exception as e:
        st.error(f"آواز پروسیسنگ میں مسئلہ آیا: {str(e)}")
        return None

# --- سائڈ بار ---
with st.sidebar:
    st.title("🚀 EduGuide AI Urdu")
    st.caption("Urdu Learning & Assessment Assistant")
    st.divider()
    
    st.subheader("🎨 تھیم اور نیٹ ورک سیٹ اپ")
    alkhidmat_theme = st.toggle("🟢 الخدمت برانڈنگ تھیم (Green/Blue)", value=True)
    low_bandwidth = st.toggle("⚡ لو بینڈوڈتھ / دیہاتی موڈ (2G Mode)", value=False)
    socratic_mode = st.toggle("🧠 سقراطی استاد موڈ (Socratic Tutor)", value=False, help="بنا بنایا حل دینے کے بجائے طالب علم کی سوچ بیدار کرنے کے لیے سوالیہ اشارے فراہم کرتا ہے۔")
    
    if alkhidmat_theme:
        st.markdown("""
        <style>
        .stApp { background-color: #f4f9f5; }
        h1, h2, h3 { color: #0d6efd !important; }
        .stButton > button { background-color: #198754 !important; color: white !important; }
        </style>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("🏛️ 1️⃣ تعلیمی بورڈ کی سلیکشن (Board)")
    selected_board = st.selectbox(
        "اپنا تعلیمی بورڈ منتخب کریں:",
        [
            "سندھ بورڈ (BIEK / BSEK Karachi)",
            "پنجاب بورڈ (BISE Lahore / Rawalpindi etc.)",
            "فیڈرل بورڈ (FBISE Islamabad)",
            "آغا خان بورڈ (AKU-EB)",
            "O / A Levels (Cambridge System)",
            "عام / عمومی (General Education)"
        ]
    )
    
    st.subheader("🎯 2️⃣ مضمون کا انتخاب (Subject)")
    selected_subject = st.selectbox(
        "اپنا متعلقہ مضمون منتخب کریں:",
        [
            "عمومی / دیگر (General)",
            "💻 کمپیوٹر سائنس / آئی ٹی",
            "⚛️ فزکس (Physics)",
            "🧪 کیمسٹری (Chemistry)",
            "🧬 بائیولوجی (Biology)",
            "📐 ریاضی (Mathematics)",
            "📜 تاریخ / مطالعہ پاکستان / معلومات عامہ"
        ]
    )
    
    st.subheader("📊 3️⃣ سطح کا انتخاب (Difficulty)")
    selected_level = st.select_slider(
        "لیول منتخب کریں:",
        options=["ابتدائی (Primary/Middle)", "میٹرک / انٹرمیڈیٹ (High School)", "یونیورسٹی / ایڈوانسڈ (Undergrad)"],
        value="میٹرک / انٹرمیڈیٹ (High School)"
    )
    
    st.divider()
    st.subheader("📈 اسٹوڈنٹ پرفارمنس ڈیش بورڈ")
    st.metric(label="کل پوچھے گئے سوالات", value=st.session_state.total_questions)
    col_q1, col_q2 = st.columns(2)
    col_q1.metric(label="کوئز اسکور", value=st.session_state.quiz_score)
    col_q2.metric(label="کل کوئز", value=st.session_state.quiz_total)
    if st.session_state.quiz_total > 0:
        accuracy = int((st.session_state.quiz_score / st.session_state.quiz_total) * 100)
        st.progress(accuracy / 100, text=f"کوئز ایکوریسی: {accuracy}%")
    
    st.divider()
    st.subheader("🤝 معاون و سرپرست")
    st.markdown("""
    * 🌟 **الخدمت فاؤنڈیشن (Alkhidmat Foundation)**
    * 🚀 **بنو قابل 3.0 (Bano Qabil)**
    * ☁️ **علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026)**
    """)
    st.divider()
    st.write("👤 **ڈویلپر:** ارسلان (Arsalan)")
    st.write("🎓 AI & Software Development")

# --- dynamic SYSTEM PROMPT ---
socratic_instruction = ""
if socratic_mode:
    socratic_instruction = """
🧠 **سقراطی طریقہ تدریس موڈ فعال ہے (SOCRATIC TUTOR MODE ACTIVE):**
- طالب علم کو براہ راست بنا بنایا مکمل حل یا حتمی جواب مت دیں۔
- اس کے بجائے، اہم تصور کی ایک سطر وضاحت کریں، پھر طالب علم سے ایک تعمیری رہنمائی والا سوال (Guiding/Leading Question) یا اشارہ (Hint) پوچھیں تاکہ وہ خود صحیح نتیجے پر پہنچے۔
"""

SYSTEM_PROMPT = f"""
تمہارا نام 'EduGuide AI' ہے۔ تم پاکستان کے طلباء کے لیے ایک انتہائی محتاط اور سمارٹ AI تعلیمی معاون ہو۔
یہ پروجیکٹ الخدمت فاؤنڈیشن، بنو قابل (Bano Qabil 3.0) اور علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026) کے لیے تیار کیا گیا ہے۔

موجودہ سیشن کی معلومات:
- منتخب کردہ بورڈ/نصاب: "{selected_board}"
- منتخب کردہ مضمون: "{selected_subject}"
- منتخب کردہ تعلیمی لیول: "{selected_level}"

{socratic_instruction}

🛑 **سخت ترین مضمون کی وریفیکیشن کے قواعد (STRICT SUBJECT MATCH RULE):**
1. اگر منتخب کردہ مضمون 'عمومی / دیگر (General)' کے علاوہ کوئی مخصوص مضمون ہے، تو سب سے پہلے صارف کے دیے گئے متن/سوال/تصویر کی جانچ کرو۔
2. اگر صارف کا سوال چنے گئے مضمون سے تعلق **نہیں** رکھتا، تو تم **ہرگز سوال کا جواب نہیں دو گے**۔
3. عدم مطابقت (Mismatch) کی صورت میں صرف یہ پیغام دو:
   "⚠️ **مضمون میں عدم مطابقت (Subject Mismatch)!**
   آپ نے سائڈ بار میں '**{selected_subject}**' منتخب کیا ہے، جبکہ آپ کا سوال کسی اور مضمون سے متعلق ہے۔ براہِ کرم درست مضمون چوئس کریں۔"

📜 **سخت ترین تحریری و زبان کے قواعد:**
1. تمام جوابات **صرف اور صرف خالص اور سلیس اردو رسم الخط (Urdu Script)** میں ہونے چاہئیں۔
2. ریاضیاتی یا سائنسی مساوات کے لیے مناسب فارمیٹ یا LaTeX فارمیٹ استعمال کریں تاکہ آسانی سے سمجھا جا سکے۔
3. تمام جوابات بالکل منتخب کردہ بورڈ ("{selected_board}") کے پیٹرن اور نصاب کے مطابق تیار کرو۔
4. جواب میں کوئی اضافی، فضول یا غیر متعلقہ جملے شامل نہ کرو۔
5. جب بھی ممکن ہو، تکنیکی انگریزی الفاظ کا اردو ترجمہ **"🔤 اہم تکنیکی الفاظ (Glossary)"** کی ہیڈنگ کے ساتھ لازمی بنائیں۔
"""

# --- مین انٹرفیس ---
st.title("🚀 EduGuide AI: Urdu Learning & Assessment Assistant")
st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کا خصوصی پروجیکٹ**")

# --- AI کال کرنے کا فنکشن ---
def fetch_ai_response(prompt_text, img_data=None, custom_sys_prompt=None):
    if not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key غائب ہے! براہ کرم اپنی درست API Key درج کریں۔")
        return None
    
    client = Groq(api_key=MY_GROQ_KEY)
    active_sys_prompt = custom_sys_prompt if custom_sys_prompt else SYSTEM_PROMPT

   text_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "meta-llama/llama-guard-3-8b",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    last_error_msg = None
    
    try:
        # اگر تصویر ہو تو وژن ماڈل
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
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                                }
                            ]
                        }
                    ]
                    res = client.chat.completions.create(
                        model=v_model,
                        messages=messages,
                        temperature=0.1
                    )
                    raw_answer = res.choices[0].message.content
                    return remove_foreign_characters(raw_answer)
                except Exception as e:
                    last_error_msg = str(e)
                    continue
            st.error(f"تصویر پروسیسنگ میں مسئلہ آیا یا ماڈل لمٹ ختم ہے۔ تفصیل: {last_error_msg}")
            return None 
        
        # اگر ٹیکسٹ سوال ہو تو فال بیک چین
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
                raw_answer = res.choices[0].message.content
                return remove_foreign_characters(raw_answer)
            except Exception as e:
                last_error_msg = str(e)
                continue
                
        st.error(f"تمام AI ماڈلز کی درخواستیں ناکام ہو گئیں یا لمٹ ختم ہے۔ آخری مسئلہ: {last_error_msg}")
        return None
            
    except Exception as e:
        st.error(f"کنکشن یا API کا مسئلہ ہے: {str(e)}")
        return None

# --- ڈائنامک کوئز جنریٹر فنکشن ---
def generate_dynamic_quiz_data(topic_content):
    quiz_sys_prompt = """You are an exam generator. Return strictly valid JSON array of 3 MCQs based on the topic.
Format:
[
  {
    "question": "اردو میں سوال",
    "options": ["آپشن ۱", "آپشن ۲", "آپشن ۳", "آپشن ۴"],
    "correct_index": 0,
    "explanation": "اردو میں درست جواب کی مختصر وضاحت"
  }
]
Do not include markdown blocks or any other commentary, only the raw JSON array."""
    
    quiz_prompt = f"Generate 3 MCQs in Urdu based on this content:\n\n{topic_content}"
    res = fetch_ai_response(quiz_prompt, custom_sys_prompt=quiz_sys_prompt)
    if res:
        try:
            cleaned_json = res.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            data = json.loads(cleaned_json)
            return data
        except Exception:
            return []
    return []

# --- فلیش کارڈز جنریٹر فنکشن ---
def generate_flashcards_data(topic_content):
    fc_sys_prompt = """You are a revision card builder. Return strictly valid JSON array of 4 key revision flashcards in Urdu.
Format:
[
  {
    "term": "اصطلاح یا بنیادی تصور",
    "definition": "ایک یا دو سطروں میں انتہائی اہم تعریف یا خلاصہ"
  }
]
Only return raw JSON array."""
    
    fc_prompt = f"Generate 4 revision flashcards in Urdu for this topic:\n\n{topic_content}"
    res = fetch_ai_response(fc_prompt, custom_sys_prompt=fc_sys_prompt)
    if res:
        try:
            cleaned_json = res.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            data = json.loads(cleaned_json)
            return data
        except Exception:
            return []
    return []

# --- 📁 فائل، تصویر اور وائس ان پٹ ---
st.subheader("📄 فائل، تصویر یا وائس ان پٹ (اختیاری):")
tab_file, tab_voice = st.tabs(["📁 PDF / TXT / تصویر اپ لوڈ", "🎙️ اردو صوتی سوال (Voice Query)"])

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
                st.image(uploaded_file, caption="اپ لوڈ کی گئی تصویر", width=350)
            st.success("تصویر کامیابی سے اپ لوڈ ہو گئی ہے!")
        else:
            file_extracted_text = extract_text_from_file(uploaded_file)
            if file_extracted_text:
                st.success(f"فائل '{uploaded_file.name}' کامیابی سے پڑھ لی گئی ہے!")

with tab_voice:
    st.write("🎙️ ریکارڈنگ شروع کرنے کے لیے **Start Recording** اور ختم کرنے کے لیے **Stop** پر کلک کریں:")
    
    audio_data = mic_recorder(
        start_prompt="🔴 Start Recording",
        stop_prompt="⏹️ Stop Recording",
        key='custom_mic_recorder'
    )
    
    if audio_data is not None:
        audio_bytes = audio_data['bytes']
        st.audio(audio_bytes, format='audio/wav')
        
        with st.spinner("EduGuide AI آپ کی آواز کو ٹیکسٹ میں بدل رہا ہے..."):
            recognized_text = transcribe_urdu_audio(audio_bytes)
            
            if recognized_text:
                st.session_state.voice_text = recognized_text
                st.success(f"🗣️ AI نے آپ کا سوال سن لیا: **\"{recognized_text}\"**")
                
                with st.spinner("جواب تیار کیا جا رہا ہے..."):
                    main_prompt = f"برائے مہربانی {selected_board} کے نصاب کے مطابق درج ذیل صوتی سوال کا سلیس اردو میں تفصیلی اور جامع جواب دیں:\n\n{recognized_text}"
                    ans = fetch_ai_response(main_prompt)
                    if ans:
                        st.session_state.last_answer = ans
                        st.session_state.total_questions += 1
                        st.session_state.dynamic_quizzes = []
                        st.session_state.flashcards_data = []
                        st.rerun()
            else:
                st.error("آواز واضح نہیں تھی یا پروسیسنگ میں مسئلہ آیا۔ دوبارہ کوشش کریں۔")

# --- ان پٹ باکس ---
default_text = st.session_state.voice_text if st.session_state.voice_text else file_extracted_text
user_input = st.text_area(
    "اپنا تعلیمی سوال، ٹاپک یا ہدایت یہاں درج کریں:", 
    value=default_text,
    height=140,
    placeholder="یہاں اپنا سوال، ریاضی کا فارمولا، یا نوٹس درج کریں..."
)

# --- 🚀 مرکزی جواب حاصل کرنے کا بٹن ---
if st.button("🚀 جواب حاصل کریں (Get Answer)", use_container_width=True, type="primary"):
    clean_input_text = user_input.strip()
    
    if not clean_input_text and image_bytes is None:
        st.warning("پہلے ٹیکسٹ باکس میں اپنا سوال درج کریں یا کوئی فائل/تصویر/آواز اپ لوڈ کریں!")
    else:
        with st.spinner('EduGuide AI جواب تیار کر رہا ہے...'):
            math_visual_instruction = ""
            if image_bytes is not None:
                math_visual_instruction = "\nنوٹ: اگر تصویر میں ریاضی یا سائنس کا کوئی نیومیریکل/مساوات ہے، تو اسے Step 1 (فارمولا)، Step 2 (ویلیوز کا اندراج)، اور Step 3 (حتمی جواب بمعہ یونٹ) کے ساتھ واضح باکسز اور LaTeX میں حل کریں۔"
            
            main_prompt = f"برائے مہربانی {selected_board} کے نصاب کے مطابق درج ذیل سوال/ٹاپک کا سلیس اردو میں تفصیلی اور جامع جواب دیں:{math_visual_instruction}\n\n{clean_input_text}"
            ans = fetch_ai_response(main_prompt, image_bytes)
            if ans:
                st.session_state.last_answer = ans
                st.session_state.total_questions += 1
                st.session_state.dynamic_quizzes = []
                st.session_state.flashcards_data = []

# --- 📋 جواب اور ایجوکیشنل AI ٹولز کا ڈسپلے ---
if st.session_state.last_answer:
    st.divider()
    
    st.markdown("##### 🔊 فوری آڈیو سنیں (Audio Response):")
    audio_fp_auto = generate_urdu_audio(st.session_state.last_answer[:600])
    if audio_fp_auto:
        st.audio(audio_fp_auto, format='audio/mp3')
    
    st.subheader("📋 EduGuide AI کا تعلیمی جواب:")
    st.markdown(st.session_state.last_answer)
    
    if "مضمون میں عدم مطابقت" not in st.session_state.last_answer:
        st.divider()
        st.subheader("🎓 اس جواب پر مزید ایجوکیشنل AI ٹولز استعمال کریں:")
        
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        row3_col1, row3_col2 = st.columns(2)
        
        tool_prompt = None
        
        with row1_col1:
            if st.button("🔍 1. مزید آسان اردو میں سمجھائیں", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس جواب کو اور زیادہ سادہ، عام فہم اور روزمرہ کی آسان مثالوں میں دوبارہ لکھیں:\n\n{st.session_state.last_answer}"
        
        with row1_col2:
            if st.button("📅 2. AI اسٹڈی پلانر بنائیں", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس تعلیمی جواب اور مضمون کی روشنی میں {selected_board} کے امتحان کی تیاری کا ایک منظم 15 دن کا اسٹڈی پلانر (Study Roadmap) تیار کریں:\n\n{st.session_state.last_answer}"
        
        with row1_col3:
            if st.button("📝 3. مکمل ماڈل پیپر جنریٹ کریں", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس حاصل شدہ جواب کے ٹاپک پر {selected_board} کے ایگزام پیٹرن کے مطابق ایک مکمل ماڈل پیپر بنائیں جس میں 10 MCQs، 5 مختصر سوالات اور 2 تفصیلی سوالات ماڈل اردو جوابات کے ساتھ شامل ہوں:\n\n{st.session_state.last_answer}"
        
        with row2_col1:
            if st.button("🧪 4. Step-by-Step فارمولا حل", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس جواب میں موجود تمام فارمولوں یا ریاضی/فزکس کے مسائل کو Step 1 (دی گئی معلومات و فارمولا)، Step 2 (حل و مساوات)، اور Step 3 (حتمی جواب) کے طور پر واضح اور تفصیلی حل کریں:\n\n{st.session_state.last_answer}"
        
        with row2_col2:
            if st.button("💡 5. سوچنے کے لیے اشارہ (Hint) دیں", use_container_width=True):
                tool_prompt = f"اس جواب کی بنیاد پر طالب علم سے ایک سوال پوچھیں اور ساتھ میں ایک چھوٹا اشارہ (Hint) دیں تاکہ طالب علم خود سوچ کر جواب دینے کی کوشش کرے:\n\n{st.session_state.last_answer}"
        
        with row2_col3:
            if st.button("🔤 6. اہم تکنیکی الفاظ کی لغت", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس جواب میں آنے والی تمام مشکل انگریزی و سائنس کی اصطلاحات کی ایک علیحدہ اردو لغت (Glossary) بمعہ تشریح بنائیں:\n\n{st.session_state.last_answer}"
        
        with row3_col1:
            if st.button("📜 7. پاسٹ پیپرز اینالیٹکس (Past Papers Focus)", use_container_width=True):
                tool_prompt = f"برائے مہربانی {selected_board} کے گزشتہ 5 سالہ پاسٹ پیپرز کے رجحانات کا تجزیہ کریں اور بتائیں کہ اس ٹاپک سے کون سے سوالات بار بار آئے ہیں:\n\n{st.session_state.last_answer}"

        with row3_col2:
            if st.button("🎮 8. فارم بائیٹ کوئز گیم (Gamified Quiz Mode)", use_container_width=True):
                tool_prompt = f"اس جواب کی بنیاد پر ایک 3 سوالات کا انٹرایکٹو اردو کوئز تیار کریں جس میں ہر سوال کے 4 اختیارات واضح لکھے ہوں اور آخر میں جواب کی کنجی (Answer Key) بھی دی گئی ہو:\n\n{st.session_state.last_answer}"

        if tool_prompt:
            with st.spinner('EduGuide AI منتخب کردہ ٹول کا پروسیس چلا رہا ہے...'):
                processed_ans = fetch_ai_response(tool_prompt, image_bytes)
                if processed_ans:
                    st.session_state.last_answer = processed_ans
                    st.rerun()

        # --- فلیش کارڈز UI ---
        st.divider()
        st.subheader("🎴 کسٹم اسمارٹ فلیش کارڈز (Quick Revision Cards)")
        if st.button("⚡ اس ٹاپک کے ریویژن فلیش کارڈز تیار کریں", use_container_width=True):
            with st.spinner("EduGuide AI فلیش کارڈز تیار کر رہا ہے..."):
                fcs = generate_flashcards_data(st.session_state.last_answer)
                if fcs:
                    st.session_state.flashcards_data = fcs

        if st.session_state.flashcards_data:
            fc_cols = st.columns(len(st.session_state.flashcards_data))
            for idx, card in enumerate(st.session_state.flashcards_data):
                with fc_cols[idx]:
                    st.markdown(f"""
                    <div class="flashcard-box">
                        <div class="flashcard-title">📌 {card.get('term', f'کارڈ {idx+1}')}</div>
                        <p style="font-size: 14px; color: #333;">{card.get('definition', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)

        # --- ڈائنامک کوئز UI ---
        st.divider()
        st.subheader("🎯 ڈائنامک AI کوئز انجن (رئیل ٹائم اسسمنٹ)")
        if st.button("🔄 موجودہ ٹاپک سے لائیو ٹیسٹ بنائیں (Generate Dynamic Quiz)", use_container_width=True):
            with st.spinner("AI اسی ٹاپک کے 3 فریش سوالات تیار کر رہا ہے..."):
                quiz_data = generate_dynamic_quiz_data(st.session_state.last_answer)
                if quiz_data:
                    st.session_state.dynamic_quizzes = quiz_data
                else:
                    st.error("کوئز تیار نہیں ہو سکا۔ دوبارہ کلک کریں۔")

        if st.session_state.dynamic_quizzes:
            st.markdown("##### 📝 سوالات حل کریں اور فوری رزلٹ دیکھیں:")
            for q_idx, q in enumerate(st.session_state.dynamic_quizzes):
                st.markdown(f"**سوال {q_idx + 1}: {q.get('question')}**")
                options = q.get('options', [])
                user_choice = st.radio(
                    f"آپشن منتخب کریں (سوال {q_idx+1}):", 
                    options, 
                    key=f"dyn_q_{q_idx}", 
                    label_visibility="collapsed"
                )
                
                if st.button(f"سوال {q_idx + 1} کا جواب چیک کریں", key=f"dyn_btn_{q_idx}"):
                    correct_idx = q.get('correct_index', 0)
                    st.session_state.quiz_total += 1
                    if options.index(user_choice) == correct_idx:
                        st.success(f"🎉 بالکل درست! {q.get('explanation', '')}")
                        st.session_state.quiz_score += 1
                    else:
                        st.error(f"❌ غلط جواب! صحیح آپشن تھا: '{options[correct_idx]}' | وضاحت: {q.get('explanation', '')}")
                st.write("---")

    # --- 🚀 اضافی ٹولز ---
    st.divider()
    st.subheader("🛠️ اضافی ٹولز (Extra Features):")
    
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    
    with feat_col1:
        st.markdown("##### 🔊 مکمل آڈیو سنیں:")
        audio_fp = generate_urdu_audio(st.session_state.last_answer)
        if audio_fp:
            st.audio(audio_fp, format='audio/mp3')
        else:
            st.info("آڈیو جنریٹ نہیں ہو سکی۔")
    
    with feat_col2:
        st.markdown("##### 📥 ٹیکسٹ ڈاؤن لوڈ:")
        st.download_button(
            label="📄 جواب (.txt) ڈاؤن لوڈ کریں",
            data=st.session_state.last_answer,
            file_name="EduGuide_AI_Response.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with feat_col3:
        st.markdown("##### 📄 PDF پورٹل ایکسپورٹ:")
        pdf_file = create_pdf_report(st.session_state.last_answer)
        st.download_button(
            label="📕 PDF رپورٹ ڈاؤن لوڈ کریں",
            data=pdf_file,
            file_name="EduGuide_AI_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("##### 📋 متن کاپی کرنے کے لیے نیچے دیے گئے باکس کے اوپر Copy آئیکن پر کلک کریں:")
    st.code(st.session_state.last_answer, language=None)

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Urdu Learning & Assessment Assistant | Developed by Arsalan Mustafa for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")
