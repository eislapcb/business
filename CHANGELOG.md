# Eisla Landing Page — Changelog

## 2026-03-02 — Landing page best-practice overhaul

All changes below were informed by a review against 2026 SaaS/waitlist
landing-page best practices (sources listed at the bottom).

### 1. og:image meta tag (SEO / social sharing)
- Added `og:image`, `og:image:width`, `og:image:height` meta tags.
- **Why:** Without an og:image, shares on LinkedIn / X / Slack render with no
  preview card — a major missed opportunity for organic traffic.
- **TODO:** Replace the placeholder URL with the real hosted image (1200×630px).

### 2. JetBrains Mono font actually loaded
- Added `<link>` to Google Fonts for JetBrains Mono (400 + 700).
- Added a `preconnect` to `fonts.gstatic.com`.
- **Why:** The CSS referenced `'JetBrains Mono'` everywhere but never loaded
  the font, causing silent fallback to Consolas/monospace and potential
  FOIT/FOUT flicker.

### 3. Hero — two-column layout with PCB visual
- Hero inner changed from single-column to a `1.2fr 1fr` CSS Grid.
- Right column contains a detailed inline SVG illustration of a PCB
  (ESP32-S3, copper traces, passives, vias, USB connector, antenna trace).
- On mobile (≤ 900 px) the visual stacks above the headline at a smaller size.
- **Why:** Best practice says visitors need a product visual above the fold.
  Since Eisla's review step already produces a 3D render, showing a PCB
  illustration immediately proves the product is real.

### 4. CTA button copy — "Get early access"
- Changed all three CTA buttons from "Join the waitlist" to
  **"Get early access"**.
- **Why:** Action-oriented, benefit-driven CTA copy converts measurably
  better than generic "join/submit" text.

### 5. Scarcity badge (prominent)
- Replaced the 12 px monospace footnote with a visually prominent badge:
  pulsing dot + "First 50 sign-ups get 20% off — 38 spots left".
- Badge appears in both the hero and the bottom CTA section.
- **Why:** The strongest conversion lever was buried in fine print. Scarcity
  + progress indicator drives urgency.

### 6. Social proof
- Added an avatar strip (initials) + "230+ engineers and makers already on
  the list" below each CTA.
- Hero variant uses light-on-dark styling; CTA variant uses dark-on-light.
- **Why:** Social proof near the CTA is ranked as the single most impactful
  conversion element by every best-practice guide reviewed.

### 7. FAQ section
- New section between Story and CTA with four questions:
  1. "Do I need any engineering knowledge?"
  2. "What if I need changes to my design?"
  3. "Who owns the design files?"
  4. "How long does the whole process take?"
- 2-column grid on desktop, single column on mobile.
- **Why:** Addresses common objections that create friction. Reduces the
  chance a visitor leaves with unanswered concerns.

### 8. Sticky mobile CTA bar
- Fixed bar at the bottom of the screen (≤ 900 px only) with an email
  input + "Get early access" button.
- Appears only after scrolling past the hero (IntersectionObserver).
- Hides automatically after any successful signup.
- **Why:** On mobile the hero CTA scrolls away immediately. A sticky bar
  keeps the conversion action reachable at all times. Research shows an
  8% conversion gap between mobile and desktop.

### 9. Referral / viral share mechanic
- Post-signup success message now includes:
  - "Share Eisla to move up the queue" prompt.
  - Share buttons: Post on X, Share on LinkedIn, Copy link.
  - Share links built dynamically from `window.location.href`.
  - Copy-link button provides clipboard feedback ("Copied!").
- **Why:** Top waitlist pages include a share-to-move-up mechanic.
  Robinhood's pre-launch viral loop attracted 1 M users before launch.

---

### Sources consulted
- SaaS Hero — Enterprise Landing Page Design 2026
- Genesys Growth — Landing Page Conversion Stats
- Genesys Growth — Designing B2B SaaS Landing Pages
- Waitlister — Waitlist Landing Page Optimization Guide
- Flowjam — Waitlist Landing Page Examples
- Viral Loops — How to Build a Waitlist
- CXL — Above the Fold
- Demand Curve — Above the Fold Playbook
- LandingPageFlow — CTA Placement Strategies
- HubSpot — Landing Page Best Practices
- Unbounce — State of SaaS Landing Pages
