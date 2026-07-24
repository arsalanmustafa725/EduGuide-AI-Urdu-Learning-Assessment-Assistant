import streamlit as st
from groq import Groq
import sys
import os

# --- 1. اسٹریم لٹ پیج سیٹ اپ ---
st.set_page_config(page_title="EduGuide AI Urdu | تعلیمی معاون", layout="wide")

# --- 2. اردو سپورٹ اور انکوڈنگ فکس ---
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- 3. گروک اے پی آئی کی (Groq API Key) حاصل کرنا (Safe Method) ---
MY_GROQ_KEY = None

# پہلے کلاؤڈ/لوکل secrets چیک کریں
try:
    if "GROQ_API_KEY" in st.secrets:
        MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# اگر secrets نہ ملے تو ماحول (Environment/Local) سے چیک کریں
if not MY_GROQ_KEY:
    MY_GROQ_KEY = os.getenv("GROQ_API_KEY", "YOUR_LOCAL_GROQ_KEY_HERE")

# --- 4. نیا اور اپ گریڈڈ سسٹم پرامپٹ (EduGuide AI Urdu) ---
SYSTEM_PROMPT = """
تمہارا نام 'EduGuide AI Urdu' ہے۔ تم پاکستان کے طلباء کے لیے ایک سمارٹ AI تعلیمی معاون اور اسسٹنٹ ہو۔
تمہارا بنیادی مقصد تعلیم میں زبان کی رکاوٹ کو ختم کرنا اور طلباء کی خود احتسابی (Assessment) میں مدد کرنا ہے۔

تمہاری 3 بنیادی ذمہ داریاں ہیں:
1. Urdu Concept Explainer: یوزر کے دیے گئے کسی بھی تعلیمی سوال، مضمون یا انگریزی ٹاپک کو نہایت آسان، سلیس اور عام فہم اردو میں منتقل اور واضح کرنا۔
2. Urdu Text Summarizer: بڑی تعلیمی تحریر یا مضمون کا مختصر اور جامع خلاصہ (Key Points) اردو میں تیار کرنا۔
3. Urdu MCQ Quiz Generator: یوزر کے فراہم کردہ ٹاپک یا تحریر پر 3 سے 5 کثیر الانتخابی سوالات (MCQs) جوابات اور وضاحت کے ساتھ بنانا۔

سخت لسانی قواعد (STRICT RULES):
1. تمام جوابات صرف اور صرف خالص اردو رسم الخط (Urdu Script) میں ہونی چاہئیں۔
2. رومن اردو، ہندی رسم الخط یا انگلش مکسنگ سے پرہیز کریں۔
3. جوابات میں خوبصورت ہیڈنگز، بولڈ ٹیکسٹ اور بلٹ پوائنٹس کا استعمال کریں۔
"""

# --- سائڈ بار ---
with st.sidebar:
    st.title("🚀 EduGuide AI Urdu")
    st.subheader("🛠️ پروجیکٹ کے بنیادی فیچرز")
    st.info("""
    1. آسان اردو میں مفاہیم کی وضاحت 📚
    2. تعلیمی تحریر کا خلاصہ (Summarizer) 📝
    3. خودکار اردو MCQ ٹیسٹ (Quiz) 🧠
    4. دو لسانی مواد کی تبدلی 🔄
    """)
    st.divider()
    st.write("👤 **ڈویلپر:** ارسلان")
    st.write("🎓 AI & Software Development")

# --- مین انٹرفیس ---
st.title("🚀 EduGuide AI Urdu: تعلیمی و تحصیلی معاون")
st.write("تعلیم میں زبان کی رکاوٹ کو دور کرنے اور آسان اردو میں سیکھنے کا سمارٹ حل")

if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

def set_query(query):
    st.session_state.user_input = query

# --- 5. فوری فیچر بٹنز ---
st.subheader("💡 فیچر منتخب کریں یا ڈائریکٹ سوال پوچھیں:")
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("📖 ٹاپک کی اردو میں وضاحت"):
        set_query("Photosynthesis (ضیاعی تالیف) کیا ہے؟ اس کو آسان اردو میں تفصیل سے سمجھائیں۔")

with col_btn2:
    if st.button("📝 نالج کا خلاصہ (Summary)"):
        set_query("مندرجہ ذیل ٹاپک کا مختصر اردو خلاصہ بنائیں: Artificial Intelligence in Modern Education")

with col_btn3:
    if st.button("🧠 اردو MCQ کوئز جنریٹ کریں"):
        set_query("کمپیوٹر نیٹ ورکس (Computer Networks) کے بنیادی مفاہیم پر 4 اردو MCQs بنائیں اور نیچے ان کے درست جوابات بھی دیں۔")

# ان پٹ باکس
user_query = st.text_area("اپنا تعلیمی سوال، مضمون یا ٹیکسٹ یہاں درج کریں:", value=st.session_state.user_input, height=120)

# --- پراسیسنگ ---
if st.button("AI سے جواب حاصل کریں 🔍"):
    if not user_query:
        st.warning("ارسلان بھائی، پہلے کوئی ٹیکسٹ یا سوال تو درج کریں!")
    elif not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key غائب ہے! Streamlit Secrets میں API Key شامل کریں۔")
    else:
        try:
            with st.spinner('EduGuide AI Urdu جواب اور ٹیسٹ تیار کر رہا ہے...'):
                client = Groq(api_key=MY_GROQ_KEY)
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=0.3
                )
                answer = res.choices[0].message.content
                
                st.divider()
                st.subheader("📋 EduGuide AI Urdu کا جواب:")
                st.markdown(answer)
                                
        except Exception as e:
            st.error(f"کنیکشن یا API کا مسئلہ ہے۔ تفصیل: {str(e)}")

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI Urdu | Developed for Alibaba Cloud & Bano Qabil AI Hackathon 2026")