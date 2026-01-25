# Procode Agent Frontend

Modern web UI for the Procode Agent Framework with real-time cost optimization visualization.

## 🎨 Features

- **Real-time Chat Interface** - Powered by CopilotKit
- **Agent Status Visualization** - See what the agent is thinking
- **Cost Metrics Dashboard** - Track savings in real-time
- **Multi-LLM Strategy Display** - See which model handles each request
- **Streaming Responses** - Real-time feedback as agent works
- **Beautiful UI** - Modern design with Tailwind CSS

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python backend running on `http://localhost:9998`

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 📁 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx             # Main page with CopilotKit
│   ├── globals.css          # Global styles
│   └── api/
│       └── copilot/
│           └── route.ts     # API route for CopilotKit
├── components/
│   ├── AgentStatus.tsx      # Agent status panel
│   ├── AgentDashboard.tsx   # Performance metrics
│   └── CostMetrics.tsx      # Cost tracking display
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:9998

# Optional: Enable debug mode
NEXT_PUBLIC_DEBUG=false
```

### Backend Proxy

The frontend proxies API requests to your Python backend. Configure in `next.config.js`:

```javascript
async rewrites() {
  return [
    {
      source: '/api/agent/:path*',
      destination: 'http://localhost:9998/:path*',
    },
  ];
}
```

## 🎯 Key Components

### CopilotKit Integration

The main chat interface uses CopilotKit for seamless agent interaction:

```typescript
<CopilotKit runtimeUrl="/api/copilot">
  <CopilotSidebar
    labels={{
      title: "Chat with Agent",
      initial: "How can I help you today?",
    }}
  />
</CopilotKit>
```

### Agent Status Panel

Shows real-time agent state:
- Current status (idle, thinking, executing, success)
- Detected intent
- Model used (deterministic, cached, Haiku, Sonnet)
- Quick stats (response time, cost savings)

### Cost Metrics Dashboard

Displays:
- Session cost
- Savings percentage
- Cache hit rate
- Total requests
- LLM call rate

### Performance Metrics

Tracks:
- Total requests
- Cache hits
- LLM calls
- Deterministic rate
- Cost breakdown

## 🎨 Customization

### Styling

The UI uses Tailwind CSS with custom color scheme. Modify in `app/globals.css`:

```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96.1%;
  /* ... more colors */
}
```

### Components

All components are in `components/` and can be customized:

- **AgentStatus.tsx** - Modify status indicators
- **CostMetrics.tsx** - Adjust metric displays
- **AgentDashboard.tsx** - Customize dashboard layout

## 🔌 API Integration

### Connecting to Python Backend

The frontend expects these endpoints from your Python backend:

#### 1. Chat Endpoint (A2A Protocol)
```
POST http://localhost:9998/
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "user message"}]
    }
  },
  "id": 1
}
```

#### 2. Streaming Endpoint
```
POST http://localhost:9998/stream
Content-Type: application/json

{
  "message": {
    "role": "user",
    "parts": [{"kind": "text", "text": "user message"}]
  }
}
```

#### 3. Metrics Endpoint (Optional)
```
GET http://localhost:9998/metrics

Response:
{
  "total_requests": 100,
  "cache_hits": 60,
  "llm_calls": 10,
  "cost_savings": 0.98
}
```

## 📊 Cost Visualization

The frontend visualizes your multi-LLM strategy:

### Model Badges
- 🟢 **Deterministic** - Free (keyword matching)
- 🔵 **Cached** - Free (cached result)
- 🟡 **Haiku** - $0.0001 (small model)
- 🔴 **Sonnet** - $0.001 (large model, rarely used)

### Cost Breakdown
Shows comparison:
- Current cost with optimization
- Cost without optimization
- Total savings

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables for Production

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

## 🧪 Development

### Running Tests

```bash
# Run type checking
npm run lint

# Build to check for errors
npm run build
```

### Hot Reload

The development server supports hot reload. Changes to components will reflect immediately.

## 🎯 Features Roadmap

- [ ] Dark mode toggle
- [ ] Conversation history export
- [ ] Multi-user support
- [ ] Advanced metrics charts
- [ ] Custom agent templates
- [ ] File upload support
- [ ] Voice input
- [ ] Mobile responsive improvements

## 🐛 Troubleshooting

### Backend Connection Issues

If the frontend can't connect to the backend:

1. Ensure Python backend is running on port 9998
2. Check CORS settings in backend
3. Verify proxy configuration in `next.config.js`

### CopilotKit Not Loading

1. Check that `/api/copilot/route.ts` exists
2. Verify backend API is responding
3. Check browser console for errors

### Styling Issues

1. Run `npm install` to ensure all dependencies are installed
2. Clear `.next` cache: `rm -rf .next`
3. Rebuild: `npm run build`

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [CopilotKit Documentation](https://docs.copilotkit.ai)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

Same as parent project.

---

**Built with ❤️ using Next.js, CopilotKit, and Tailwind CSS**
