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

# --- 🎯 غیر ملکی اور فضول حروف ہٹانے کا فنکشن ---
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

# --- 🔊 اردو ٹیکسٹ ٹو سپیچ فنکشن ---
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
    
    st.subheader("🏛️ 1️⃣ تعلیمی بورڈ کی سلیکشن (Board)")
    selected_board = st.selectbox(
        "اپنا تعلیمی بورڈ منتخب کریں:",
        [
            "سندھ بورڈ (BIEK / BSEK Karachi)",
            "پنجاب بورڈ (BISE Lahore / Rawalpindi etc.)",
            "فیڈرل بورڈ (FBISE Islamabad)",
            "آغا خان بورڈ (AKU-EB)",
            "O / A Levels (Cambridge System)",
            "عام / عمومی (General Education)"
        ]
    )
    
    st.subheader("🎯 2️⃣ مضمون کا انتخاب (Subject)")
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
    
    st.subheader("📊 3️⃣ سطح کا انتخاب (Difficulty)")
    selected_level = st.select_slider(
        "لیول منتخب کریں:",
        options=["ابتدائی (Primary/Middle)", "میٹرک / انٹرمیڈیٹ (High School)", "یونیورسٹی / ایڈوانسڈ (Undergrad)"],
        value="میٹرک / انٹرمیڈیٹ (High School)"
    )
    
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

# --- dynamic SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
تمہارا نام 'EduGuide AI' ہے۔ تم پاکستان کے طلباء کے لیے ایک انتہائی محتاط اور سمارٹ AI تعلیمی معاون ہو۔
یہ پروجیکٹ الخدمت فاؤنڈیشن، بنو قابل (Bano Qabil 3.0) اور علی بابا کلاؤڈ (Alibaba Cloud AI Hackathon 2026) کے لیے تیار کیا گیا ہے۔

موجودہ سیشن کی معلومات:
- منتخب کردہ بورڈ/نصاب: "{selected_board}"
- منتخب کردہ مضمون: "{selected_subject}"
- منتخب کردہ تعلیمی لیول: "{selected_level}"

🛑 **سخت ترین مضمون کی وریفیکیشن کے قواعد (STRICT SUBJECT MATCH RULE):**
1. اگر منتخب کردہ مضمون 'عمومی / دیگر (General)' کے علاوہ کوئی مخصوص مضمون ہے، تو سب سے پہلے صارف کے دیے گئے متن/سوال/تصویر کی جانچ کرو۔
2. اگر صارف کا سوال چنے گئے مضمون سے تعلق **نہیں** رکھتا، تو تم **ہرگز سوال کا جواب نہیں دو گے**۔
3. عدم مطابقت (Mismatch) کی صورت میں صرف یہ پیغام دو:
   "⚠️ **مضمون میں عدم مطابقت (Subject Mismatch)!**
   آپ نے سائڈ بار میں '**{selected_subject}**' منتخب کیا ہے، جبکہ آپ کا سوال کسی اور مضمون سے متعلق ہے۔ براہِ کرم درست مضمون چوئس کریں۔"

📜 **سخت ترین تحریری و زبان کے قواعد:**
1. تمام جوابات **صرف اور صرف خالص اور سلیس اردو رسم الخط (Urdu Script)** میں ہونے چاہئیں۔
2. تمام جوابات بالکل منتخب کردہ بورڈ ("{selected_board}") کے پیٹرن اور نصاب کے مطابق تیار کرو۔
3. جواب میں کوئی اضافی، فضول یا غیر متعلقہ جملے شامل نہ کرو۔
4. جب بھی ممکن ہو، تکنیکی انگریزی الفاظ کا اردو ترجمہ **"🔤 اہم تکنیکی الفاظ (Glossary)"** کی ہیڈنگ کے ساتھ لازمی بنائیں۔
"""

# --- مین انٹرفیس ---
st.title("🚀 EduGuide AI: Urdu Learning & Assessment Assistant")
st.markdown("##### **الخدمت فاؤنڈیشن، بنو قابل اور علی بابا کلاؤڈ ہیکاتھون 2026 کا خصوصی پروجیکٹ**")

# --- 📁 فائل اور تصویر اپ لوڈر ---
st.subheader("📄 فائل یا تصویر اپ لوڈ کریں (اختیاری):")
uploaded_file = st.file_uploader(
    "اپنی PDF، TXT فائل یا سوال/فارمولا/نوٹس کی تصویر اپ لوڈ کریں:", 
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
    "اپنا تعلیمی سوال، ٹاپک یا ہدایت یہاں درج کریں:", 
    value=file_extracted_text if file_extracted_text else "",
    height=140,
    placeholder="یہاں اپنا سوال، ریاضی کا فارمولا، یا نوٹس درج کریں..."
)

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
            st.error("تصویر پروسیسنگ کا ماڈل دستیاب نہیں ہے۔ براہ کرم صرف متن درج کریں۔")
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
            st.error("تمام AI ماڈلز کی روزانہ کی لمٹ ختم ہو چکی ہے۔ کچھ دیر بعد کوشش کریں۔")
            return None
            
    except Exception as e:
        st.error(f"API کی کا مسئلہ ہے: {str(e)}")
        return None

# --- 🚀 مرکزی جواب حاصل کرنے کا بٹن ---
if st.button("🚀 جواب حاصل کریں (Get Answer)", use_container_width=True, type="primary"):
    clean_input_text = user_input.strip()
    if not clean_input_text and not image_bytes:
        st.warning("ارسلان بھائی، پہلے ٹیکسٹ باکس میں اپنا سوال درج کریں یا کوئی فائل/تصویر اپ لوڈ کریں!")
    else:
        with st.spinner('EduGuide AI جواب تیار کر رہا ہے...'):
            main_prompt = f"برائے مہربانی {selected_board} کے نصاب کے مطابق درج ذیل سوال/ٹاپک کا سلیس اردو میں تفصیلی اور جامع جواب دیں:\n\n{user_input}"
            ans = fetch_ai_response(main_prompt, image_bytes)
            if ans:
                st.session_state.last_answer = ans

# --- 📋 جواب اور ایجوکیشنل ٹولز کا ڈسپلے ---
if st.session_state.last_answer:
    st.divider()
    st.subheader("📋 EduGuide AI کا تعلیمی جواب:")
    st.markdown(st.session_state.last_answer)
    
    # اگر عدم مطابقت کا پیغام نہ ہو صرف تب ایجوکیشنل ٹولز اور آپشنز دکھائیں
    if "مضمون میں عدم مطابقت" not in st.session_state.last_answer:
        st.divider()
        st.subheader("🎓 اس جواب پر مزید ایجوکیشنل AI ٹولز استعمال کریں:")
        st.caption("مندرجہ بالا جواب کو مزید بہتر بنانے یا پروسیس کرنے کے لیے نیچے دیے گئے بٹنز پر کلک کریں:")
        
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        
        tool_prompt = None
        
        with row1_col1:
            if st.button("🔍 1. مزید آسان اردو میں سمجھائیں", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس جواب کو اور زیادہ سادہ، عام فہم اور روزمرہ کی آسان مثالوں میں دوبارہ لکھیں:\n\n{st.session_state.last_answer}"
        
        with row1_col2:
            if st.button("📅 2. AI اسٹڈی پلانر بنائیں", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس تعلیمی جواب اور مضمون کی روشنی میں {selected_board} کے امتحان کی تیاری کا ایک منظم 15 دن کا اسٹڈی پلانر (Study Roadmap) تیار کریں:\n\n{st.session_state.last_answer}"
        
        with row1_col3:
            if st.button("📝 3. مکمل ماڈل پیپر جنریٹ کریں", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس حاصل شدہ جواب کے ٹاپک پر {selected_board} کے ایگزام پیٹرن کے مطابق ایک مکمل ماڈل پیپر بنائیں جس میں 10 MCQs، 5 مختصر سوالات اور 2 تفصیلی سوالات ماڈل اردو جوابات کے ساتھ شامل ہوں:\n\n{st.session_state.last_answer}"
        
        with row2_col1:
            if st.button("🧪 4. Step-by-Step فارمولا حل", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس جواب میں موجود تمام فارمولوں یا ریاضی/فزکس کے مسائل کو Step-by-Step اور وضاحت کے ساتھ حل کریں:\n\n{st.session_state.last_answer}"
        
        with row2_col2:
            if st.button("💡 5. سوچنے کے لیے اشارہ (Hint) دیں", use_container_width=True):
                tool_prompt = f"اس جواب کی بنیاد پر طالب علم سے ایک سوال پوچھیں اور ساتھ میں ایک چھوٹا اشارہ (Hint) دیں تاکہ طالب علم خود سوچ کر جواب دینے کی کوشش کرے:\n\n{st.session_state.last_answer}"
        
        with row2_col3:
            if st.button("🔤 6. اہم تکنیکی الفاظ کی لغت", use_container_width=True):
                tool_prompt = f"برائے مہربانی اس جواب میں آنے والی تمام مشکل انگریزی و سائنس کی اصطلاحات کی ایک علیحدہ اردو لغت (Glossary) بمعہ تشریح بنائیں:\n\n{st.session_state.last_answer}"
        
        # اگر کسی ایجوکیشنل ٹول کا بٹن دبایا جائے
        if tool_prompt:
            with st.spinner('EduGuide AI منتخب کردہ ٹول کا پروسیس چلا رہا ہے...'):
                processed_ans = fetch_ai_response(tool_prompt, image_bytes)
                if processed_ans:
                    st.session_state.last_answer = processed_ans
                    st.rerun()

    # --- 🚀 اضافی ٹولز (Audio, Download, Copy) ---
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
