# The Forge: S.P.E.C.I.A.L. Edition

**Backend**
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)

**Frontend**
![Angular](https://img.shields.io/badge/Angular-21.2-DD0031?logo=angular&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?logo=tailwindcss&logoColor=white)

Track your tasks, earn XP, upgrade your stats, and slowly realize this is just your to-do list with extra steps. Productivity experts would call this gamification. Your manager calls it lack of focus. The Forge calls it a side quest.

---

## Overview

**The Forge** is a personal life management app that turns your tasks, goals and habits into a RPG progression system. Every mission you complete earns rewards tied to one of seven **S.P.E.C.I.A.L.** attributes, each representing a real area of your life. You already know which one is at level 1. The Forge just makes it harder to pretend otherwise. The heart of it all is one inevitable loop: grind, unlock, repeat. The cycle doesn't end. That's not a bug. That's the entire point.

---

## Core Systems

### S.P.E.C.I.A.L. Attributes

Your life, broken down into seven measurable areas. Finally, something your therapist and your HR department can agree on:

| Attribute          | Area of Life                                            | Material          |
| ------------------ | ------------------------------------------------------- | ----------------- |
| **S** Strength     | Physical fitness — gym, sports, crossfit                | Damascus Steel    |
| **P** Perception   | Learning & awareness — reading, photography, meditation | Quartz Lens       |
| **E** Endurance    | Health & resilience — running, swimming, hiking         | Carbon Fiber      |
| **C** Charisma     | Social life — music, dancing, comedy                    | Resonance Crystal |
| **I** Intelligence | Creation & problem solving — coding, astronomy, writing | Binary Essence    |
| **A** Agility      | Daily balance — cooking, dancing, pilates               | Inertial Catalyst |
| **L** Luck         | RNG decided - Not your fault, still your problem        | Stardust          |

### Mission System

- **Main Quest** — major goals with checkpoints. More effective than the $200 course you never finished.
- **Side Quest** — medium effort tasks. Not urgent enough to panic, too important to ignore.
- **Daily Grind** — daily habits with streak tracking. Yesterday doesn't count anymore. Today does.

All missions have a threat level that affects rewards:

- **Minor** — low stakes tasks with baseline rewards. Not every mission needs to be a crisis to count.
- **Major** — medium effort tasks with better rewards. The sweet spot between "too easy" and "I'll do it tomorrow."
- **Critical** — high priority tasks with maximum rewards. The ones that got here by being ignored long enough.

### Dashboard

The first thing you see every day. No fluff, no motivational quotes just what needs your attention:

- **Weekly Report** — a weekly breakdown of completed missions, threat distribution, attribute XP earned and average resolution time. Navigate back through previous weeks to see if you're improving or just busy.
- **Active Missions** — everything that's overdue, urgent, or about to become your problem. Sorted by threat level. The list doesn't get shorter by itself.

### Forge & Relics

Materials earned from missions don't sit in your inventory forever. The Forge is where you put them to work:

- **Stardust Condenser** — transform 6 ordinary materials into Stardust. The math is simple. The grind is not.
- **Relic Workshop** — invest materials into attribute specific relics for permanent passive bonuses. The ones you upgrade first say a lot about you.

### Achievements

Milestones that track your long-term progress across every system. Each one unlocks permanently in your profile. With a company-approved message that somehow makes you feel worse about winning.

### Prestige & Perks

The endgame loop. Everything you've built gets sacrificed and that's exactly the point:

- **Prestige (Ascension)** — max all attributes, pay the cost. Attributes, relics and perks reset to zero. Congratulations. Now do it again.
- **Perks** — spend Prestige Points on passive bonuses across multiple paths. Each path has exclusive choices. Points refund on Prestige so you can change your build or make the same mistake again.

---

## Tech Stack

| Layer      | Technology                     | Version     |
| ---------- | ------------------------------ | ----------- |
| Runtime    | Python                         | 3.10+       |
| Runtime    | Node.js                        | 20+         |
| Backend    | FastAPI + SQLAlchemy (async)   | 0.136 / 2.0 |
| Frontend   | Angular (standalone + signals) | 21.2        |
| Database   | PostgreSQL                     | 17          |
| Migrations | Alembic                        | 1.18        |
| Auth       | JWT (python-jose + passlib)    | 3.5 / 1.7   |
| Styling    | Tailwind CSS                   | 3.4         |

---
