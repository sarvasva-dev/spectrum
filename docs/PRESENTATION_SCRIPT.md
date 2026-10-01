# 🎤 CleanLoop - Final Master Pitch Script (Hackathon 2025)

> **Instructions for Team:**
> - **Screen Controller:** Match your clicks with the bolded **[On Screen]** cues.
> - **Speakers:** Learn the story, not the words. Eye contact with judges is mandatory.
> - **Total Time:** ~4 Minutes.

---

## 👤 Speaker 1: Purvi Gupta — The Problem & Architecture

**[On Screen: CleanLoop Landing Page]**

"Good morning, respected judges and fellow innovators. We are **Team Bug Busters**, and today we present **CleanLoop**—a Smart, AI-driven Waste Management Ecosystem.

Have you ever walked past an overflowing garbage bin, taken a photo, but had no idea where to report it? Or reported it somewhere and never heard back? That broken loop is exactly what we are solving today.

But CleanLoop is not just a complaint form. It is a full-stack, enterprise-grade platform. Let me explain what's running under the hood, because our architecture itself is a USP.

Our backend is built on **Django 4.2** with an **ASGI server powered by Daphne**. To make data move in real-time—without any page refresh—we integrated **WebSockets using Django Channels**. This means the moment a citizen submits a complaint, it appears live on the Admin Dashboard. That is the power of **`ws://`** over **`http://`**.

We also have a health API endpoint and a **WebSocket connection test** that we've written to verify our real-time pipeline is always alive.

I'll now hand it over to Samridhi to show you the citizen's experience."

---

## 👤 Speaker 2: Samridhi Gupta — Citizen Journey & The AI Brain

**[On Screen: Scroll down Landing page → open Citizen Dashboard]**

"Thank you, Purvi. Welcome to the CleanLoop Citizen Dashboard.

To make people *want* to participate, we gamified civic responsibility. Citizens earn **'CleanCoins'** for every verified waste report they submit. On the Community Champion Leaderboard, you can see who is keeping the city clean—turning a duty into a community competition.

**[On Screen: Open AI Assistant chat window]**

But what if a citizen is confused about—say—how to dispose of hazardous e-waste? That's where our **Sarvam AI-powered Assistant** steps in. This is not a basic FAQ bot. The AI handles the *entire lifecycle of an interaction*, from guiding the citizen on segregation, to reading their complaint, analyzing the uploaded image for waste type, and finally automating the ticket creation process. Start to finish.

**[On Screen: Click 'Report Waste' → show GPS auto-capture + photo upload]**

When they are ready to report an issue, it takes 3 clicks. They upload a photo, and CleanLoop **automatically captures their GPS coordinates using the browser's Geolocation API**. The system then calls our `calculate_smart_priority()` function, which uses the **Haversine formula** to measure if other active complaints exist within a **500-meter radius**. If yes, the complaint is auto-escalated to **CRITICAL priority**. No human judgment needed."

---

## 👤 Speaker 3 — Admin Panel, Testing & Future Vision

**[On Screen: Log out → Log in as Admin → Admin Dashboard → click 'Resolve']**

"So the citizen has filed the complaint. What happens next?

Because of our WebSocket integration, the complaint appears live on the Admin Dashboard—instantly. The admin sees a bird's-eye view of every ward in the city. Complaints from the same area are automatically **clustered as Hotspots**, so the admin sends one truck instead of five.

With one click on 'Resolve', the sanitation crew is dispatched, the citizen receives their CleanCoins reward, and the loop is closed.

**Report. Assign. Resolve. Reward.** That is CleanLoop.

**[On Screen: Keep Admin Dashboard visible]**

Now, here's what makes our engineering stand out:

**First — Geo-Smart Hotspot Detection with Haversine Algorithm.**
Our `Complaint` model runs a real-time geo-query using the Haversine distance formula. If 2 or more complaints exist within 500 meters, priority auto-escalates to CRITICAL. This is real algorithmic intelligence, not a manual flag.

**Second — End-to-End AI Automation via Sarvam AI.**
Sarvam AI's `sarvam-105b` model runs the entire chat workflow—from greeting a citizen at login, analyzing their query, reading complaint images, and assisting the admin in operational decisions. It is an automated municipal assistant, not just a chatbot.

**Third — Professional Test Suite with Django & WebSocket Testing.**
We have written **9 comprehensive unit and integration tests** covering authentication, security isolation, complaint workflows, pickup scheduling, admin controls, smart priority, and hotspot elevation. We also have a dedicated **WebSocket connection test script** that validates our real-time pipeline on every deployment.

**Fourth — Future Vision — 100% Inclusivity.**
Our next step is a **WhatsApp and IVR toll-free 24/7 helpline**. Citizens who can't use apps—the elderly, daily wage workers—can simply drop a photo on WhatsApp or call a number. Our AI will parse the data, extract the location, and auto-generate a ticket on this dashboard.

To conclude: A cleaner city begins with a responsible citizen... but it is truly achieved when a real-time, AI-powered platform turns that responsibility into automated action.

**Thank you! We are now open for your questions.**"
