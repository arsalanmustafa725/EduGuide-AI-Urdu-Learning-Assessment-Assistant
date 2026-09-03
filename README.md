# EduGuide AI: Urdu & International Learning & Assessment Assistant

An intelligent, multimodal educational assistant developed for the **Alibaba Cloud AI Hackathon Pakistan 2026** in collaboration with **Alkhidmat Foundation** and the **Bano Qabil Platform**. EduGuide AI is specifically engineered to empower students and educators with AI-driven learning tools, multilingual support (Urdu & English), and dynamic assessments.

---

## 🚀 Key Features & Capabilities

- **Multilingual Support (Urdu & English):** Fully supports 100% pure Urdu generation and English content without mixing, complete with dynamic RTL (Right-to-Left) formatting and Noto Nastaliq Urdu typography.
- **Multimodal AI Processing:** Powered by Groq and Llama vision models (`llama-3.2-11b-vision-preview`, `llama-3.2-90b-vision-preview`) to solve textbook problems and questions directly from uploaded images[cite: 1].
- **Voice-to-Text & Text-to-Speech:** Integrated Whisper (`whisper-large-v3-turbo`) for voice queries and gTTS for instant audio playback of explanations.
- **Dynamic AI Quiz Engine:** Automatically generates live multiple-choice questions (MCQs) and tracks scores interactively.
- **Smart Revision Flashcards:** Generates key revision flashcards and definitions dynamically from learning topics.
- **Saved Answers (Favorites):** Persistent local storage using JSON to save and review important educational answers anytime.
- **Advanced Educational Tools:** Includes simplified explanations, AI study roadmaps, model paper generators, step-by-step math breakdowns, and Socratic tutor modes.

---

## 🛠️ Technology Stack

- **Frontend & UI:** Streamlit (with custom CSS, dynamic direction toggling, and responsive design)
- **AI & LLM Inference:** Groq API (`llama-3.1-8b-instant`, `llama-3.3-70b-versatile`)
- **Speech & Vision Processing:** Whisper AI, gTTS, Pillow (PIL), PyPDF2
- **Data Persistence:** JSON-based local caching for saved favorites

---

## 📌 Installation & Local Setup

Follow these steps to run the project locally on your machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/EduGuide-AI.git](https://github.com/your-username/EduGuide-AI.git)
   cd EduGuide-AI
