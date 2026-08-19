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
    
    st.subheader("🏛️ 2️⃣ تعلیمی بورڈ کا انتخاب (Board)")
    selected_board = st.selectbox(
        "اپنا تعلیمی بورڈ منتخب کریں:",
        [
            "سندھ بورڈ (BIEK / BSEK)",
            "پنجاب بورڈ (BISE)",
            "فیڈرل بورڈ (FBISE)",
            "آغا خان بورڈ (AKU-EB)",
            "O/A Levels (Cambridge)"
        ]
    )
    
    st.subheader("📊 3️⃣ سطح کا انتخاب (Difficulty)")
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
    4. **AI اسٹڈی و ایگزام پلانر** 📅
    5. **خودکار امتحانی پیپر جنریٹر** 📝
    6. **میتھ و سائنس سٹیپ بائی سٹیپ سولور** 📐
    7. **ہنٹ و سیلف کریکشن سسٹم** 💡
    8. **تکنیکی الفاظ کی لغت (Glossary)** 🔤
    """)
    st.divider()
    
    st.subheader("🤝 معاون و سرپرست")
    st.markdown("""
    * 🌟 **الخدمت فاؤنڈیشن (Alkhidmat Foundation)**
    * 🚀 **بنو قابل 3.0 (Bano Qabil)**
    * ☁️ **علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026)**
    """)
    st.divider()
    
    st.write("👤 **ڈویلپر:** ارسلان مصطفیٰ (Arsalan Mustafa)")
    st.write("🎓 AI & Software Development")

# --- dynamic SYSTEM PROMPT (سخت ترین ہدایات کے ساتھ) ---
SYSTEM_PROMPT = f"""
تمہارا نام 'EduGuide AI' ہے۔ تم پاکستان کے طلباء کے لیے ایک انتہائی محتاط اور سمارٹ AI تعلیمی معاون ہو۔
یہ پروجیکٹ الخدمت فاؤنڈیشن، بنو قابل (Bano Qabil 3.0) اور علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026) کے لیے تیار کیا گیا ہے۔

موجودہ سیشن کا منتخب کردہ مضمون: "{selected_subject}"
موجودہ سیشن کا منتخب کردہ بورڈ: "{selected_board}"
موجودہ سیشن کا منتخب کردہ تعلیمی لیول: "{selected_level}"

🛑 **سخت ترین مضمون کی وریفیکیشن کے قواعد (STRICT SUBJECT MATCH RULE):**
1. اگر منتخب کردہ مضمون 'عمومی / دیگر (General)' کے علاوہ کوئی مخصوص مضمون ہے (مثلاً فزکس، کیمسٹری، کمپیوٹر سائنس، بائیولوجی، ریاضی وغیرہ)، تو سب سے پہلے صارف کے دیے گئے متن/سوال/تصویر کی جانچ کرو۔
2. اگر صارف کا سوال چنے گئے مضمون سے تعلق **نہیں** رکھتا (مثال کے طور پر ڈراپ ڈاؤن میں '{selected_subject}' منتخب ہے لیکن سوال کسی دوسرے مضمون کا ہے)، تو تم **ہرگز سوال کا جواب نہیں دو گے**۔
3. عدم مطابقت (Mismatch) کی صورت میں تم صرف اور صرف یہ معذرت خواہی کا پیغام دو گے:
   "⚠️ **مضمون میں عدم مطابقت (Subject Mismatch)!**
   آپ نے سائڈ بار میں ڈراپ ڈاؤن سے '**{selected_subject}**' منتخب کیا ہے، جبکہ آپ کا سوال کسی اور مضمون سے متعلق محسوس ہو رہا ہے۔ 
   براہِ کرم سائڈ بار سے صحیح مضمون منتخب کریں تاکہ آپ کو درست اور صحیح تعلیمی جواب فراہم کیا جا سکے۔"

📜 **سخت ترین تحریری و زبان کے قواعد (STRICT LANGUAGE RULES):**
1. تمام جوابات **صرف اور صرف خالص اور سلیس اردو رسم الخط (Urdu Script)** میں ہونے چاہئیں۔
2. چینی، ہندی، جاپانی یا کسی بھی غیر متعلقہ غیر ملکی زبان کے حروف کا استعمال سخت منع ہے۔
3. اگر تصویر/متن میں ریاضی، فزکس یا کیمسٹری کا سوال ہے تو ہر مرحلے (Step-by-Step) کی آسان اردو میں وضاحت فراہم کرو۔
4. جواب کے آخر میں 3 سے 5 اہم تکنیکی الفاظ کا اردو ترجمہ **"🔤 اہم تکنیکی الفاظ (Glossary)"** کے نام سے لازمی بنائیں۔
"""

# --- AI کال کرنے کا فنکشن ---
def fetch_ai_response(prompt_text, img_data=None):
    if not MY_GROQ_KEY or MY_GROQ_KEY == "YOUR_LOCAL_GROQ_KEY_HERE":
        st.error("Groq API Key غائب ہے! Streamlit Secrets میں API Key شامل کریں۔")
        return None
    
    client = Groq(api_key=MY_GROQ_KEY)
    text_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    
    try:
        if img_data:
            vision_models = ["llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"]
            for v_model in vision_models:
                try:
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
                        model=v_model,
                        messages=messages,
                        temperature=0.1
                    )
                    raw_answer = res.choices[0].message.content
                    return remove_foreign_characters(raw_answer)
                except Exception:
                    continue
            st.error("تصویر پروسیس کرنے والا ماڈل اس وقت دستیاب نہیں ہے، صرف متن بھیجیں۔")
            return None
        else:
            for model_name in text_models:
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
                except Exception:
                    continue
            st.error("معذرت! تمام AI ماڈلز مصروف ہیں۔ کچھ دیر بعد کوشش کریں۔")
            return None
    except Exception as e:
        st.error(f"API کی کا مسئلہ ہے: {str(e)}")
        return None

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
    height=150,
    placeholder="یہاں اپنا سوال درج کریں یا تصویر/فائل کا انتخاب کریں..."
)

# --- 🎯 اہم تعلیمی فیچرز کا ٹیب سسٹم (Tabs Layout) ---
st.subheader("🎯 AI تعلیمی ٹولز (Educational Tools):")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 عام وضاحت و کوئز", 
    "📅 AI اسٹڈی پلانر", 
    "📝 خودکار پیپر جنریٹر", 
    "📐 میتھ و سائنس سولور", 
    "💡 ہنٹ و سیلف کریکشن"
])

action_prompt = None

# --- Tab 1: بنیادی ایکشنز ---
with tab1:
    act_col1, act_col2, act_col3, act_col4 = st.columns(4)
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
            action_prompt = f"برائے مہربانی مندرجہ ذیل متن/تصویر/ٹاپک کی بنیاد پر 3 مختصر امتحانی سوالات اور 2 تفصیلی سوالات ماڈل اردو جوابات کے ساتھ تیار کریں:\n\n{user_input}"

# --- Tab 2: 2️⃣ AI اسٹڈی اور ایگزام پلانر ---
with tab2:
    st.markdown("##### 📅 AI اسٹڈی اور ایگزام پلانر (Smart Study Planner)")
    plan_col1, plan_col2 = st.columns(2)
    with plan_col1:
        days = st.number_input("امتحان میں باقی دن:", min_value=1, max_value=90, value=15)
    with plan_col2:
        weak_topics = st.text_input("کمزور ٹاپکس (اگر کوئی ہیں):", placeholder="مثال: Dynamic Memory Allocation, Thermodynamics")
    
    if st.button("📅 روزانہ کا ٹائم ٹیبل بنائیں", use_container_width=True):
        action_prompt = f"طالب علم کے پاس {selected_subject} کا امتحان کی تیاری کے لیے کل {days} دن باقی ہیں۔ اس کے کمزور ٹاپکس یہ ہیں: {weak_topics}۔ براؤ کرم {selected_board} کے نصاب کے مطابق اس کے لیے روزانہ کا مکمل شیڈول اور تیاری کا روڈ میپ سلیس اردو میں تیار کریں۔\n\nاضافی متن: {user_input}"

# --- Tab 3: 3️⃣ خودکار امتحانی پیپر جنریٹر ---
with tab3:
    st.markdown("##### 📝 خودکار امتحانی پیپر جنریٹر (Mock Exam Generator)")
    if st.button("📄 مکمل ماڈل امتحانی پیپر جنریٹ کریں", use_container_width=True):
        action_prompt = f"برائے مہربانی {selected_board} اور {selected_level} کے پیٹرن پر {selected_subject} کا ایک مکمل ماڈل پیپر تیار کریں۔ اس میں شامل کریں:\n1. 10 کثیر الانتخابی سوالات (MCQs)\n2. 5 مختصر امتحانی سوالات (Short Questions)\n3. 2 تفصیلی سوالات (Long Questions)\nتمام سوالات کے جوابات اور وریفکیشن سلیس اردو میں فراہم کریں۔\n\nٹاپک/متن: {user_input}"

# --- Tab 4: 4️⃣ فارمولا اور ڈایاگرام ایکسپلاینر ---
with tab4:
    st.markdown("##### 📐 میتھ و سائنس سٹیپ بائی سٹیپ سولور (Math & Science Solver)")
    if st.button("🧩 فارمولا اور مساوات مرحلہ وار حل کریں", use_container_width=True):
        action_prompt = f"برائے مہربانی درج ذیل ریاضی، فزکس یا سائنس کے فارمولے/مساوات/تصویر کا سٹیپ بائی سٹیپ (Step-by-Step) حل اور ہر قدم کی سلیس اردو میں وضاحت فراہم کریں:\n\n{user_input}"

# --- Tab 5: 5️⃣ غلط جواب کی خودکار اصلاح و ہنٹ ---
with tab5:
    st.markdown("##### 💡 ہنٹ و اشارہ لیں (Self-Correction & Hint System)")
    student_ans = st.text_input("اپنا غلط یا نامکمل جواب یہاں درج کریں:")
    if st.button("💡 اشارہ (Hint) حاصل کریں", use_container_width=True):
        action_prompt = f"طالب علم کا سوال: {user_input}\nطالب علم کا جواب: {student_ans}\nبراہِ کرم فوراً صحیح جواب نہ بتائیں، بلکہ طالب علم کو ایک چھوٹا سا اشارہ (Hint) دیں اور اس کی غلطی کی نشاندہی سلیس اردو میں کریں تاکہ وہ خود درست جواب تک پہنچ سکے۔"

# --- 6️⃣ اردو اصطلاحات کی لغت (Glossary Tool) ---
st.divider()
if st.button("🔤 صرف اردو اصطلاحات کی لغت (Urdu Glossary) جنریٹ کریں", use_container_width=True):
    action_prompt = f"برائے مہربانی مندرجہ ذیل متن/ٹاپک میں سے تمام اہم انگریزی تعلیمی اور تکنیکی الفاظ کا انتخاب کریں اور ان کا سلیس اردو ترجمہ اور آسان مثالوں پر مشتمل ایک 'Interactive Urdu Glossary Table' بنائیں:\n\n{user_input}"

# --- پراسیسنگ اور AI رسپانس ---
if action_prompt:
    clean_input_text = user_input.strip()
    if not clean_input_text and not image_bytes and "روزانہ کا ٹائم ٹیبل" not in action_prompt and "مکمل ماڈل امتحانی پیپر" not in action_prompt:
        st.warning("ارسلان بھائی، پہلے ٹیکسٹ باکس میں اپنا سوال/ٹاپک درج کریں یا کوئی فائل/تصویر اپ لوڈ کریں!")
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
    
    if "مضمون میں عدم مطابقت" not in st.session_state.last_answer:
        st.divider()
        simp_col1, simp_col2 = st.columns([2, 1])
        with simp_col1:
            st.info("کیا یہ جواب تھوڑا مشکل محسوس ہو رہا ہے؟")
        with simp_col2:
            if st.button("🔄 اسے اور آسان اردو میں سمجھائیں", use_container_width=True):
                simplify_prompt = f"برائے مہربانی نیچے دیے گئے جواب کو انتہائی سادہ، بچوں جیسی عام فہم اردو اور روزمرہ کی آسان مثالوں میں دوبارہ لکھیں:\n\n{st.session_state.last_answer}"
                with st.spinner('جواب کو مزید آسان اردو میں تبدیل کیا جا رہا ہے...'):
                    simplified_ans = fetch_ai_response(simplify_prompt, image_bytes)
                    if simplified_ans:
                        st.session_state.last_answer = simplified_ans
                        st.rerun()

    # --- 🚀 اضافی ٹولز ---
    st.divider()
    st.subheader("🛠️ اضافی ٹولز (Extra Features):")
    
    feat_col1, feat_col2 = st.columns(2)
    
    with feat_col1:
        st.markdown("##### 🔊 جواب آڈیو میں سنیں:")
        audio_fp = generate_urdu_audio(st.session_state.last_answer)
        if audio_fp:
            st.audio(audio_fp, format='audio/mp3')
        else:
            st.info("آڈیو جنریٹ نہیں ہو سکی۔")
    
    with feat_col2:
        st.markdown("##### 📥 نتیجہ ڈاؤن لوڈ کریں:")
        st.download_button(
            label="📄 جواب ٹیکسٹ فائل (.txt) میں ڈاؤن لوڈ کریں",
            data=st.session_state.last_answer,
            file_name="EduGuide_AI_Response.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("##### 📋 متن کاپی کرنے کے لیے نیچے دیے گئے باکس کے اوپر Copy آئیکن پر کلک کریں:")
    st.code(st.session_state.last_answer, language=None)

# --- فوٹر ---
st.divider()
st.caption("EduGuide AI: Urdu Learning & Assessment Assistant | Developed by Arsalan Mustafa for Alibaba Cloud, Bano Qabil & Alkhidmat Foundation Hackathon 2026")
