# Frontend Setup Guide

Complete guide to set up and run the Procode Agent web interface.

## 📋 Prerequisites

- **Node.js 18+** and npm
- **Python backend** running (see main README)
- Terminal/Command line access

## 🚀 Quick Setup (5 Minutes)

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

This will install:
- Next.js 14
- React 18
- CopilotKit (for AI chat interface)
- Tailwind CSS (for styling)
- Lucide React (for icons)
- TypeScript

**Note**: The TypeScript errors you see in VS Code will disappear after running `npm install`.

### Step 3: Start Python Backend

In a separate terminal, start your Python backend:

```bash
# From project root
cd ..
source .venv/bin/activate
python __main__.py
```

Backend should be running on `http://localhost:9998`

### Step 4: Start Frontend Development Server

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## 🎉 You're Done!

Open your browser to `http://localhost:3000` and you should see:
- Modern chat interface
- Agent status panel
- Cost metrics dashboard
- Real-time streaming responses

## 🔧 Configuration

### Environment Variables (Optional)

Create `.env.local` in the `frontend/` directory:

```bash
# Backend API URL (default: http://localhost:9998)
BACKEND_URL=http://localhost:9998

# Enable debug mode
NEXT_PUBLIC_DEBUG=false
```

### Customizing the UI

#### Colors

Edit `app/globals.css` to change the color scheme:

```css
:root {
  --primary: 221.2 83.2% 53.3%;  /* Blue */
  --secondary: 210 40% 96.1%;     /* Light gray */
  /* ... more colors */
}
```

#### Components

All components are in `components/`:
- `AgentStatus.tsx` - Status panel
- `CostMetrics.tsx` - Cost tracking
- `AgentDashboard.tsx` - Performance metrics

## 📦 Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# Type checking
npm run lint
```

## 🐛 Troubleshooting

### Issue: "Cannot find module 'next'"

**Solution**: Run `npm install` in the frontend directory

### Issue: "Backend connection failed"

**Solution**: 
1. Check Python backend is running: `curl http://localhost:9998/health`
2. Verify port 9998 is not blocked
3. Check `next.config.js` proxy configuration

### Issue: TypeScript errors in VS Code

**Solution**: 
1. Run `npm install` to install dependencies
2. Restart VS Code: `Cmd+Shift+P` → "Reload Window"
3. Wait for TypeScript server to initialize

### Issue: Styles not loading

**Solution**:
1. Delete `.next` folder: `rm -rf .next`
2. Reinstall: `npm install`
3. Rebuild: `npm run dev`

### Issue: Port 3000 already in use

**Solution**:
```bash
# Use different port
PORT=3001 npm run dev
```

## 🎯 Features Overview

### 1. Chat Interface (CopilotKit)
- Real-time streaming responses
- Message history
- Auto-scroll
- Typing indicators

### 2. Agent Status Panel
Shows:
- Current status (idle/thinking/executing)
- Detected intent
- Model used (deterministic/cached/Haiku/Sonnet)
- Response time
- Cost per request

### 3. Cost Metrics Dashboard
Displays:
- Session cost
- Savings percentage (vs. baseline)
- Cache hit rate
- Total requests
- LLM call rate

### 4. Performance Metrics
Tracks:
- Total requests
- Cache hits
- LLM calls
- Deterministic rate
- Cost breakdown

## 🚀 Production Deployment

### Option 1: Vercel (Easiest)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variable
vercel env add BACKEND_URL
```

### Option 2: Docker

Create `Dockerfile` in frontend directory:

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "start"]
```

Build and run:

```bash
docker build -t procode-frontend .
docker run -p 3000:3000 -e BACKEND_URL=http://backend:9998 procode-frontend
```

### Option 3: Traditional Server

```bash
# Build
npm run build

# Start with PM2
npm install -g pm2
pm2 start npm --name "procode-frontend" -- start

# Or with systemd
sudo systemctl enable procode-frontend
sudo systemctl start procode-frontend
```

## 📊 Monitoring

### Development

The console will show:
- API requests
- Errors
- Performance metrics

### Production

Add monitoring:

```typescript
// app/layout.tsx
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

## 🔐 Security

### CORS Configuration

The backend needs to allow requests from your frontend:

```python
# In your Python backend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables

Never commit `.env.local` to git. Add to `.gitignore`:

```
.env.local
.env*.local
```

## 📚 Next Steps

1. ✅ **Customize the UI** - Change colors, layout, components
2. ✅ **Add features** - File upload, voice input, charts
3. ✅ **Deploy** - Choose Vercel, Docker, or traditional hosting
4. ✅ **Monitor** - Add analytics and error tracking
5. ✅ **Share** - Show off your cost-optimized AI agent!

## 🤝 Need Help?

- Check the main [README.md](README.md)
- Review [UX Enhancement Proposal](../docs/UX_ENHANCEMENT_PROPOSAL.md)
- Open an issue on GitHub
- Check CopilotKit docs: https://docs.copilotkit.ai

## 🎓 Learning Resources

- **Next.js**: https://nextjs.org/learn
- **React**: https://react.dev/learn
- **Tailwind CSS**: https://tailwindcss.com/docs
- **CopilotKit**: https://docs.copilotkit.ai
- **TypeScript**: https://www.typescriptlang.org/docs

---

**Happy coding! 🚀**
