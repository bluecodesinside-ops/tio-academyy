# TIO Academy – Online Latin Dance Platform

A modern full-stack web application for running an online Latin dance academy.  
It includes a marketing website, course catalog, and internal tools for managing content, users and payments.

## 🎯 Project Overview

TIO Academy is built as a production-style Django project with a React frontend.  
The goal: host structured online dance courses (3 levels × 4 sessions), manage students, and later plug into real payment + video hosting (AWS/S3).

## 🧱 Tech Stack

- **Backend:** Django
- **Frontend:** React (in `frontend/`)
- **Templates:** Django templates for public pages + admin views
- **Database:** Django ORM (local SQLite for dev, can switch to Postgres/MySQL in prod)
- **Styling:** CSS (custom), responsive layouts
- **Auth:** Django auth system (custom admin user)
- **Deployment target:** AWS (EC2 / Elastic Beanstalk) via this GitHub repo

---

## 📁 Main Project Structure

> High-level – actual folders may contain more files.

```bash
tio-academyy/
├── blog/          # Blog app – posts, news, articles
├── courses/       # Core course & session models / views
├── frontend/      # React frontend (SPA / components)
├── gallery/       # Photo gallery logic
├── newsletter/    # Newsletter / subscribers
├── payments/      # Payment/invoice logic (future integration)
├── pricing/       # Pricing plans, offers, packages
├── programs/      # Program / package definition
├── slideshow/     # Homepage hero sliders
├── static/        # Static assets (CSS, JS, images)
├── templates/     # Django HTML templates
├── manage.py
└── README.md
