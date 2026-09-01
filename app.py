import streamlit as st
from groq import Groq
import sys
import os
import json
import time
from gtts import gTTS
import io
import PyPDF2
from PIL import Image
import base64
from streamlit_mic_recorder import mic_recorder  

if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None

# --- 1. اسٹریم لٹ پیج سیٹ اپ ---
st.set_page_config(
    page_title="EduGuide AI: Learning & Assessment Assistant",
    page_icon="🎓",
    layout="wide"
)

# --- فیوریٹس کو فائل میں محفوظ کرنے کا محفوظ سیٹ اپ (مسئلہ حل) ---
FAV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites.json")

def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []
    return []

def save_favorites_to_file(favorites):
    try:
        with open(FAV_FILE, "w", encoding="utf-8") as f:
            json.dump(favorites, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving file: {e}")

# سیشن اسٹیٹ میں فائل سے ڈیٹا لوڈ کریں
if "favorites_list" not in st.session_state:
    st.session_state.favorites_list = load_favorites()

# --- 2. انکوڈنگ فکس ---
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- 3. سیشن اسٹیٹ ---
if "language" not in st.session_state:
    st.session_state.language = "Urdu"

if "answer_urdu" not in st.session_state:
    st.session_state.answer_urdu = None
if "answer_english" not in st.session_state:
    st.session_state.answer_english = None

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

# --- 🎨 متحرک CSS ---
current_lang = st.session_state.language
text_direction = "rtl" if current_lang == "Urdu" else "ltr"
text_align = "right" if current_lang == "Urdu" else "left"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');

h1, h2, h3, h4, h5, h6, p, div:not([data-testid="stFileUploader"] *) {{
    font-family: {'\'Noto Nastaliq Urdu\', \'Jameel Noori Nastaliq\', sans-serif' if current_lang == 'Urdu' else '\'Segoe UI\', sans-serif'} !important;
}}

.dynamic-text-box {{
    direction: {text_direction};
    text-align: {text_align};
    font-size: 17px;
    line-height: 1.8;
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
}}

.flashcard-box {{
    background: linear-gradient(135deg, #ffffff, #f0fdf4);
    border: 1.5px solid #198754;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 4px 12px rgba(25, 135, 84, 0.08);
    direction: {text_direction};
    text-align: {text_align};
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

# --- 4. Groq API Key (مضبوط اور محفوظ طریقہ) ---
MY_GROQ_KEY = None
try:
    if st.secrets and "GROQ_API_KEY" in st.secrets:
        MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not MY_GROQ_KEY:
    MY_GROQ_KEY = os.getenv("GROQ_API_KEY", "")

# اگر آپ چاہیں تو عارضی طور پر یہ لائن لگا کر چیک کر سکتے ہیں کہ کیی اٹھ رہی ہے یا نہیں
# if not MY_GROQ_KEY:
#     st.error("API Key نہیں مل رہی! براہ کرم Streamlit Secrets چیک کریں۔")

# --- 🎯 مددگار فنکشنز ---
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

import re

def generate_audio(text, lang_code):
    try:
        if not text:
            return None
            
        clean_text = re.sub(r'[#*_`~`\-]', ' ', text)
        clean_text = re.sub(r'http\S+|www\S+|https\S+', '', clean_text, flags=re.MULTILINE)
        clean_text = ' '.join(clean_text.split())
        
        tts = gTTS(text=clean_text, lang=lang_code, slow=True)
        
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        return None

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
    
    st.subheader("🌐 Language / زبان")
    
    lang_choice = st.radio(
        "Select Language / زبان منتخب کریں:",
        options=["Urdu 🇵🇰", "English 🇺🇸"],
        index=0 if st.session_state.language == "Urdu" else 1,
        key="language_radio_selection"
    )
    
    new_lang_val = "Urdu" if "Urdu" in lang_choice else "English"
    
    if new_lang_val != st.session_state.language:
        st.session_state.language = new_lang_val
        st.session_state.dynamic_quizzes = []
        st.session_state.flashcards_data = []
        st.session_state.quiz_state = {}
        st.rerun()
        
    st.divider()
    st.subheader("🎨 تھیم اور سیٹ اپ" if st.session_state.language == "Urdu" else "🎨 Theme & Setup")
    alkhidmat_theme = st.toggle("🟢 الخدمت برانڈنگ تھیم" if st.session_state.language == "Urdu" else "🟢 Alkhidmat Branding Theme", value=True)
    low_bandwidth = st.toggle("⚡ لو بینڈوڈتھ / دیہاتی موڈ" if st.session_state.language == "Urdu" else "⚡ Low Bandwidth / 2G Mode", value=False)
    socratic_mode = st.toggle("🧠 سقراطی استاد موڈ" if st.session_state.language == "Urdu" else "🧠 Socratic Tutor Mode", value=False)
    
    if alkhidmat_theme:
        st.markdown("""
        <style>
        .stApp { background-color: #f4f9f5; }
        h1, h2, h3 { color: #0d6efd !important; }
        .stButton > button { background-color: #198754 !important; color: white !important; }
        </style>
        """, unsafe_allow_html=True)

    selected_subject = st.selectbox(
        "مضمون منتخب کریں:" if st.session_state.language == "Urdu" else "Select subject:",
        [
            "عمومی / دیگر (General)" if st.session_state.language == "Urdu" else "General / Other",
            "💻 کمپیوٹر سائنس / آئی ٹی" if st.session_state.language == "Urdu" else "💻 Computer Science / IT",
            "⚛️ فزکس (Physics)" if st.session_state.language == "Urdu" else "⚛️ Physics",
            "🧪 کیمسٹری (Chemistry)" if st.session_state.language == "Urdu" else "🧪 Chemistry",
            "🧬 بائیولوجی (Biology)" if st.session_state.language == "Urdu" else "🧬 Biology",
            "📐 ریاضی (Mathematics)" if st.session_state.language == "Urdu" else "📐 Mathematics",
            "📖 اسلامیات (Islamic Studies)" if st.session_state.language == "Urdu" else "📖 Islamic Studies",
            "🇵🇰 مطالعہ پاکستان (Pakistan Studies)" if st.session_state.language == "Urdu" else "🇵🇰 Pakistan Studies",
            "📜 تاریخ (History)" if st.session_state.language == "Urdu" else "📜 History",
            "📈 معاشیات (Economics)" if st.session_state.language == "Urdu" else "📈 Economics",
            "🌍 جغرافیہ (Geography)" if st.session_state.language == "Urdu" else "🌍 Geography"
        ]
    )
    
    selected_level = st.select_slider(
        "لیول منتخب کریں:" if st.session_state.language == "Urdu" else "Select level:",
        options=["ابتدائی (Primary/Middle)" if st.session_state.language == "Urdu" else "Primary/Middle", "میٹرک / انٹرمیڈیٹ" if st.session_state.language == "Urdu" else "High School", "یونیورسٹی / ایڈوانسڈ" if st.session_state.language == "Urdu" else "Undergrad"],
        value="میٹرک / انٹرمیڈیٹ" if st.session_state.language == "Urdu" else "High School"
    )
    
    st.divider()
    st.metric(label="کل سوالات" if st.session_state.language == "Urdu" else "Total Questions", value=st.session_state.total_questions)
    col_q1, col_q2 = st.columns(2)
    col_q1.metric(label="اسکور" if st.session_state.language == "Urdu" else "Score", value=st.session_state.quiz_score)
    col_q2.metric(label="کل کوئز" if st.session_state.language == "Urdu" else "Total Quiz", value=st.session_state.quiz_total)
    
    # --- ⭐ سائیڈ بار میں محفوظ شدہ جوابات (Favorites) کا سیکشن ---
    st.divider()
    st.subheader("⭐ Saved Answers" if st.session_state.language == "English" else "⭐ محفوظ کردہ جوابات")
    
    if not st.session_state.favorites_list:
        st.sidebar.info("No saved answers yet." if st.session_state.language == "English" else "ابھی کوئی جواب محفوظ نہیں ہے۔")
    else:
        for idx, fav_ans in enumerate(st.session_state.favorites_list):
            btn_label = f"📌 Answer {idx+1}" if st.session_state.language == "English" else f"📌 جواب نمبر {idx+1}"
            
            if st.sidebar.button(btn_label, key=f"open_fav_{idx}"):
                @st.dialog("📖 Saved Answer Details" if st.session_state.language == "English" else "📖 محفوظ شدہ جواب کی تفصیل")
                def show_full_answer(answer_text):
                    st.write(answer_text)
                    st.write("")
                    if st.button("❌ Close" if st.session_state.language == "English" else "❌ بند کریں", key=f"close_dialog_{idx}"):
                        st.rerun()
                show_full_answer(fav_ans)

            if st.sidebar.button("🗑️ Remove #{}".format(idx+1) if st.session_state.language == "English" else "🗑️ ہٹائیں #{}".format(idx+1), key=f"del_fav_{idx}"):
                st.session_state.favorites_list.pop(idx)
                save_favorites_to_file(st.session_state.favorites_list)
                st.rerun()

    st.divider()
    st.write("👤 **ڈویلپر:** ارسلان  (ARSALAN)")

# --- 🔥 سسٹم پرامپٹ (سخت زبان اور مکسنگ روکنے والا اصول) ---
active_lang = st.session_state.language

if active_lang == "English":
    lang_instruction = "ABSOLUTE MANDATORY RULE: You MUST output your ENTIRE response STRICTLY, 100%, and EXCLUSIVELY in professional, fluent ENGLISH. Do NOT output any internal thinking process, do NOT output drafts or English/Urdu mixing."
    subject_guardrail = f"""
    SUBJECT ENFORCEMENT RULE:
    - Currently Selected Subject: '{selected_subject}'
    - If the selected subject is NOT 'General / Other', you MUST strictly verify if the user's question or uploaded file is relevant to '{selected_subject}'.
    - If the question belongs to a different field, politely refuse.
    """
else:
    lang_instruction = "قطعی اور سخت ترین حکم: آپ کا پورا جواب سو فیصد (100%) اور صرف اور صرف خالص اردو زبان اور اردو رسم الخط میں ہونا چاہئے۔ ہرگز ہرگز کوئی اندرونی سوچ (Thinking process)، ڈرافٹ، انگریزی الفاظ یا انگریزی کے جملے سکرین پر ظاہر نہ کریں۔ براہ راست صرف اور صرف حتمی اردو جواب پیش کریں۔"
    subject_guardrail = f"""
    مضمون کی پابندی کا سخت قانون (Subject Guardrail Rule):
    - موجودہ منتخب کردہ مضمون: '{selected_subject}'
    - اگر منتخب کردہ مضمون 'عمومی / دیگر (General)' نہیں ہے، تو چیک کریں کہ آیا سوال اسی مضمون سے متعلق ہے یا نہیں۔ اگر نہیں، تو صاف اور سختی سے اردو میں انکار کر دیں۔
    """

socratic_instruction = ""
if socratic_mode:
    socratic_instruction = "\nSocratic Mode Active: Guide the student with hints instead of giving direct answers." if active_lang == "English" else "\nسقراطی موڈ فعال ہے: طالب علم کو براہ راست جواب دینے کے بجائے اشارے اور رہنما سوالات دیں۔"

SYSTEM_PROMPT = f"""
You are 'EduGuide AI', an educational assistant for Alkhidmat Foundation, Bano Kabil 3.0, and Alibaba Cloud AI Hackathon 2026[cite: 1].

STRICT CONFIGURATION & ANTI-MIXING RULE:
- Active Language Mode: {active_lang}
- {lang_instruction}
- Selected Subject: {selected_subject}
- Selected Academic Level: {selected_level}
{subject_guardrail}
{socratic_instruction}

CRITICAL INSTRUCTION FOR URDU MODE:
If the Active Language Mode is Urdu, you are strictly prohibited from outputting any English words, translation drafts, internal reasoning, or thinking process. Output ONLY the final, clean, 100% pure Urdu text from the very first character to the last. No English thoughts allowed under any circumstances.
"""

# --- مین انٹرفیس ---
if active_lang == "Urdu":
    st.title("🚀 EduGuide AI: Urdu Learning & Assessment Assistant")
    st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کا خصوصی پروجیکٹ**[cite: 1]")
else:
    st.title("🚀 EduGuide AI: International Learning & Assessment Assistant")
    st.markdown("##### **Special Project for Alkhidmat Foundation, Bano Kabil & Alibaba Cloud Hackathon 2026**[cite: 1]")

def fetch_ai_response(prompt_text, img_data=None, custom_sys_prompt=None):
    if not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key is missing! Please configure your API key.")
        return None
    
    client = Groq(api_key=MY_GROQ_KEY)
    active_sys_prompt = custom_sys_prompt if custom_sys_prompt else SYSTEM_PROMPT

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
                return res.choices[0].message.content.strip()
            except Exception:
                time.sleep(1)
                continue
        
        st.error("تصویر پروسیسنگ میں مسئلہ آ رہا ہے۔ براہ کرم تصویر کا سائز کم کریں یا سوال لکھ کر پوچھیں۔" if active_lang == "Urdu" else "Vision processing failed. Please check image size or type the question.")
        return None

    # --- مستحکم ٹیکسٹ ماڈلز کی لسٹ ---
    text_models = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile"
    ]
    
    for model_name in text_models:
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": active_sys_prompt},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.1,
                top_p=0.9
            )
            if res and res.choices:
                return res.choices[0].message.content.strip()
        except Exception:
            time.sleep(1)
            continue
            
    st.error("All AI requests failed. Please check your API key or internet connection.")
    return None

def generate_dynamic_quiz_data(topic_content):
    lang_json_rule = "strictly in English" if active_lang == "English" else "strictly in Urdu script"
    quiz_sys_prompt = f"You are an exam generator. Return strictly a valid JSON array of 3 MCQs {lang_json_rule}. Format: [{{\"question\": \"Text\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"correct_index\": 0, \"explanation\": \"Short explanation\"}}]. Do not include any extra markdown text outside the JSON array."
    
    quiz_prompt = f"Generate 3 MCQs {lang_json_rule} based on this content:\n\n{topic_content}"
    res = fetch_ai_response(quiz_prompt, custom_sys_prompt=quiz_sys_prompt)
    
    if res:
        try:
            cleaned_json = res.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            
            parsed_data = json.loads(cleaned_json)
            if isinstance(parsed_data, list):
                return parsed_data
        except Exception:
            return []
    return []

def generate_flashcards_data(topic_content):
    lang_fc_rule = "strictly in English" if active_lang == "English" else "strictly in Urdu script"
    fc_sys_prompt = f"You are a revision card builder. Return strictly valid JSON array of 4 key revision flashcards {lang_fc_rule}. Format: [{{\"term\": \"Key term\", \"definition\": \"Concise definition\"}}]."
    
    fc_prompt = f"Generate 4 revision flashcards {lang_fc_rule} for this topic:\n\n{topic_content}"
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
st.subheader("📄 File, Image or Voice Input:" if active_lang == "English" else "📄 فائل، تصویر یا وائس ان پٹ:")
tab_file, tab_voice = st.tabs(["📁 PDF / TXT / Image Upload", "🎙️ Voice Query"])

file_extracted_text = ""
image_bytes = None

with tab_file:
    uploaded_file = st.file_uploader("", type=['pdf', 'txt', 'png', 'jpg', 'jpeg'], label_visibility="collapsed")
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            st.session_state.uploaded_image_bytes = uploaded_file.read()
            if not low_bandwidth:
                st.image(uploaded_file, caption="Uploaded Image", width=350)
            st.success("Image uploaded successfully!" if active_lang == "English" else "تصویر کامیابی سے اپ لوڈ ہو گئی!")
        else:
            file_extracted_text = extract_text_from_file(uploaded_file)
            if file_extracted_text:
                st.success(f"File '{uploaded_file.name}' read successfully!")

with tab_voice:
    st.markdown('<div dir="ltr" style="text-align: left;">', unsafe_allow_html=True)
    audio_data = mic_recorder(start_prompt="🔴 Start Recording", stop_prompt="⏹️ Stop Recording", key='custom_mic_recorder')
    st.markdown('</div>', unsafe_allow_html=True)
    
    if audio_data is not None:
        audio_bytes = audio_data['bytes']
        audio_hash = hash(audio_bytes)
        if "last_processed_audio" not in st.session_state:
            st.session_state.last_processed_audio = None
            
        if st.session_state.last_processed_audio != audio_hash:
            st.session_state.last_processed_audio = audio_hash
            st.audio(audio_bytes, format='audio/wav')
            with st.spinner("Processing voice input..."):
                lang_code_whisper = "ur" if active_lang == "Urdu" else "en"
                recognized_text = transcribe_audio(audio_bytes, lang_code_whisper)
                if recognized_text:
                    st.session_state.voice_text = recognized_text
                    st.success(f"🗣️ Recognized: **\"{recognized_text}\"**")

# --- 📝 فارم بیسڈ ان پٹ اور وائس سنکرونائزیشن ---
if "user_query_box" not in st.session_state:
    st.session_state.user_query_box = ""

if st.session_state.voice_text:
    st.session_state.user_query_box = st.session_state.voice_text
    st.session_state.voice_text = ""
    st.rerun()

with st.form(key="user_query_form"):
    user_input = st.text_area(
        "Enter your educational question, topic or prompt here:" if active_lang == "English" else "اپنا تعلیمی سوال، ٹاپک یا ہدایت یہاں درج کریں:", 
        value=st.session_state.user_query_box,
        height=140,
        placeholder="Type your question here or use voice..." if active_lang == "English" else "یہاں اپنا سوال لکھیں یا اوپر بولیں..."
    )
    submit_button = st.form_submit_button(label="🚀 Get Answer" if active_lang == "English" else "🚀 جواب حاصل کریں", use_container_width=True)

if submit_button:
    st.session_state.user_query_box = user_input
    clean_input_text = user_input.strip()

    image_bytes = st.session_state.uploaded_image_bytes
    
    if not clean_input_text and image_bytes is not None:
        clean_input_text = "Please solve this mathematical problem or answer the question shown in this image step by step." if active_lang == "English" else "براہ کرم اس تصویر میں دیے گئے ریاضی کے سوال یا تحریر کو پڑھ کر اس کا مکمل اور قدم بہ قدم حل بیان کریں۔"
    
    if not clean_input_text and image_bytes is None:
        st.warning("Please enter a question or upload a file/image first!" if active_lang == "English" else "پہلے اپنا سوال درج کریں یا کوئی فائل/تصویر اپ لوڈ کریں!")
    else:
        with st.spinner('EduGuide AI is generating the answer...' if active_lang == "English" else 'EduGuide AI جواب تیار کر رہا ہے...'):
            if active_lang == "English":
                lang_rule_text = "strictly, 100%, and exclusively in professional English"
                main_prompt = f"Provide a comprehensive answer {lang_rule_text} based on subject '{selected_subject}':\n\n{clean_input_text}"
            else:
                lang_rule_text = "سو فیصد (100%) اور صرف خالص اردو زبان میں بغیر کسی انگریزی رلاوٹ یا سوچ کے"
                main_prompt = f"اس تعلیمی سوال کا تفصیلی جواب {lang_rule_text} مضمون '{selected_subject}' کے مطابق فراہم کریں:\n\n{clean_input_text}"
            
            ans = fetch_ai_response(main_prompt, image_bytes)
            if ans:
                if active_lang == "English":
                    st.session_state.answer_english = ans
                else:
                    st.session_state.answer_urdu = ans
                
                st.session_state.total_questions += 1
                st.session_state.dynamic_quizzes = []
                st.session_state.flashcards_data = []
                st.session_state.quiz_state = {}
                st.rerun()

# --- فعال جواب کا ڈسپلے ---
current_active_answer = st.session_state.answer_english if active_lang == "English" else st.session_state.answer_urdu

if current_active_answer:
    st.divider()
    
    st.markdown("##### 🔊 Audio Response:" if active_lang == "English" else "##### 🔊 فوری آڈیو سنیں:")
    tts_lang_code = "ur" if active_lang == "Urdu" else "en"
    audio_fp_auto = generate_audio(current_active_answer, tts_lang_code)
    if audio_fp_auto:
        st.audio(audio_fp_auto, format='audio/mp3')
    
    st.subheader("📋 EduGuide AI Response:" if active_lang == "English" else "📋 EduGuide AI کا جواب:")
    st.markdown(f'<div class="dynamic-text-box">{current_active_answer}</div>', unsafe_allow_html=True)
    
    # --- ⭐ جواب کو فیوریٹس میں محفوظ کرنے کا بٹن ---
    col_fav1, col_fav2 = st.columns([1, 4])
    with col_fav1:
        if st.button("⭐ Save to Favorites" if active_lang == "English" else "⭐ فیوریٹس میں محفوظ کریں", key="save_main_ans_btn"):
            if current_active_answer and current_active_answer not in st.session_state.favorites_list:
                st.session_state.favorites_list.append(current_active_answer)
                save_favorites_to_file(st.session_state.favorites_list)
                st.success("Saved to Favorites!" if active_lang == "English" else "فیوریٹس میں محفوظ ہو گیا!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.info("Already in Favorites!" if active_lang == "English" else "پہلے سے محفوظ ہے!")

    if "Subject Mismatch" not in current_active_answer:
        st.divider()
        st.subheader("🎓 Educational AI Tools:" if active_lang == "English" else "🎓 اس جواب پر مزید ایجوکیشنل AI ٹولز:")
        
        r1_c1, r1_c2, r1_c3 = st.columns(3)
        r2_c1, r2_c2, r2_c3 = st.columns(3)
        r3_c1, r3_c2 = st.columns(2)
        
        tool_prompt = None
        if active_lang == "English":
            lang_rule_tool = "strictly, 100%, and exclusively in professional English"
        else:
            lang_rule_tool = "سو فیصد (100%) خالص اردو زبان میں"

        with r1_c1:
            if st.button("🔍 1. Simplify Explanation" if active_lang == "English" else "🔍 1. مزید آسان الفاظ میں سمجھائیں", use_container_width=True):
                tool_prompt = f"Explain this simpler {lang_rule_tool}:\n\n{current_active_answer}"
        
        with r1_c2:
            if st.button("📅 2. AI Study Roadmap" if active_lang == "English" else "📅 2. AI اسٹڈی پلانر بنائیں", use_container_width=True):
                tool_prompt = f"Create a 15-day study roadmap {lang_rule_tool} for this topic:\n\n{current_active_answer}"
        
        with r1_c3:
            if st.button("📝 3. Generate Model Paper" if active_lang == "English" else "📝 3. مکمل ماڈل پیپر جنریٹ کریں", use_container_width=True):
                tool_prompt = f"Generate a model test paper {lang_rule_tool} based on:\n\n{current_active_answer}"
        
        with r2_c1:
            if st.button("🧪 4. Step-by-Step Solution" if active_lang == "English" else "🧪 4. Step-by-Step حل", use_container_width=True):
                tool_prompt = f"Break down concepts step-by-step {lang_rule_tool}:\n\n{current_active_answer}"
        
        with r2_c2:
            if st.button("💡 5. Socratic Hint" if active_lang == "English" else "💡 5. سوچنے کے لیے اشارہ (Hint)", use_container_width=True):
                tool_prompt = f"Provide a guiding hint {lang_rule_tool}:\n\n{current_active_answer}"
        
        with r2_c3:
            if st.button("🔤 6. Technical Glossary" if active_lang == "English" else "🔤 6. اہم تکنیکی الفاظ کی لغت", use_container_width=True):
                tool_prompt = f"List key technical terms and definitions {lang_rule_tool}:\n\n{current_active_answer}"

        with r3_c1:
            if st.button("📜 7. Past Papers Focus" if active_lang == "English" else "📜 7. پاسٹ پیپرز اینالیٹکس", use_container_width=True):
                tool_prompt = f"Analyze past paper importance {lang_rule_tool}:\n\n{current_active_answer}"

        with r3_c2:
            if st.button("🎮 8. Gamified Quiz Mode" if active_lang == "English" else "🎮 8. کوئز گیم موڈ", use_container_width=True):
                tool_prompt = f"Create a 3-question MCQ quiz {lang_rule_tool} based on:\n\n{current_active_answer}"

        if tool_prompt:
            with st.spinner('Processing tool request...'):
                processed_ans = fetch_ai_response(tool_prompt, image_bytes)
                if processed_ans:
                    if active_lang == "English":
                        st.session_state.answer_english = processed_ans
                    else:
                        st.session_state.answer_urdu = processed_ans
                    st.rerun()

    # --- فلیش کارڈز UI ---
        st.divider()
        st.subheader("🎴 Smart Revision Flashcards" if active_lang == "English" else "🎴 اسمارٹ فلیش کارڈز")
        if st.button("⚡ Generate Flashcards" if active_lang == "English" else "⚡ فلیش کارڈز تیار کریں", use_container_width=True):
            with st.spinner("Building flashcards..."):
                fcs = generate_flashcards_data(current_active_answer)
                if fcs:
                    st.session_state.flashcards_data = fcs

        if st.session_state.flashcards_data:
            fc_cols = st.columns(len(st.session_state.flashcards_data))
            for idx, card in enumerate(st.session_state.flashcards_data):
                with fc_cols[idx]:
                    card_title = card.get('term', f'Card {idx+1}')
                    card_def = card.get('definition', '')
                    st.markdown(f'<div class="flashcard-box dynamic-text-box"><div class="flashcard-title">&#128204; {card_title}</div><p style="font-size: 14px;">{card_def}</p></div>', unsafe_allow_html=True)

        # --- ڈائنامک کوئز UI ---
        st.divider()
        st.subheader("🎯 Dynamic AI Quiz Engine" if active_lang == "English" else "🎯 ڈائنامک AI کوئز انجن")
        if st.button("🔄 Generate Live Quiz" if active_lang == "English" else "🔄 لائیو ٹیسٹ بنائیں", use_container_width=True):
            with st.spinner("Generating fresh MCQs..."):
                quiz_data = generate_dynamic_quiz_data(current_active_answer)
                if quiz_data:
                    st.session_state.dynamic_quizzes = quiz_data
                    st.session_state.quiz_state = {}

        if st.session_state.dynamic_quizzes:
            st.markdown("##### 📝 Solve questions and view score:" if active_lang == "English" else "##### 📝 سوالات حل کریں:")
            for q_idx, q in enumerate(st.session_state.dynamic_quizzes):
                q_key = f"quiz_{q_idx}"
                options = q.get('options', [])
                correct_index = q.get('correct_index', 0)
                
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
                    if st.button(f"Check Answer (Q{q_idx + 1})" if active_lang == "English" else f"جواب چیک کریں ({q_idx + 1})", key=f"dyn_btn_{q_idx}"):
                        chosen_idx = options.index(user_choice)
                        is_correct = (chosen_idx == correct_index)
                        
                        q_state["submitted"] = True
                        q_state["selected_idx"] = chosen_idx
                        q_state["is_correct"] = is_correct
                        
                        st.session_state.quiz_total += 1
                        if is_correct:
                            st.session_state.quiz_score += 1
                        st.rerun()
                else:
                    if q_state["is_correct"]:
                        st.success(f"🎉 Correct! {q.get('explanation', '')}" if active_lang == "English" else f"🎉 بالکل درست! {q.get('explanation', '')}")
                    else:
                        st.error(f"❌ Incorrect! Correct was: '{options[correct_index]}' | {q.get('explanation', '')}" if active_lang == "English" else f"❌ غلط! درست آپشن تھا: '{options[correct_index]}'")
                
                st.write("---")

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Learning & Assessment Assistant | Developed by ARSALAN")
