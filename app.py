import streamlit as st
from groq import Groq
import sys
import os
import re
from gtts import gTTS
import io
import PyPDF2
from PIL import Image
import base64

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

# --- 🖼️ تصویر کو Base64 میں تبدیل کرنے کا فنکشن ---
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

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
    1. **پی ڈی ایف، ٹیکسٹ اور امیج پروسیسنگ** 📄🖼️
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
1. اگر منتخب کردہ مضمون 'عمومی / دیگر (General)' کے علاوہ کوئی مخصوص مضمون ہے (مثلاً فزکس، کیمسٹری، کمپیوٹر سائنس، بائیولوجی، ریاضی وغیرہ)، تو سب سے پہلے صارف کے دیے گئے متن/سوال/تصویر کی جانچ کرو۔
2. اگر صارف کا سوال چنے گئے مضمون سے تعلق **نہیں** رکھتا (مثال کے طور پر ڈراپ ڈاؤن میں '{selected_subject}' منتخب ہے لیکن سوال کسی دوسرے مضمون جیسے کمپیوٹر، کیمسٹری، یا جنرل باتوں کا ہے)، تو تم **ہرگز سوال کا جواب نہیں دو گے**۔
3. عدم مطابقت (Mismatch) کی صورت میں تم صرف اور صرف یہ معذرت خواہی کا پیغام دو گے:
   "⚠️ **مضمون میں عدم مطابقت (Subject Mismatch)!**
   آپ نے سائڈ بار میں ڈراپ ڈاؤن سے '**{selected_subject}**' منتخب کیا ہے، جبکہ آپ کا سوال کسی اور مضمون سے متعلق محسوس ہو رہا ہے۔ 
   براہِ کرم سائڈ بار سے صحیح مضمون (مثلاً کمپیوٹر، فزکس، کیمسٹری وغیرہ) منتخب کریں تاکہ آپ کو درست اور صحیح تعلیمی جواب فراہم کیا جا سکے۔"

📜 **سخت ترین تحریری و زبان کے قواعد (STRICT LANGUAGE RULES):**
1. تمام جوابات **صرف اور صرف خالص اور سلیس اردو رسم الخط (Urdu Script)** میں ہونے چاہئیں۔
2. چینی، ہندی، جاپانی یا کسی بھی غیر متعلقہ غیر ملکی زبان کے حروف کا استعمال سخت منع اور گناہِ کبیرہ ہے۔
3. اگر تصویر میں سوال یا نوٹس دیے گئے ہیں تو پہلے اس سوال کا تجزیہ کرو اور پھر سلیس اردو میں جواب فراہم کرو۔
4. جواب میں کوئی اضافی، فضول یا غیر متعلقہ جملے شامل نہ کرو۔ صرف اور صرف مطلوبہ تعلیمی مواد دو۔
5. اگر سوال چنے گئے مضمون سے مطابقت رکھتا ہو:
   - کوئز (MCQs) کی صورت میں 4 اختیارات (الف، ب، ج، د)، **درست جواب** اور **مختصر اردو وضاحت** لازمی لکھیں۔
   - ہر صحیح جواب کے آخر میں 3 سے 5 اہم تکنیکی انگریزی الفاظ اور ان کا اردو ترجمہ **"🔤 اہم تکنیکی الفاظ (Glossary)"** کی ہیڈنگ کے ساتھ لازمی بنائیں۔
"""

# --- مین انٹرفیس ---
st.title("🚀 EduGuide AI: Urdu Learning & Assessment Assistant")
st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کا خصوصی پروجیکٹ**")
st.write("تعلیم میں زبان کی رکاوٹ کو دور کرنے اور سلیس اردو میں سیکھنے و ٹیسٹ دینے کا جدید ترین حل۔")

# --- 📁 فائل اور تصویر اپ لوڈر ---
st.subheader("📄 فائل یا تصویر اپ لوڈ کریں:")
uploaded_file = st.file_uploader(
    "اپنی PDF، TXT فائل یا سوال کی تصویر (PNG, JPG, JPEG) اپ لوڈ کریں:", 
    type=['pdf', 'txt', 'png', 'jpg', 'jpeg']
)

file_extracted_text = ""
image_bytes = None

if uploaded_file is not None:
    if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        image_bytes = uploaded_file.read()
        st.image(uploaded_file, caption="اپ لوڈ کی گئی تصویر", width=350)
        st.success("تصویر کامیابی سے اپ لوڈ ہو گئی ہے!")
    else:
        file_extracted_text = extract_text_from_file(uploaded_file)
        if file_extracted_text:
            st.success(f"فائل '{uploaded_file.name}' کامیابی سے پڑھ لی گئی ہے!")

# --- ان پٹ باکس ---
user_input = st.text_area(
    "اپنا تعلیمی سوال، مضمون یا متن یہاں درج کریں (یا تصویر/فائل کے ساتھ اضافی ہدایت لکھیں):", 
    value=file_extracted_text if file_extracted_text else "",
    height=180,
    placeholder="یہاں اپنا سوال درج کریں یا تصویر/فائل کا انتخاب کریں..."
)

# --- ایکشن بٹنز ---
st.subheader("🎯 منتخب کریں کہ AI کیا کرے:")
act_col1, act_col2, act_col3, act_col4 = st.columns(4)

action_prompt = None

with act_col1:
    if st.button("🔍 آسان اردو میں وضاحت کریں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن/تصویر یا سوال کی آسان اور سلیس اردو میں تفصیلی وضاحت کریں:\n\n{user_input}"

with act_col2:
    if st.button("📝 مختصر اردو خلاصہ بنائیں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن/تصویر کا اہم نکات پر مشتمل مختصر اور جامع اردو خلاصہ بنائیں:\n\n{user_input}"

with act_col3:
    if st.button("🧠 اردو MCQ کوئز بنائیں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن/تصویر/ٹاپک کی بنیاد پر 4 کثیر الانتخابی سوالات (MCQs) بنائیں، اختیارات دیں اور ہر سوال کے نیچے درست جواب اور مختصر اردو وضاحت بھی درج کریں:\n\n{user_input}"

with act_col4:
    if st.button("❓ اہم امتحانی سوالات جنریٹ کریں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن/تصویر/ٹاپک کی بنیاد پر 3 مختصر امتحانی سوالات (Short Questions) اور 2 تفصیلی سوالات (Long Questions) ان کے ماڈل اردو جوابات کے ساتھ تیار کریں:\n\n{user_input}"

# --- AI کال کرنے کا فنکشن (Text & Vision Support + Model Fallback) ---
def fetch_ai_response(prompt_text, img_data=None):
    if not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key غائب ہے! Streamlit Secrets میں API Key شامل کریں۔")
        return None
    
    client = Groq(api_key=MY_GROQ_KEY)
    
    try:
        if img_data:
            # 🖼️ تصویر کے لیے Vision Model
            base64_img = encode_image(img_data)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
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
                model="llama-3.2-11b-vision-preview",
                messages=messages,
                temperature=0.1
            )
            raw_answer = res.choices[0].message.content
            return remove_foreign_characters(raw_answer)
        else:
            # 📝 محض ٹیکسٹ کے لیے Llama 3.3 / Llama 3 Fallback
            models_to_try = ["llama-3.3-70b-versatile", "llama3-8b-8192"]
            for model_name in models_to_try:
                try:
                    res = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt_text}
                        ],
                        temperature=0.1
                    )
                    raw_answer = res.choices[0].message.content
                    return remove_foreign_characters(raw_answer)
                except Exception as e:
                    if "rate_limit" in str(e).lower():
                        continue
                    else:
                        st.error(f"کنیکشن یا API کا مسئلہ ہے۔ تفصیل: {str(e)}")
                        return None
            st.error("معذرت! تمام AI ماڈلز کی روزانہ کی لمٹ ختم ہو چکی ہے۔ کچھ دیر بعد کوشش کریں یا نئی API Key استعمال کریں۔")
            return None
            
    except Exception as e:
        st.error(f"کنیکشن یا API کا مسئلہ ہے۔ تفصیل: {str(e)}")
        return None

# --- پراسیسنگ اور AI رسپانس ---
if action_prompt:
    clean_input_text = user_input.strip()
    if not clean_input_text and not image_bytes:
        st.warning("ارسلان بھائی، پہلے ٹیکسٹ باکس میں اپنا سوال درج کریں یا کوئی فائل/تصویر اپ لوڈ کریں!")
    else:
        with st.spinner('EduGuide AI Urdu جواب تیار کر رہا ہے...'):
            ans = fetch_ai_response(action_prompt, image_bytes)
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
                    simplified_ans = fetch_ai_response(simplify_prompt, image_bytes)
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
st.caption("EduGuide AI: Urdu Learning & Assessment Assistant | Developed by Arsalan Mustafa for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")
