import streamlit as st
from groq import Groq
import sys
import os

# --- 1. اسٹریم لٹ پیج سیٹ اپ ---
st.set_page_config(
    page_title="EduGuide AI: Urdu Learning & Assessment Assistant",
    page_icon="🎓",
    layout="wide"
)

# --- 2. اردو سپورٹ اور انکوڈنگ فکس ---
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- 3. گروک اے پی آئی کی (Groq API Key) حاصل کرنا (Safe Method) ---
MY_GROQ_KEY = None

try:
    if "GROQ_API_KEY" in st.secrets:
        MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not MY_GROQ_KEY:
    MY_GROQ_KEY = os.getenv("GROQ_API_KEY", "YOUR_LOCAL_GROQ_KEY_HERE")

# --- 4. اپ گریڈڈ اور سخت لسانی پرامپٹ (Strict System Prompt) ---
SYSTEM_PROMPT = """
تمہارا نام 'EduGuide AI: Urdu Learning & Assessment Assistant' ہے۔ تم پاکستان کے طلباء کے لیے ایک سمارٹ AI تعلیمی معاون اور اسسٹنٹ ہو۔
یہ پروجیکٹ الخدمت فاؤنڈیشن، بنو قابل (Bano Qabil 3.0) اور علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026) کے تحت پاکستان کے طلباء کے لیے تیار کیا گیا ہے۔

تمہاری 3 بنیادی ذمہ داریاں ہیں:
1. Urdu Concept Explainer: صارف کے دیے گئے کسی بھی تعلیمی سوال، مضمون یا انگریزی ٹاپک کو نہایت آسان، سلیس اور عام فہم اردو میں منتقل اور واضح کرنا۔
2. Urdu Text Summarizer: بڑی تعلیمی تحریر یا مضمون کا مختصر اور جامع خلاصہ (Key Points) اردو میں تیار کرنا۔
3. Urdu MCQ Quiz Generator: صارف کے فراہم کردہ ٹاپک یا تحریر پر 3 سے 5 کثیر الانتخابی سوالات (MCQs) جوابات اور وضاحت کے ساتھ بنانا۔

سخت لسانی اور تحریری قواعد (STRICT MANDATORY RULES):
1. تمام جوابات صرف اور صرف خالص اور سلیس اردو رسم الخط (Urdu Script) میں ہونے چاہئیں۔
2. چینی (Chinese)، عربی اعراب کی غلطیاں، یا بے معنی غیر ملکی حروف (Garbage Tokens/Foreign Characters) سخت منع ہیں۔
3. اگر صارف انگریزی میں بھی سوال یا متن فراہم کرے، تب بھی تمہارا جواب **100% خالص اور عام فہم اردو** میں ہونا چاہیے۔
4. رومن اردو، ہندی رسم الخط یا غیر ضروری انگلش مکسنگ سے پرہیز کریں۔
5. جوابات میں خوبصورت ہیڈنگز، بولڈ ٹیکسٹ اور بلٹ پوائنٹس کا استعمال کریں۔

کوئز (MCQ Quiz) کے لیے خاص ہدایات:
- جب صارف کوئز یا MCQs بنانے کا کہے، تو سوالات کے ساتھ 4 اختیارات (الف، ب، ج، د) بناؤ۔
- ہر سوال کے بالکل نیچے **"درست جواب:"** اور اس کی **"مختصر اردو وضاحت:"** لازمی لکھو تاکہ طالب علم اپنی خود احتسابی (Self-Assessment) کر سکے۔
"""

# --- سائڈ بار (برانڈنگ اور کریڈٹس) ---
with st.sidebar:
    st.title("🚀 EduGuide AI Urdu")
    st.caption("Urdu Learning & Assessment Assistant")
    st.divider()
    
    st.subheader("🛠️ بنیادی فیچرز")
    st.markdown("""
    1. **مفاہیم کی اردو وضاحت** 📚
    2. **تعلیمی تحریر کا خلاصہ (Summarizer)** 📝
    3. **خودکار اردو MCQ ٹیسٹ و جوابات** 🧠
    4. **دو لسانی ترجمہ و تشریح** 🔄
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
st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کے لیے تیار کردہ سمارٹ حل**")
st.write("تعلیم میں زبان کی رکاوٹ کو دور کرنے اور سلیس اردو میں سیکھنے و ٹیسٹ دینے کا جدید ترین ذریعہ۔")

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
        set_query("مندرجہ ذیل ٹاپک کا مختصر اور جامع اردو خلاصہ بنائیں: Artificial Intelligence in Modern Education")

with col_btn3:
    if st.button("🧠 اردو MCQ کوئز جنریٹ کریں"):
        set_query("کمپیوٹر نیٹ ورکس (Computer Networks) کے بنیادی مفاہیم پر 4 اردو MCQs بنائیں، اختیارات دیں اور ساتھ میں درست جواب اور اس کی وضاحت بھی درج کریں۔")

# ان پٹ باکس
user_query = st.text_area("اپنا تعلیمی سوال، مضمون یا ٹیکسٹ یہاں درج کریں:", value=st.session_state.user_input, height=130)

# --- پراسیسنگ ---
if st.button("AI سے جواب حاصل کریں 🔍", type="primary"):
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
                    temperature=0.2, # خالص اور مستحکم اردو کے لیے
                    top_p=0.9
                )
                answer = res.choices[0].message.content
                
                st.divider()
                st.subheader("📋 EduGuide AI Urdu کا جواب:")
                st.markdown(answer)
                                
        except Exception as e:
            st.error(f"کنیکشن یا API کا مسئلہ ہے۔ تفصیل: {str(e)}")

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Urdu Learning & Assessment Assistant | Developed by Arsalan for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")