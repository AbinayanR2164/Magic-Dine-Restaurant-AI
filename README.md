# 🍽️ MagicDine AI

### AI-Powered Restaurant Management & Growth Assistant

MagicDine AI is a full-stack restaurant management platform that combines **real-time restaurant analytics, customer intelligence, offer management, and an AI-powered business assistant**.

The platform helps restaurant owners understand their business data, monitor performance, analyze customers, manage offers, and receive data-driven recommendations through an AI assistant.

---

## 🚀 Features

### 📊 Restaurant Dashboard
- Total orders
- Total revenue
- Average order value
- Best-performing order channel
- Order analytics
- Channel revenue distribution
- Customer overview
- AI-generated business insights

### 🤖 AI Business Assistant
The AI assistant can answer questions using the restaurant's actual database information.

Examples:

- How many customers have no orders?
- Who is my top customer by spending?
- What active offers do I currently have?
- What is my total revenue?
- Which order channel performs best?

The AI is grounded in the application's database data and is designed to avoid inventing business metrics.

### 👥 Customer Intelligence
- Customer profiles
- Order count
- Total spending
- Average order value
- Repeat customer identification
- High-value customer identification
- Customers with no orders
- Customer search
- Customer filtering
- Customer sorting
- Individual customer order history
- Revenue contribution

### 🎁 Offer Management
- Create offers
- Edit offers
- Delete offers
- Active/inactive offer tracking
- Offer expiration tracking
- Discount percentage
- Offer start and end dates
- Offer urgency indicators

### 📈 Business Insights
- Revenue analysis
- Order analysis
- Channel performance
- Customer analytics
- AI-generated insights
- Data-driven recommendations

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │     Frontend        │
                    │ HTML / CSS / JS     │
                    └──────────┬──────────┘
                               │
                               │ HTTP / REST API
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
       ┌─────────────────┐          ┌─────────────────┐
       │      MySQL      │          │      Groq       │
       │    Database     │          │   AI / LLM      │
       └─────────────────┘          └─────────────────┘