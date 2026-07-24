import streamlit as st
from groq import Groq
import sys
import os
import re

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

# غیر ضروری یا چینی حروف فلٹر کرنے کا فنکشن
def clean_urdu_text(text):
    return re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df]+', '', text)

# --- 4. سسٹم پرامپٹ (System Prompt) ---
SYSTEM_PROMPT = """
تمہارا نام 'EduGuide AI: Urdu Learning & Assessment Assistant' ہے۔ تم پاکستان کے طلباء کے لیے ایک سمارٹ AI تعلیمی معاون ہو۔
یہ پروجیکٹ الخدمت فاؤنڈیشن، بنو قابل (Bano Qabil 3.0) اور علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026) کے لیے تیار کیا گیا ہے۔

سخت ترین لسانی اور تحریری قواعد (STRICT MANDATORY RULES):
1. تمام جوابات صرف اور صرف **خالص اور سلیس اردو** (Urdu Script) میں ہونے چاہئیں۔
2. چینی (Chinese)، غیر ضروری اعراب، یا بے معنی حروف سخت ممنوع ہیں۔
3. اگر صارف کا متن انگریزی میں ہے اور وہ خلاصہ، کوئز یا وضاحت مانگے، تو بھی تمہارا جواب **100% سلیس اردو** میں ہونا چاہیے۔
4. کوئز کی صورت میں سوالات، 4 اختیارات (الف، ب، ج، د)، **درست جواب** اور **مختصر اردو وضاحت** لازمی لکھیں۔
5. جواب میں Markdown ہیڈنگز اور بلٹ پوائنٹس استعمال کریں۔
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
st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کا خصوصی پروجیکٹ**")
st.write("تعلیم میں زبان کی رکاوٹ کو دور کرنے اور سلیس اردو میں سیکھنے و ٹیسٹ دینے کا جدید ترین حل۔")

# --- سیشن اسٹیٹ ہینڈلنگ (فکسڈ) ---
if "user_text" not in st.session_state:
    st.session_state["user_text"] = ""

def set_sample_text(text):
    st.session_state["user_text"] = text

# --- 5. سیمپل بٹنز (مثال کے لیے) ---
st.subheader("💡 اگر آپ کے پاس سوال نہیں ہے، تو مثال کے لیے نیچے کلک کریں:")
col_sample1, col_sample2, col_sample3 = st.columns(3)

with col_sample1:
    st.button(
        "📖 مثال 1: وضاحت", 
        on_click=set_sample_text, 
        args=("Photosynthesis (ضیاعی تالیف) کیا ہے؟ اس کو آسان اردو میں تفصیل سے سمجھائیں۔",)
    )

with col_sample2:
    st.button(
        "📝 مثال 2: خلاصہ", 
        on_click=set_sample_text, 
        args=("Artificial Intelligence is transforming modern education by providing personalized learning experiences, automating administrative tasks, and assisting students in overcoming language barriers.",)
    )

with col_sample3:
    st.button(
        "🧠 مثال 3: کوئز", 
        on_click=set_sample_text, 
        args=("کمپیوٹر نیٹ ورکس (Computer Networks) کے بنیادی مفاہیم پر 4 اردو MCQs بنائیں۔",)
    )

# ان پٹ باکس (Key کی مدد سے سیشن میں ڈائریکٹ محفوظ ہوگا)
user_input = st.text_area(
    "اپنا تعلیمی سوال، مضمون یا متن یہاں درج کریں:", 
    key="user_text", 
    height=140
)

# --- ایکشن بٹنز ---
st.subheader("🎯 اب منتخب کریں کہ اس متن کے ساتھ کیا کرنا ہے:")
act_col1, act_col2, act_col3 = st.columns(3)

action_type = None

with act_col1:
    if st.button("🔍 آسان اردو میں وضاحت کریں", use_container_width=True):
        action_type = "explain"

with act_col2:
    if st.button("📝 مختصر اردو خلاصہ (Summary) بنائیں", use_container_width=True):
        action_type = "summarize"

with act_col3:
    if st.button("🧠 اردو MCQ کوئز جنریٹ کریں", use_container_width=True):
        action_type = "quiz"

# --- پراسیسنگ اور AI رسپانس ---
if action_type:
    # براہ راست موجودہ ٹیکسٹ باکس سے ٹیکسٹ حاصل کریں
    current_text = st.session_state["user_text"].strip()
    
    if not current_text:
        st.warning("ارسلان بھائی، پہلے نیچے باکس میں کوئی متن یا سوال تو درج کریں!")
    elif not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key غائب ہے! Streamlit Secrets میں API Key شامل کریں۔")
    else:
        # پرامپٹ کی تیاری
        if action_type == "explain":
            action_prompt = f"مندرجہ ذیل متن یا سوال کی آسان اور سلیس اردو میں تفصیل سے وضاحت کریں:\n\n{current_text}"
        elif action_type == "summarize":
            action_prompt = f"مندرجہ ذیل متن کا اہم نکات پر مشتمل مختصر اور جامع اردو خلاصہ بنائیں:\n\n{current_text}"
        elif action_type == "quiz":
            action_prompt = f"مندرجہ ذیل متن/ٹاپک کی بنیاد پر 4 کثیر الانتخابی سوالات (MCQs) بنائیں، اختیارات دیں اور ہر سوال کے نیچے درست جواب اور مختصر اردو وضاحت بھی درج کریں:\n\n{current_text}"

        try:
            with st.spinner('EduGuide AI Urdu جواب تیار کر رہا ہے...'):
                client = Groq(api_key=MY_GROQ_KEY)
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": action_prompt}
                    ],
                    temperature=0.1,
                    top_p=0.8
                )
                raw_answer = res.choices[0].message.content
                clean_answer = clean_urdu_text(raw_answer)
                
                st.divider()
                st.subheader("📋 EduGuide AI Urdu کا جواب:")
                st.markdown(clean_answer)
                                
        except Exception as e:
            st.error(f"کنیکشن یا API کا مسئلہ ہے۔ تفصیل: {str(e)}")

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Urdu Learning & Assessment Assistant | Developed by Arsalan for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")
