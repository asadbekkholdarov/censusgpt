import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware


from translit import (
    is_cyrillic,
    is_latin,
    cyr_to_latin,
    latin_to_cyr,
)

# ================== ENV ==================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY .env faylida topilmadi")

# ================== GEMINI ==================
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ================== DATASET ==================
with open("data.json", encoding="utf-8") as f:
    DATA = json.load(f)

CONTEXT = "\n".join(
    f"{i+1}. SAVOL: {item['question']} | JAVOB: {item['answer']}"
    for i, item in enumerate(DATA)
)

# ================== FASTAPI ==================
app = FastAPI(
    title="Gemini Q&A Chatbot API",
    description="Lotin va Kirill alifbosida ishlovchi chatbot",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend qayerda bo‘lsa ham
    allow_credentials=True,
    allow_methods=["*"],  # POST, GET, OPTIONS
    allow_headers=["*"],
)

# ================== SCHEMAS ==================
class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


# ================== CORE LOGIC ==================
def find_answer(user_question: str) -> str:
    prompt = f"""
Sen professional AI assistantsan.

VAZIFA:
- Foydalanuvchi savolining MAZMUNINI tahlil qil
- Quyidagi savol-javoblardan ENG MOSINI tanla
- FAQAT o‘sha savolning JAVOBINI qaytar
- Agar mos savol topilmasa: "Savol aniqlanmadi" deb yoz

Foydalanuvchi savoli:
{user_question}

SAVOL-JAVOBLAR:
{CONTEXT}

Faqat JAVOBNI yoz. Izoh yo‘q.
"""
    response = model.generate_content(prompt)
    return response.text.strip()
    # try:
    #     response = model.generate_content(prompt)
    #     return response.text.strip()
    # except Exception as e:
    #     print("API error:", e)
    #     # Local fallback: data.json ichidan qidirish
    #     for item in DATA:
    #         if user_question.lower() in item["question"].lower():
    #             return item["answer"]
    #     return "Savolingizga hozircha javob topilmadi. Iltimos, +998 (71) 202-8175 raqamiga bog‘laning."


# ================== ROUTES ==================
@app.get("/")
def root():
    return {
        "status": "OK",
        "message": "Gemini Chatbot API ishlayapti",
        "docs": "/docs",
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    user_question = req.question.strip()

    if not user_question:
        return {"answer": "Savol bo‘sh bo‘lishi mumkin emas"}

    answer = find_answer(user_question)

    if not answer or "aniqlanmadi" in answer.lower():
        return {"answer": "Savol aniqlanmadi"}

    # user yozgan alifboga moslashtirish
    if is_latin(user_question):
        answer = cyr_to_latin(answer)
    elif is_cyrillic(user_question):
        answer = latin_to_cyr(answer)

    return {"answer": answer}
