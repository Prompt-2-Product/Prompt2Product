# Prompt2Product - Quick Start Guide

## Get Running in 60 Seconds

### 1. Install & Run
```bash
npm install
npm run dev
```

Visit: `http://localhost:3000`

### 2. Make Changes
- Edit files in `app/` and `components/`
- Hot reload automatically applies changes
- See results instantly in browser

### 3. Build & Deploy
```bash
npm run build    # Create production build
npm start        # Run production server
```

## 📂 Key Files

| File | Purpose |
|------|---------|
| `/app/page.tsx` | Landing page |
| `/app/about/page.tsx` | About & team showcase |
| `/app/describe/page.tsx` | Project description form |
| `/app/generating/page.tsx` | Real-time generation |
| `/app/preview/page.tsx` | Code preview & refinement |
| `/app/ide/page.tsx` | Code editor |
| `/components/auth-modal.tsx` | Login/signup dialog |
| `/components/navigation.tsx` | Header navigation |
| `/components/team-member-card.tsx` | Team member cards |
| `/app/globals.css` | Theme & animations |

## Styling Quick Reference

### Add Button Glow Effect
```tsx
<Button className="btn-glow bg-primary hover:bg-primary/85">
  Click Me
</Button>
```

### Add Team Card Glow
```tsx
<div className="team-card-glow rounded-2xl">
  {/* Content */}
</div>
```

### Responsive Columns
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  {/* Items */}
</div>
```

### Dark Theme Variables
```css
--background: #0a0e17;
--primary: #2563eb;
--card: #0f1419;
--foreground: #e8ecf1;
```

## Authentication Flow

1. User clicks "Sign In" or "Get Started"
2. Modal opens with full-page blur
3. User selects auth method (Google, Apple, Email)
4. Credentials stored in localStorage
5. User profile appears in nav

## Responsive Breakpoints

- **Mobile**: `< 640px` → Single column
- **Tablet**: `640px - 1024px` → Two columns
- **Desktop**: `> 1024px` → Multi-column

Use Tailwind prefixes:
```tsx
<div className="text-4xl md:text-6xl">
  Scales from 4xl to 6xl
</div>
```

## Component Templates

### Modal Trigger
```tsx
const [authModalOpen, setAuthModalOpen] = useState(false)

<Button onClick={() => setAuthModalOpen(true)}>
  Open Modal
</Button>

<AuthModal
  isOpen={authModalOpen}
  onClose={() => setAuthModalOpen(false)}
  mode="login"
/>
```

### Responsive Grid
```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
  {items.map(item => (
    <TeamMemberCard key={item.id} {...item} />
  ))}
</div>
```

### Button with Glow
```tsx
<Button className="btn-glow bg-primary hover:bg-primary/85 text-primary-foreground shadow-lg hover:shadow-xl">
  Generate
</Button>
```

## Color Palette Quick Reference

```
Primary Blue:     #2563eb
Background:       #0a0e17
Card:            #0f1419
Secondary:       #1a1f2e
Foreground:      #e8ecf1
Muted:           #64748b
```

## ⌨️ Common Commands

```bash
npm run dev      # Start dev server
npm run build    # Create prod build
npm start        # Run prod build
npm run lint     # Check code style
```

## 📍 Navigation Structure

```
/ (Landing)
├── /about (About & Team)
├── /describe (Project Setup)
├── /generating (Progress)
├── /preview (Code Preview)
└── /ide (Code Editor)
```

## 📝 Common Edits

### Change Primary Color
Edit `/app/globals.css`:
```css
--primary: #your-color-here;
```

### Add Team Member
Edit `/app/about/page.tsx`:
```tsx
<TeamMemberCard
  name="John Doe"
  role="Developer"
  initials="JD"
  gradientColor="bg-gradient-to-br from-blue-500 to-blue-700"
  github="https://github.com/johndoe"
  linkedin="https://linkedin.com/in/johndoe"
  email="john@example.com"
/>
```

### Update Navigation Menu
Edit `/components/navigation.tsx`:
```tsx
<Link href="/your-page" className="text-sm font-medium hover:text-primary">
  Your Link
</Link>
```

