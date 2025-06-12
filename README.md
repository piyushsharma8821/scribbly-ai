# Scribbly-AI ✨📝

A powerful, AI-enhanced notes API built with **FastAPI**, **MongoDB**, and **OpenAI GPT** — designed for reflective journaling, smart search, and seamless multi-platform deployment.

---

## 🚀 Features

- **User Authentication**  
  JWT-based login/signup (30-minute token expiry, configurable), with hashed passwords stored securely in MongoDB.
  - `/signup`: Send your username and password to create your account and receive your first JWT.
  - `/login`: Once signed in, send your user credentials here to create more JWTs.

- **Notes Management (REST API)**  
  - Create, retrieve (most recent first), update, and delete notes.
  - Notes include: `title`, `content`, `tags` (auto-generated via Azure AI), `owner`, and `timestamp`.
  - Notes access is **user-specific**.

- **GraphQL Support** (via Strawberry 🍓)
  - Fetch notes by date range with pagination (`limit` / `offset`).
  - Filter by tag for faster search.
  - Get total count of matching notes.
  - Retrieve top N tags used by a user.

- **AI-Powered Chat Interface**  
  Reflective journaling with the help of **OpenAI GPT-4o-nano**:
  - `/chat_with_notes`: Start a journaling conversation based on selected note IDs (optional).
  - `/follow_up`: Continue a chat thread; older messages are summarized to fit context limits and reduce token usage.
  - Conversations are stored in MongoDB with `chat_id`, associated `note_ids`, question-answer history, and evolving summaries.

- **Chat History**  
  - `/get_chat_history/{chat_id}`: View previous chats (user-specific).

- **Scalable & Portable Deployment**  
  - Fully **Dockerized** (via `Dockerfile` and `docker-compose.yml`).
  - Continuous Integration and Deployment (CI/CD):
    - GitHub Actions automatically builds and deploys on merge to `main`.
    - Deploys to both **Azure App Service** (Web App for Containers) and **Google Kubernetes Engine** (2-node cluster with LoadBalancer).

---

## 🧰 Tech Stack

- **Backend**: Python, FastAPI
- **Database**: MongoDB (NoSQL)
- **AI Integrations**:
  - OpenAI GPT (reflective journaling)
  - Azure AI (automatic tag extraction)
- **API Types**: REST + GraphQL (Strawberry)
- **Authentication**: JWT
- **Containerization**: Docker, DockerHub
- **Deployment**: Azure App Service, Google Kubernetes Engine (GKE)
- **CI/CD**: GitHub Actions with custom workflows

---

## 📦 Installation (for Local Dev)

```bash
git clone https://github.com/piyushsharma8821/scribbly-ai.git
cd scribbly-ai
docker-compose up --build
