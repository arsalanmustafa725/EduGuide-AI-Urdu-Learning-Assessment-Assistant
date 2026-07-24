import streamlit as st
from groq import Groq
import sys
import os
import re
from gtts import gTTS
import io
import PyPDF2

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

# --- 3. گروک اے پی آئی کی (Groq API Key) حاصل کرنا ---
MY_GROQ_KEY = None

try:
    if "GROQ_API_KEY" in st.secrets:
        MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not MY_GROQ_KEY:
    MY_GROQ_KEY = os.getenv("GROQ_API_KEY", "YOUR_LOCAL_GROQ_KEY_HERE")

# --- 🎯 غیر ملکی اور فضول حروف مکمل ہٹانے کا فنکشن ---
def remove_foreign_characters(text):
    if not text:
        return ""
    # چینی، ہندی، اور دیگر غیر متعلقہ غیر ملکی سیمبلز کو ہٹانا
    pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\u0900-\u097f]+'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text.strip()

# --- 📄 PDF اور TXT فائل سے ٹیکسٹ نکالنے کا فنکشن ---
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

# --- 🔊 اردو ٹیکسٹ ٹو سپیچ (Audio Player) فنکشن ---
def generate_urdu_audio(text):
    try:
        clean_speech_text = re.sub(r'[*#\_`~]', '', text)
        tts = gTTS(text=clean_speech_text, lang='ur')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        return None

# --- 4. سیشن سٹیٹ (Session State) ---
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

# --- سائڈ بار (Sidebar) ---
with st.sidebar:
    st.title("🚀 EduGuide AI Urdu")
    st.caption("Urdu Learning & Assessment Assistant")
    st.divider()
    
    st.subheader("🎯 1️⃣ مضمون کا انتخاب (Subject)")
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
    
    st.subheader("📊 2️⃣ سطح کا انتخاب (Difficulty)")
    selected_level = st.select_slider(
        "لیول منتخب کریں:",
        options=["ابتدائی (Primary/Middle)", "میٹرک / انٹرمیڈیٹ (High School)", "یونیورسٹی / ایڈوانسڈ (Undergrad)"],
        value="میٹرک / انٹرمیڈیٹ (High School)"
    )
    
    st.divider()
    st.subheader("🛠️ بنیادی فیچرز")
    st.markdown("""
    1. **پی ڈی ایف و ٹیکسٹ فائل پروسیسنگ** 📄
    2. **سخت مضمون کی تصدیق (Subject Validation)** 🛑
    3. **اردو آواز سے سننا (Text-to-Speech)** 🔊
    4. **تکنیکی الفاظ کی لغت (Vocabulary)** 🔤
    5. **امتحانی سوالات جنریٹر** ❓
    6. **آسان اردو میں تبدیلی بٹن** ⚡
    """)
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

# --- dynamic SYSTEM PROMPT (سخت ترین ہدایات کے ساتھ) ---
SYSTEM_PROMPT = f"""
تمہارا نام 'EduGuide AI' ہے۔ تم پاکستان کے طلباء کے لیے ایک انتہائی محتاط اور سمارٹ AI تعلیمی معاون ہو۔
یہ پروجیکٹ الخدمت فاؤنڈیشن، بنو قابل (Bano Qabil 3.0) اور علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026) کے لیے تیار کیا گیا ہے۔

موجودہ سیشن کا منتخب کردہ مضمون: "{selected_subject}"
موجودہ سیشن کا منتخب کردہ تعلیمی لیول: "{selected_level}"

🛑 **سخت ترین مضمون کی وریفیکیشن کے قواعد (STRICT SUBJECT MATCH RULE):**
1. اگر منتخب کردہ مضمون 'عمومی / دیگر (General)' کے علاوہ کوئی مخصوص مضمون ہے (مثلاً فزکس، کیمسٹری، کمپیوٹر سائنس، بائیولوجی، ریاضی وغیرہ)، تو سب سے پہلے صارف کے دیے گئے متن/سوال کی جانچ کرو۔
2. اگر صارف کا سوال چنے گئے مضمون سے تعلق **نہیں** رکھتا (مثال کے طور پر ڈراپ ڈاؤن میں '{selected_subject}' منتخب ہے لیکن سوال کسی دوسرے مضمون جیسے کمپیوٹر، کیمسٹری، یا جنرل باتوں کا ہے)، تو تم **ہرگز سوال کا جواب نہیں دو گے**۔
3. عدم مطابقت (Mismatch) کی صورت میں تم صرف اور صرف یہ معذرت خواہی کا پیغام دو گے:
   "⚠️ **مضمون میں عدم مطابقت (Subject Mismatch)!**
   آپ نے سائڈ بار میں ڈراپ ڈاؤن سے '**{selected_subject}**' منتخب کیا ہے، جبکہ آپ کا سوال کسی اور مضمون سے متعلق محسوس ہو رہا ہے۔ 
   براہِ کرم سائڈ بار سے صحیح مضمون (مثلاً کمپیوٹر، فزکس، کیمسٹری وغیرہ) منتخب کریں تاکہ آپ کو درست اور صحیح تعلیمی جواب فراہم کیا جا سکے۔"

📜 **سخت ترین تحریری و زبان کے قواعد (STRICT LANGUAGE RULES):**
1. تمام جوابات **صرف اور صرف خالص اور سلیس اردو رسم الخط (Urdu Script)** میں ہونے چاہئیں۔
2. چینی، ہندی، جاپانی یا کسی بھی غیر متعلقہ غیر ملکی زبان کے حروف کا استعمال سخت منع اور گناہِ کبیرہ ہے۔
3. جواب میں کوئی اضافی، فضول یا غیر متعلقہ جملے شامل نہ کرو۔ صرف اور صرف مطلوبہ تعلیمی مواد دو۔
4. اگر سوال چنے گئے مضمون سے مطابقت رکھتا ہو:
   - کوئز (MCQs) کی صورت میں 4 اختیارات (الف، ب، ج، د)، **درست جواب** اور **مختصر اردو وضاحت** لازمی لکھیں۔
   - ہر صحیح جواب کے آخر میں 3 سے 5 اہم تکنیکی انگریزی الفاظ اور ان کا اردو ترجمہ **"🔤 اہم تکنیکی الفاظ (Glossary)"** کی ہیڈنگ کے ساتھ لازمی بنائیں۔
"""

# --- مین انٹرفیس ---
st.title("🚀 EduGuide AI: Urdu Learning & Assessment Assistant")
st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کا خصوصی پروجیکٹ**")
st.write("تعلیم میں زبان کی رکاوٹ کو دور کرنے اور سلیس اردو میں سیکھنے و ٹیسٹ دینے کا جدید ترین حل۔")

# --- 📁 فائل اپ لوڈر ---
st.subheader("📄 فائل اپ لوڈ کریں (اختیاری):")
uploaded_file = st.file_uploader("اپنی PDF یا TXT فائل اپ لوڈ کریں تاکہ AI اس کا مواد پروسیس کر سکے:", type=['pdf', 'txt'])

file_extracted_text = ""
if uploaded_file is not None:
    file_extracted_text = extract_text_from_file(uploaded_file)
    if file_extracted_text:
        st.success(f"فائل '{uploaded_file.name}' کامیابی سے پڑھ لی گئی ہے!")

# --- ان پٹ باکس ---
user_input = st.text_area(
    "اپنا تعلیمی سوال، مضمون یا متن یہاں درج کریں (یا فائل اپ لوڈ کریں):", 
    value=file_extracted_text if file_extracted_text else "",
    height=180,
    placeholder="یہاں اپنا سوال یا مضمون درج کریں..."
)

# --- ایکشن بٹنز ---
st.subheader("🎯 منتخب کریں کہ AI کیا کرے:")
act_col1, act_col2, act_col3, act_col4 = st.columns(4)

action_prompt = None

with act_col1:
    if st.button("🔍 آسان اردو میں وضاحت کریں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن یا سوال کی آسان اور سلیس اردو میں تفصیلی وضاحت کریں:\n\n{user_input}"

with act_col2:
    if st.button("📝 مختصر اردو خلاصہ بنائیں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن کا اہم نکات پر مشتمل مختصر اور جامع اردو خلاصہ بنائیں:\n\n{user_input}"

with act_col3:
    if st.button("🧠 اردو MCQ کوئز بنائیں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن/ٹاپک کی بنیاد پر 4 کثیر الانتخابی سوالات (MCQs) بنائیں، اختیارات دیں اور ہر سوال کے نیچے درست جواب اور مختصر اردو وضاحت بھی درج کریں:\n\n{user_input}"

with act_col4:
    if st.button("❓ اہم امتحانی سوالات جنریٹ کریں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن/ٹاپک کی بنیاد پر 3 مختصر امتحانی سوالات (Short Questions) اور 2 تفصیلی سوالات (Long Questions) ان کے ماڈل اردو جوابات کے ساتھ تیار کریں:\n\n{user_input}"

# --- AI کال کرنے کا فنکشن ---
def fetch_ai_response(prompt_text):
    if not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key غائب ہے! Streamlit Secrets میں API Key شامل کریں۔")
        return None
    try:
        client = Groq(api_key=MY_GROQ_KEY)
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.1
        )
        raw_answer = res.choices[0].message.content
        return remove_foreign_characters(raw_answer)
    except Exception as e:
        st.error(f"کنیکشن یا API کا مسئلہ ہے۔ تفصیل: {str(e)}")
        return None

# --- پراسیسنگ اور AI رسپانس ---
if action_prompt:
    clean_input_text = user_input.strip()
    if not clean_input_text:
        st.warning("ارسلان بھائی، پہلے ٹیکسٹ باکس میں اپنا سوال درج کریں یا کوئی فائل اپ لوڈ کریں!")
    else:
        with st.spinner('EduGuide AI Urdu جواب تیار کر رہا ہے...'):
            ans = fetch_ai_response(action_prompt)
            if ans:
                st.session_state.last_answer = ans

# --- جواب ڈسپلے کرنا ---
if st.session_state.last_answer:
    st.divider()
    st.subheader("📋 EduGuide AI Urdu کا جواب:")
    st.markdown(st.session_state.last_answer)
    
    # اگر عدم مطابقت کا پیغام نہ ہو صرف تب آسان کرنے کا بٹن دکھائیں
    if "مضمون میں عدم مطابقت" not in st.session_state.last_answer:
        st.divider()
        simp_col1, simp_col2 = st.columns([2, 1])
        with simp_col1:
            st.info("کیا یہ جواب تھوڑا مشکل محسوس ہو رہا ہے؟")
        with simp_col2:
            if st.button("🔄 اسے اور آسان اردو میں سمجھائیں", use_container_width=True):
                simplify_prompt = f"برائے مہربانی نیچے دیے گئے جواب کو انتہائی سادہ، بچوں جیسی عام فہم اردو اور روزمرہ کی آسان مثالوں میں دوبارہ لکھیں تاکہ چھوٹی کلاس کا طالب علم بھی آسانی سے سمجھ سکے:\n\n{st.session_state.last_answer}"
                with st.spinner('جواب کو مزید آسان اردو میں تبدیل کیا جا رہا ہے...'):
                    simplified_ans = fetch_ai_response(simplify_prompt)
                    if simplified_ans:
                        st.session_state.last_answer = simplified_ans
                        st.rerun()

    # --- 🚀 اضافی ٹولز (Audio, Download, Copy) ---
    st.divider()
    st.subheader("🛠️ اضافی ٹولز (Extra Features):")
    
    feat_col1, feat_col2 = st.columns(2)
    
    # 🔊 آڈیو میں سنیں
    with feat_col1:
        st.markdown("##### 🔊 جواب آڈیو میں سنیں:")
        audio_fp = generate_urdu_audio(st.session_state.last_answer)
        if audio_fp:
            st.audio(audio_fp, format='audio/mp3')
        else:
            st.info("آڈیو جنریٹ نہیں ہو سکی۔")
    
    # 📥 نتیجہ ڈاؤن لوڈ کریں
    with feat_col2:
        st.markdown("##### 📥 نتیجہ ڈاؤن لوڈ کریں:")
        st.download_button(
            label="📄 جواب ٹیکسٹ فائل (.txt) میں ڈاؤن لوڈ کریں",
            data=st.session_state.last_answer,
            file_name="EduGuide_AI_Response.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # 📋 کاپی کرنے کا باکس
    st.markdown("##### 📋 متن کاپی کرنے کے لیے نیچے دیے گئے باکس کے اوپر Copy آئیکن پر کلک کریں:")
    st.code(st.session_state.last_answer, language=None)

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Urdu Learning & Assessment Assistant | Developed by Arsalan for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")
