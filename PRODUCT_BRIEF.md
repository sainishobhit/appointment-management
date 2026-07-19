# DentaFlow — Product Brief (v2)
### A solo-dentist **appointment management** app

*Outcome of a working session between the Dentist (Dr. S — MDS student & practising dentist), the Product Manager, and the Software Developer. v2 reflects the dentist's scoping decisions: this is an **appointments-only** tool — no treatment plans, no payments, dentist-controlled, English-only.*

---

## 1. Decisions locked in this round

| # | Decision | Effect on the product |
|---|---|---|
| 1 | **Recommend dates/slots** when booking | Add a *Smart Slot Suggestions* feature (see §7) |
| 2 | **Reschedule & cancellation** are first-class | Dedicated flows + auto-generated WhatsApp messages |
| 3 | **No treatment plans, no payments/dues** | Removed from scope entirely |
| 4 | **Dentist keeps full control** | No patient self-booking; she owns the calendar |
| 5 | **~30–40 appointments/week** | ~6–8/day; small scale → keep it simple, single-user |
| 6 | **English only** | No multi-language handling |
| 7 | **One-tap pre-filled WhatsApp** (no full automation) | WhatsApp opens with text ready; she taps send. No WhatsApp Business API. |

**Focus statement:** *Everything in this app serves appointment management.* Patient records exist only to the extent needed to book, remind, and follow up.

---

## 2. Problem statement

A solo dentist who is also an MDS student runs all appointments over WhatsApp. This causes scattered information, scheduling conflicts around her academic schedule, no-shows from manual reminders, and dropped follow-ups/recalls — draining time and attention that should go to studying. She wants one focused tool to manage appointments, with the reminders still going out over WhatsApp.

---

## 3. Goals & non-goals

### Goals
1. Book/confirm an appointment in **under 15 seconds**, with the app **recommending the best date & time**.
2. Make **reschedule and cancellation** effortless, with the patient auto-notified.
3. Reduce no-shows via **one-tap WhatsApp reminders**.
4. Give **one clear day/week view** that respects her college schedule.
5. Never let a **follow-up or 6-month recall** slip.

### Non-goals
- ❌ Treatment plans / clinical charting.
- ❌ Payments, dues, or billing.
- ❌ Patient self-booking or any patient-facing app — **dentist controls everything**.
- ❌ Full WhatsApp automation / Business API — **one-tap pre-filled messages only**.
- ❌ Multi-doctor / multi-clinic, insurance, EMR.
- ❌ Multi-language — **English only**.

---

## 4. Target user & context

- **User:** One dentist (the operator). She does all booking, reminding, rescheduling — no receptionist, no patient logins.
- **Context:** On her phone, between patients or between college and clinic, sometimes on weak internet. Short, interruption-prone sessions.
- **Scale:** ~30–40 appointments/week (~6–8/day). Small enough that the app can stay simple and fast; no heavy infrastructure needed.
- **Design implications:** Mobile-first, thumb-reachable, minimal typing, works offline and syncs later.

---

## 5. Product principles

1. **Faster than WhatsApp** — booking here must beat typing a chat.
2. **Suggest, don't make her think** — the app proposes dates; she confirms.
3. **Respect the irregular schedule** — availability bends around college.
4. **Never make her remember** — follow-ups, recalls, and conflicts surface on their own.
5. **She's in control** — no patient can change her calendar.
6. **Boring and reliable** over clever and fragile.

---

## 6. Feature set

### Core (MVP)

**A. Appointment booking with Smart Slot Suggestions**
- New appointment in a few taps: patient → procedure/duration → **app proposes the 3 best open slots** → confirm.
- Manual override always available (pick any date/time).
- Full detail of the suggestion logic in **§7**.

**B. Calendar & conflict detection**
- **Day view** (default, today first) and **week view**.
- Warns on overlaps and on any time blocked by her academic schedule.
- Statuses: *Scheduled → Confirmed → Completed / No-show / Cancelled.*

**C. Availability & schedule blocking**
- Recurring **unavailable blocks** (college hours, lectures) and one-off blocks (exams, seminars, leave).
- Default clinic sessions (e.g., Mon/Wed evenings, Sat morning), overridable per week.
- These blocks feed directly into the slot recommender.

**D. Reschedule (first-class)**
- Open appointment → **Reschedule** → recommender proposes new slots → confirm → auto-generate *"We've moved your appointment to…"* WhatsApp message.
- Original slot is freed and becomes available again.

**E. Cancellation (first-class)**
- Open appointment → **Cancel** (with optional reason) → auto-generate a courteous WhatsApp cancellation/notice message → slot freed.
- Cancelled appointments stay in patient history for context.

**F. No-show handling**
- One tap to mark **No-show**; patient flagged, optional rebooking nudge message.

**G. Patient records (minimal — only what appointments need)**
- Name, phone (WhatsApp), age/sex, chief complaint, allergies/medical flags, free-text notes, and **appointment history**.
- Fast search by name/phone; **deduplication** so one patient = one record.

**H. Follow-ups & recalls**
- On completing a visit: *"Schedule next visit?"* → set the interval → recommender proposes dates around it.
- **6-month recall** flag → patient surfaces in a "due for check-up" list; one tap to invite back.

**I. One-tap WhatsApp messaging**
- App generates the message and opens WhatsApp **pre-filled** to the right patient; she taps send.
- Templates: booking confirmation, day-before reminder, reschedule notice, cancellation notice, follow-up/recall invite.
- A daily **"to remind" list** (tomorrow's patients) to batch through.

### Later (nice-to-have, post-MVP)
- Simple **analytics**: no-show rate, busiest days/sessions, recall compliance.
- **Recurring/quick templates** for frequent procedures.
- **Backup / export** of the schedule and patient list.
- Smarter recommender tuning based on her accept/reject history.

---

## 7. Smart Slot Suggestions — how the date recommendation works

When booking (or rescheduling, or setting a follow-up), the app proposes a short ranked list of concrete slots, e.g.:

> **Suggested:** ① Wed · 6:30 PM · ② Thu · 7:00 PM · ③ Sat · 10:00 AM

**Inputs:** procedure duration, her clinic sessions, academic/blocked time, existing appointments, a buffer between patients, a daily cap, the follow-up target interval (if any), and the patient's usual time-of-day (if history exists).

**Ranking rules:**
1. **Never** inside academic/blocked time; **only** within clinic sessions.
2. Must fit the **full duration + buffer** with no overlap.
3. **Cluster onto days she's already seeing patients** rather than opening a fresh day — keeps other days free for college.
4. For **follow-ups**, center on the target interval (e.g., "next sitting in ~7 days" → propose slots at 6–8 days).
5. Prefer the patient's **usual time-of-day** when known.
6. Respect a **daily cap** (default configurable, ~8) so days don't over-pack.
7. Favour **earliest** among otherwise-equal options.

She can always ignore the suggestions and pick manually. Over time the recommender can learn from which suggestions she accepts.

---

## 8. Key user flows

1. **Book (chairside):** New appointment → search/add patient → pick procedure → **tap a suggested slot** → confirm → one tap sends WhatsApp confirmation. *(Target <15s.)*
2. **Reschedule:** Open appointment → Reschedule → tap a suggested new slot → confirm → "we've moved you to…" message sent; old slot freed.
3. **Cancel:** Open appointment → Cancel (+ reason) → cancellation message sent; slot freed; kept in history.
4. **Morning reminder run:** Open app → "Remind tomorrow's patients" → tap each → WhatsApp opens pre-filled → send.
5. **No-show:** Mark no-show → optional rebooking nudge.
6. **Complete → follow-up:** Mark complete → "Next visit?" → set interval → tap a suggested slot → confirmation sent.
7. **Recall due:** App surfaces due patients → one tap to invite back.

---

## 9. Data model (trimmed to appointments)

- **Patient** — id, name, phone, age, sex, medical flags/allergies, notes, recall-due date, usual time-of-day (derived).
- **Appointment** — id, patient_id, start time, duration, procedure type, status, notes, follow-up-of (optional link to prior appointment), reminder-sent flag.
- **AvailabilityBlock** — id, type (clinic-session / unavailable), recurrence rule, start/end, label (e.g., "College posting").
- **MessageLog** — appointment_id, template, timestamp (records that a WhatsApp message was prepared/sent).

*(No treatment-plan or payment entities — deliberately out of scope.)*

---

## 10. WhatsApp approach

**One-tap pre-filled messages only.** The app builds the text and opens WhatsApp via a deep link (`wa.me`) to the correct patient; the dentist taps send. No WhatsApp Business API, no per-message cost, no automation approvals. Simple, free, reliable, and entirely under her control.

---

## 11. Non-functional requirements

- **Platform:** Mobile-first PWA (installable, no app-store friction; Android-first).
- **Offline-tolerant:** View schedule and add/reschedule offline; sync when back online.
- **Performance:** Opens to today's schedule in <2s; slot suggestions feel instant. Trivial data volume at ~30–40/week.
- **Privacy & security:** Minimal patient data, encrypted at rest and in transit, PIN/biometric lock, data owned by her; align with **India's DPDP Act 2023**.
- **Reliability:** Daily automatic backup; no data loss on crash.
- **Cost:** Effectively zero running cost at this scale.
- **Language:** English only.

---

## 12. Success metrics

- **Time-to-book** under 15 seconds, with a suggested slot accepted in most bookings.
- **No-show rate** drops after 4 weeks of reminders (vs. week-1 baseline).
- **≥90%** of appointments managed in-app rather than on WhatsApp within a month.
- **Zero** missed follow-ups/recalls among flagged appointments.
- She reports **less daily admin stress** and reclaimed study time.

---

## 13. Open questions (small, non-blocking)

1. Typical **procedure types & durations** to seed the picker (e.g., consultation 15m, RCT 45m, extraction 30m)?
2. Default **clinic sessions** and a rough **weekly college timetable** to pre-load availability?
3. Preferred **buffer between patients** and **daily cap** for the recommender?
4. Exact **wording/tone** for the WhatsApp message templates?

---

## 14. Roadmap

| Phase | Theme | Headline |
|---|---|---|
| **1 — MVP** | Manage appointments end-to-end | Smart-suggested booking, day/week calendar, availability blocking, reschedule, cancellation, no-show, minimal patient records, follow-ups/recalls, one-tap WhatsApp |
| **2 — Polish** | Small quality-of-life wins | Analytics, quick templates, backup/export, recommender tuning |

---

*Next step: answer the four small questions in §13, then turn Phase 1 into a screen-by-screen feature list — or start prototyping the MVP.*
