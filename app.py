
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

# --- 🎯 100% پکا فلٹر: تمام چینی، دیوناگری اور غیر ملکی حروف ہٹانے کا فنکشن ---
def remove_foreign_characters(text):
    if not text:
        return ""
    # چینی، جاپانی، کورین اور دیوناگری حروف کو کاٹ کر صاف کرنا
    pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u0900-\u097F]+'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

# --- 4. سخت ترین لسانی پرامپٹ ---
SYSTEM_PROMPT = """
تمہارا نام 'EduGuide AI' ہے۔ تم پاکستان کے طلباء کے لیے ایک سمارٹ AI تعلیمی معاون ہو۔
یہ پروجیکٹ الخدمت فاؤنڈیشن، بنو قابل (Bano Qabil 3.0) اور علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026) کے لیے تیار کیا گیا ہے۔

سخت ترین تحریری قواعد:
1. تمام جوابات صرف اور صرف خالص اور سلیس **اردو رسم الخط** (Urdu Script) میں ہونے چاہئیں۔
2. اگر صارف انگریزی میں سوال پوچھے، تب بھی جواب **100% سلیس اور عام فہم اردو** میں ہی دینا ہے۔
3. کوئز (MCQs) کی صورت میں 4 اختیارات (الف، ب، ج، د)، **درست جواب** اور **مختصر اردو وضاحت** لازمی لکھیں۔
4. خوبصورت Markdown ہیڈنگز اور بلٹ پوائنٹس استعمال کریں۔
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

# --- ان پٹ باکس ---
user_input = st.text_area(
    "اپنا تعلیمی سوال، مضمون یا متن یہاں درج کریں:", 
    height=150,
    placeholder="یہاں اپنا سوال یا مضمون درج کریں..."
)

# --- اکشن بٹنز ---
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
        st.warning("ارسلان بھائی، پہلے ٹیکسٹ باکس میں اپنا سوال یا مضمون درج کریں!")
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
                
                # 🔥 سکرین پر دکھانے سے پہلے تمام چینی حروف صاف کرنا
                pure_urdu_answer = remove_foreign_characters(raw_answer)
                
                st.divider()
                st.subheader("📋 EduGuide AI Urdu کا جواب:")
                st.markdown(pure_urdu_answer)
                                
        except Exception as e:
            st.error(f"کنیکشن یا API کا مسئلہ ہے۔ تفصیل: {str(e)}")

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Urdu Learning & Assessment Assistant | Developed by Arsalan for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")
