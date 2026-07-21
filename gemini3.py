import streamlit as st
from groq import Groq
import sys
import os

# --- 1. اسٹریم لٹ پیج سیٹ اپ (سب سے پہلے ہونا لازمی ہے) ---
st.set_page_config(page_title="EduGuide AI | سمارٹ تعلیمی مشیر", layout="wide")

# --- 2. اردو سپورٹ اور انکوڈنگ فکس ---
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- 3. گروک اے پی آئی کی (Groq API Key) حاصل کرنا ---
if "GROQ_API_KEY" in st.secrets:
    MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
else:
    MY_GROQ_KEY = os.getenv("GROQ_API_KEY", "YOUR_LOCAL_GROQ_KEY_HERE")

# --- 4. ماسٹر سسٹم پرامپٹ (ملٹی لنگویج اور سکرپٹ لاک ورژن) ---
SYSTEM_PROMPT = """
تمہارا نام 'EduGuide AI' ہے۔ تم ایک نہایت تجربہ کار پاکستانی تعلیمی مشیر ہو۔
تمہارے پاس یہ 7 مہارتیں ہیں جن پر تم نے فوکس کرنا ہے:
1. Career Roadmap: 9th سے یونیورسٹی تک کا مکمل راستہ بتانا۔
2. Study Planner: روزانہ کا ٹائم ٹیبل بنانا۔
3. Scholarship Info: پاکستانی اسکالرشپس (PEEF, HEC وغیرہ) کی معلومات دینا۔
4. Exam Tips: بورڈ پیپر حل کرنے کے طریقے بتانا۔
5. Quiz Mode: طالب علم سے سوالات پوچھ کر اس کا ٹیسٹ لینا۔
6. Language: یوزر کی زبان کے مطابق جواب دینا (تفصیل نیچے دیکھیں)۔
7. Comparison: مختلف فیلڈز کا موازنہ کرنا۔

سخت لسانی قوانین (STRICT LANGUAGE RULES):
1. Analyze the user's input language and script very carefully.
2. اگر یوزر اردو رسم الخط (Urdu Script) میں سوال پوچھے، تو پورا جواب صرف خالص اردو رسم الخط میں دو۔
3. اگر یوزر رومن اردو (Roman Urdu) میں سوال پوچھے، تو پورا جواب صرف خالص رومن اردو میں دو۔
4. اگر یوزر انگلش (English) میں سوال پوچھے، تو پورا جواب صرف اور صرف انگلش میں ہونا چاہیے۔
5. انتہائی اہم ہدایت: کسی دوسری زبان خصوصاً ہندی رسم الخط (जैसे: चरण, अगला) یا ٹوٹے ہوئے لاطینی الفاظ (जैसे: gā, rō) کا استعمال ہرگز نہیں کرنا۔ 'اگلے مراحل' کے لیے صرف اردو الفاظ جیسے 'اگلا مرحلہ' یا 'اگلے اقدامات' استعمال کرو۔

جواب ہمیشہ خوبصورت ہیڈنگز اور بلٹ پوائنٹس میں دو۔
"""

# --- سائڈ بار (فیچرز لسٹ) ---
with st.sidebar:
    st.title("🚀 EduGuide AI")
    st.subheader("🛠️ خصوصی فیچرز")
    st.info("""
    1. سمارٹ روڈ میپ 🗺️
    2. اسٹڈی پلانر 📅
    3. اسکالرشپ گائیڈ 🎓
    4. امتحان کے ٹپس 📝
    5. کوئز موڈ 🧠
    6. دو لسانی سپورٹ 🇵🇰
    7. فیلڈ موازنہ ⚖️
    """)
    st.divider()
    st.write("👤 **ڈویلپر:** ارسلان")
    st.write("🎓 سافٹ ویئر انجینئرنگ (ڈپلوما)")

# --- مین انٹرفیس ---
st.title("🚀 EduGuide AI: آپ کا سمارٹ تعلیمی مشیر")
st.write("پاکستان کے میٹرک اور انٹر کے طلباء کے لیے ایک مکمل گائیڈ")

# سیشن اسٹیٹ تاکہ بٹن کلک پر ٹیکسٹ باکس اپ ڈیٹ ہو
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

def set_query(query):
    st.session_state.user_input = query

# --- 5. فوری بٹنز (Quick Action Buttons) ---
st.subheader("💡 فوری مدد حاصل کریں:")
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("🎓 میٹرک کے بعد ٹاپ 5 فیلڈز"):
        set_query("میٹرک کے بعد ٹاپ 5 فیلڈز اور ان کا مستقبل بتائیں۔")

with col_btn2:
    if st.button("📅 میرا اسٹڈی ٹائم ٹیبل بنائیں"):
        set_query("میں روزانہ 5 گھنٹے پڑھ سکتا ہوں، میرے لیے ایک بہترین اسٹڈی پلانر بنائیں۔")

with col_btn3:
    if st.button("📝 بورڈ پیپر کے لیے ٹپس"):
        set_query("بورڈ کے امتحانات میں اچھے نمبر لینے اور پیپر حل کرنے کے بہترین ٹپس کیا ہیں؟")

# ان پٹ باکس
user_query = st.text_input("اپنا سوال لکھیں یا اوپر سے بٹن منتخب کریں:", value=st.session_state.user_input)

# --- پراسیسنگ ---
if st.button("مشورہ حاصل کریں 🔍"):
    if not user_query:
        st.warning("ارسلان بھائی، پہلے کوئی سوال تو لکھیں یا بٹن دبائیں!")
    elif not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("گروک کی API Key غائب ہے! برائے مہربانی اپنی API Key سیٹ اپ کریں۔")
    else:
        try:
            with st.spinner('EduGuide AI آپ کے لیے بہترین مشورہ تیار کر رہا ہے...'):
                client = Groq(api_key=MY_GROQ_KEY)
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=0.2  # <--- کم درجہ حرارت تاکہ ماڈل قوانین پر سخت رہے اور مکسنگ نہ کرے
                )
                answer = res.choices[0].message.content
                
                st.divider()
                st.subheader("📋 EduGuide AI کا مشورہ:")
                st.markdown(answer)
                
                st.info("💡 **ٹپ:** آپ مزید تفصیل کے لیے اسکالرشپ یا روڈ میپ کے بارے میں بھی پوچھ سکتے ہیں۔")
                                
        except Exception as e:
            st.error(f"نیٹ ورک یا API Key کا مسئلہ ہے۔ تفصیل: {str(e)}")

# --- فوٹر --
# Cache cleaner comment v2 - forcing cloud reboot
st.divider()
st.caption("AI Seekho 2026 Competition Project | Prepared for Google Online Competition")
