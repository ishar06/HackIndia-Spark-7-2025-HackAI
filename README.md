
# 🚀 FormEase – Your AI-Powered Productivity Assistant

Welcome to **FormEase**, a powerful, all-in-one AI assistant that helps users manage documents, summarize content, generate resumes, and stay productive — all through a smart chat interface powered by LLMs.

🎯 Built for **HackIndia 2025** by **Team HackAI**  
🔗 Hashtags: #HackIndia2025 #HackIndia

---

## 📌 Features

### 📝 1. PDF Summarizer
Upload any PDF document and receive a concise summary in bullet points. This saves time and helps users understand the content quickly without reading lengthy text.

- ⚙️ **Tech Used**: PyMuPDF (`fitz`) for PDF parsing, Ollama for summary generation.

---

### ❓ 2. Q&A over Documents (PDFs, DOCs, PPTs)
Ask questions about uploaded documents in any format (PDF, DOCX, or PPTX), and get intelligent answers based on the content.

- 📄 **File Support**: `.pdf`, `.docx`, `.pptx`
- ⚙️ **Tech Used**: `python-docx`, `python-pptx`, PyMuPDF for file parsing, Ollama LLM for natural language understanding and Q&A.

---

### 📄 3. Resume / CV Builder
A smart resume builder that takes in basic user details and generates a polished, professional resume with the help of an LLM.

- 🛠️ Collects personal info, education, experience, and skills.
- 🧠 LLM generates the resume in text.
- 🖨️ Option to export as PDF using `xhtml2pdf`.

- ⚙️ **Tech Used**: Django Forms, Ollama, xhtml2pdf

---

### ✅ 4. To-Do List & Reminder Assistant
Stay organized with a clean, minimal task manager. Users can:
- Add, delete, and complete tasks.
- Use natural language like “Remind me to submit my project tomorrow at 5 PM.”
- (Optional) Get future reminders with background scheduling.

- ⚙️ **Tech Used**: Django models and views, optional background schedulers like Django-Q or Celery (if time permits), Ollama for task parsing.

---

## ⚙️ Tech Stack

| Area | Tools/Frameworks |
|------|------------------|
| Backend | Django (Python) |
| AI/LLM | [Ollama](https://ollama.com/) with models like LLaMA3 |
| File Parsing | PyMuPDF (`fitz`), `python-docx`, `python-pptx` |
| Resume to PDF | `xhtml2pdf` |
| Frontend | HTML5, CSS3, Bootstrap 5 |
| Optional Background Tasks | Django-Q / Celery + Redis |


---

## 👨‍💻 Team HackAI – HackIndia 2025
- 💡 Built with the goal of enhancing productivity and accessibility using LLMs.
- ⏱️ Designed to be built in **3 days** with a focused and modular plan.

---

## 🚀 Getting Started (Locally)
```bash
git clone https://github.com/ishar06/HackIndia-Spark-7-2025-HackAI
cd FormEase
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

> Make sure you have [Ollama](https://ollama.com/download) installed and running locally.

---

## 🙌 Acknowledgements
- HackIndia 2025 Organizers
- Open Source Libraries and LLM Communities

---

## 📢 We're excited for HackIndia 2025!  
Let’s build something amazing together.

