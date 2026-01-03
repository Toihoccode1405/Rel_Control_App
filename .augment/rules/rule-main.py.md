---
type: "always_apply"
description: "Example description"
---

# 🤖 AI Agent Rules - QA Management System

## ⚠️ MANDATORY RULES

### 1. 📁 File Organization

```
✅ Docs/Analysis → ./docs/
✅ Diagrams      → ./docs/diagrams/
❌ NEVER create files in root folder
❌ NEVER create *_SUMMARY.md, *_REPORT.md, *_ANALYSIS.md, *_CHECKLIST.md
```

**Existing root files to preserve**: `README.md`, `PROJECT_SUMMARY_VI.md`

### 2. 🚫 No Auto Git Operations

- ❌ Never `git commit`, `git push` without explicit request
- ✅ Only if user says "commit" or "push"

### 3. ✍️ Concise Output (20/80 Rule)

- ✅ Use 20% info to explain 80% of concept
- ✅ Bullet points, tables > paragraphs
- ✅ Example: "✅ 3 endpoints created" not detailed lists

### 4. 🏃 Complete Tasks Without Asking

- ✅ If user says "implement X" → just do it
- ✅ Continue until complete
- ❌ Don't ask "Should I proceed?"

---

## 🏗️ Project Structure

```
Admin_QA/
├── Backend/QAManagementAPI/    # ASP.NET Core 8 API
│   ├── Controllers/            # API endpoints
│   ├── Services/               # Business logic
│   ├── Models/                 # Entity models
│   ├── DTOs/                   # Data transfer objects
│   ├── Hubs/                   # SignalR hubs
│   └── Data/                   # EF Core DbContext
│
├── Client/AppDesktop/          # WPF .NET 8 Desktop App
│   ├── ViewModels/             # MVVM ViewModels
│   ├── Views/                  # XAML Views
│   └── Services/               # API/Auth services
│
├── src/                        # React 18 + Vite Frontend
│   ├── pages/                  # Page components
│   ├── components/             # Reusable components
│   ├── services/               # API services (Axios)
│   └── contexts/               # React contexts
│
├── docs/                       # Documentation
│   └── diagrams/               # Mermaid diagrams
│
└── publish/                    # Build output (gitignore)
```

---

## 🔧 Tech Stack

| Layer    | Technology                                         |
| -------- | -------------------------------------------------- |
| Backend  | ASP.NET Core 8, EF Core, SignalR, FluentValidation |
| Frontend | React 18, Vite, Tailwind CSS, Axios                |
| Desktop  | WPF .NET 8, MVVM Pattern                           |
| Database | SQL Server                                         |
| Auth     | JWT + BCrypt                                       |

---

## 📋 Coding Conventions

### Backend (C#)

- Follow existing patterns in `Services/` folder
- Use `I{Name}Service` interface + `{Name}Service` implementation
- Register in `Extensions/ServiceCollectionExtensions.cs`
- Use FluentValidation in `Validators/` folder
- DTOs go in `DTOs/` folder

### Frontend (React)

- Functional components with hooks
- Services in `src/services/`
- Use `useLoading()` context for loading states
- Tailwind CSS for styling

### Desktop (WPF)

- MVVM pattern with ViewModels
- Use `FileLogger` for logging
- API calls via `ApiService`

---

## 🚀 Commands

```bash
# Backend
cd Backend/QAManagementAPI && dotnet run

# Frontend
npm run dev

# Desktop
cd Client/AppDesktop && dotnet run

# Build
npm run build
dotnet publish -c Release
```

---

## 📝 When Adding Features

1. **New API endpoint**: Controller → Service → DTO → Register DI
2. **New React page**: Page component → Route in AdminDashboard.jsx → Service
3. **New Desktop feature**: ViewModel → View (XAML) → Bind DataContext
