# ARIA - AI Teaching Assistant for Statics & Mechanics

🤖 **ARIA** is an intelligent teaching assistant designed to help students learn Statics & Mechanics of Materials through interactive problem-solving and step-by-step guidance.

## 🚀 Quick Deploy to Streamlit Cloud

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- OpenAI API key
- Supabase project (optional, for conversation storage)

### Step 1: Upload to GitHub

1. Create a new repository on GitHub
2. Upload all files from this folder to your repository
3. Make sure `.gitignore` is included to protect sensitive files

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repository
4. Set the main file path: `app.py`
5. Click "Deploy"

### Step 3: Configure Environment Variables

In Streamlit Cloud's **Advanced Settings**, add these secrets:

```toml
[general]
OPENAI_API_KEY = "your_openai_api_key_here"
SUPABASE_URL = "your_supabase_project_url_here"
SUPABASE_ANON_KEY = "your_supabase_anon_key_here"
```

#### Required Variables:
- `OPENAI_API_KEY`: Your OpenAI API key (get from [platform.openai.com](https://platform.openai.com))

#### Optional Variables (for conversation storage):
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key

### Step 4: Set Up Database (Optional)

If using Supabase for conversation storage:

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Go to SQL Editor in your Supabase dashboard
3. Run the SQL from `supabase/migrations/001_create_conversations_table.sql`
4. Add your Supabase credentials to Streamlit secrets

## 🏗️ Project Structure

```
aria-streamlit-deploy/
├── app.py                          # Main Streamlit application
├── scripts/
│   ├── teaching_assistant.py       # Core TA logic
│   ├── database/
│   │   ├── __init__.py
│   │   └── conversation_storage.py # Database integration
│   └── embedding/
│       ├── __init__.py
│       └── rag_retriever.py        # RAG system
├── embeddings/                     # Pre-built course embeddings
├── supabase/
│   └── migrations/                 # Database schema
├── .streamlit/
│   └── secrets.toml.example        # Environment variables template
├── requirements.txt                # Python dependencies
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

## 🔧 Local Development

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd aria-streamlit-deploy
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.streamlit/secrets.toml`:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your actual API keys
```

5. Run the application:
```bash
streamlit run app.py
```

## 🎯 Features

- **Interactive Teaching**: ARIA guides students through problems step-by-step
- **RAG-Powered**: Uses course materials to provide contextual assistance
- **Conversation Storage**: Optional Supabase integration for analytics
- **Clean Interface**: Streamlined UI focused on learning
- **Mobile Friendly**: Responsive design for all devices

## 🔑 API Keys Setup

### OpenAI API Key (Required)
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add to Streamlit secrets

### Supabase Setup (Optional)
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings > API
4. Copy the Project URL and anon public key
5. Add to Streamlit secrets

## 🚨 Troubleshooting

### Common Issues:

1. **App won't start**: Check that all required environment variables are set
2. **OpenAI errors**: Verify your API key is valid and has credits
3. **Database errors**: Ensure Supabase credentials are correct and table exists
4. **Slow loading**: Embeddings are loading - this is normal on first startup

### Getting Help:

- Check Streamlit Cloud logs for detailed error messages
- Verify all secrets are properly formatted in the advanced settings
- Ensure your GitHub repository is public or properly connected

## 📊 Analytics

With Supabase integration, you can:
- Track conversation history
- Analyze student interactions
- Monitor system usage
- Export data for research

## 👥 Credits

Built by **Dibakar Roy Sarkar** and **Yue Luo**  
Lab: **Centrum IntelliPhysics**

## 📄 License

This project is for educational purposes. Please ensure compliance with OpenAI's usage policies.

---

🎓 **Ready to help students learn Statics & Mechanics!**