- **Multi-agent system** (Google ADK): Supervisor, Booking, and Information agents
- **WhatsApp-themed** React chat interface with image rendering
- **Real-time updates** via Server-Sent Events (SSE)
- **Message aggregation**: Rapid messages within 2.5s are batched before processing
- **Activity booking**: 10 Dubai activities with multiple variations, timings, and group sizes
- **Human-in-the-loop**: Supervisor email escalation with reply webhook
- **SQLite mock database** with full activity catalog

---

```bash
git clone https://github.com/your-username/allout-travel-assistant.git
cd allout-travel-assistant
```

### 2. Backend Setup

```bash
cd backend

python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env`:
```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=google_ai_studio_api_key_here

# For email escalation
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_app_password
SUPERVISOR_EMAIL=supervisor@company.com
```

Start the backend:
```bash
python main.py
# Server runs at http://localhost:8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# App runs at http://localhost:3000
```