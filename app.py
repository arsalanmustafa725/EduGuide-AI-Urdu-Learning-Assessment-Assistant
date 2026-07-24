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

# --- 🎯 غیر ملکی حروف ہٹانے کا فنکشن ---
def remove_foreign_characters(text):
    if not text:
        return ""
    pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\u0900-\u097f]+'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

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

# --- 4. سخت ترین لسانی پرامپٹ ---
SYSTEM_PROMPT = """
تمہارا نام 'EduGuide AI' ہے۔ تم پاکستان کے طلباء کے لیے ایک سمارٹ AI تعلیمی معاون ہو۔
یہ پروجیکٹ الخدمت فاؤنڈیشن، بنو قابل (Bano Qabil 3.0) اور علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026) کے لیے تیار کیا گیا ہے۔

سخت ترین تحریری قواعد:
1. تمام جوابات صرف اور صرف خالص اور سلیس **اردو رسم الخط** (Urdu Script) میں ہونے چاہئیں۔
2. چینی یا کسی دوسری غیر متعلقہ زبان کے حروف استعمال کرنا بالکل منع ہے۔
3. اگر صارف انگریزی میں سوال پوچھے، تب بھی جواب **100% سلیس اور عام فہم اردو** میں ہی دینا ہے۔
4. کوئز (MCQs) کی صورت میں 4 اختیارات (الف، ب، ج، د)، **درست جواب** اور **مختصر اردو وضاحت** لازمی لکھیں۔
5. خوبصورت Markdown ہیڈنگز اور بلٹ پوائنٹس استعمال کریں۔
"""

# --- سائڈ بار ---
with st.sidebar:
    st.title("🚀 EduGuide AI Urdu")
    st.caption("Urdu Learning & Assessment Assistant")
    st.divider()
    
    st.subheader("🛠️ بنیادی فیچرز")
    st.markdown("""
    1. **مفاہیم کی اردو وضاحت** 📚
    2. **تعلیمی تحریر کا خلاصہ (Summarizer)** 📝
    3. **خودکار اردو MCQ ٹیسٹ و جوابات** 🧠
    4. **پی ڈی ایف و ٹیکسٹ فائل پروسیسنگ** 📄
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

# --- مین انٹرفیس ---
st.title("🚀 EduGuide AI: Urdu Learning & Assessment Assistant")
st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کا خصوصی پروجیکٹ**")
st.write("تعلیم میں زبان کی رکاوٹ کو دور کرنے اور سلیس اردو میں سیکھنے و ٹیسٹ دینے کا جدید ترین حل۔")

# --- 📁 1️⃣ فیچر: PDF اور TXT فائل اپ لوڈر ---
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
act_col1, act_col2, act_col3 = st.columns(3)

action_prompt = None

with act_col1:
    if st.button("🔍 آسان اردو میں وضاحت کریں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن یا سوال کی آسان اور سلیس اردو میں تفصیلی وضاحت کریں:\n\n{user_input}"

with act_col2:
    if st.button("📝 مختصر اردو خلاصہ (Summary) بنائیں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن کا اہم نکات پر مشتمل مختصر اور جامع اردو خلاصہ بنائیں:\n\n{user_input}"

with act_col3:
    if st.button("🧠 اردو MCQ کوئز جنریٹ کریں", use_container_width=True):
        action_prompt = f"برائے مہربانی مندرجہ ذیل متن/ٹاپک کی بنیاد پر 4 کثیر الانتخابی سوالات (MCQs) بنائیں، اختیارات دیں اور ہر سوال کے نیچے درست جواب اور مختصر اردو وضاحت بھی درج کریں:\n\n{user_input}"

# --- پراسیسنگ اور AI رسپانس ---
if action_prompt:
    clean_input_text = user_input.strip()
    
    if not clean_input_text:
        st.warning("ارسلان بھائی، پہلے ٹیکسٹ باکس میں اپنا سوال درج کریں یا کوئی فائل اپ لوڈ کریں!")
    elif not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key غائب ہے! Streamlit Secrets میں API Key شامل کریں۔")
    else:
        try:
            with st.spinner('EduGuide AI Urdu جواب تیار کر رہا ہے...'):
                client = Groq(api_key=MY_GROQ_KEY)
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": action_prompt}
                    ],
                    temperature=0.1
                )
                
                raw_answer = res.choices[0].message.content
                pure_urdu_answer = remove_foreign_characters(raw_answer)
                
                st.divider()
                st.subheader("📋 EduGuide AI Urdu کا جواب:")
                st.markdown(pure_urdu_answer)
                
                # --- 🚀 اضافی فیچرز (Audio, Download, Copy) ---
                st.divider()
                st.subheader("🛠️ اضافی ٹولز (Extra Features):")
                
                feat_col1, feat_col2 = st.columns(2)
                
                # 🔊 2️⃣ فیچر: آڈیو میں سنیں (Audio Player)
                with feat_col1:
                    st.markdown("##### 🔊 جواب آڈیو میں سنیں:")
                    audio_fp = generate_urdu_audio(pure_urdu_answer)
                    if audio_fp:
                        st.audio(audio_fp, format='audio/mp3')
                    else:
                        st.info("آڈیو جنریٹ نہیں ہو سکی۔")
                
                # 📥 3️⃣ فیچر: نتیجہ ڈاؤن لوڈ کریں (Download Button)
                with feat_col2:
                    st.markdown("##### 📥 نتیجہ ڈاؤن لوڈ کریں:")
                    st.download_button(
                        label="📄 جواب ٹیکسٹ فائل (.txt) میں ڈاؤن لوڈ کریں",
                        data=pure_urdu_answer,
                        file_name="EduGuide_AI_Response.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                # 📋 4️⃣ فیچر: کاپی ٹو کلپ بورڈ (Copy Box)
                st.markdown("##### 📋 متن کاپی کرنے کے لیے نیچے دیے گئے باکس کے اوپر Copy آئیکن پر کلک کریں:")
                st.code(pure_urdu_answer, language=None)
                                
        except Exception as e:
            st.error(f"کنیکشن یا API کا مسئلہ ہے۔ تفصیل: {str(e)}")

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Urdu Learning & Assessment Assistant | Developed by Arsalan for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")
