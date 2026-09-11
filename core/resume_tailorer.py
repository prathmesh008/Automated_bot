"""
core/resume_tailorer.py

Dynamically tailors candidate resume per job following top FAANG & Ivy League (Jake's Resume / Overleaf standard) ATS guidelines:
1. 100% Parseability & ATS Standard (Clean single-column ReportLab layout, steel horizontal rules, no graphic artifacts)
2. Professional Summary (Targeted 2-3 line summary highlighting core specialization and impact)
3. Mathematical Hanging Indents (Two-column layout ensuring line 2, 3 align flush with line 1)
4. Google XYZ Formula (Accomplished [X] as measured by [Y], by doing [Z] with benchmarks)
5. Clean 1-Page Breathable Geometry (Balanced vertical distribution filling the page from top to bottom)
"""
import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from core.profile_loader import Profile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

load_dotenv()

def build_ats_pdf(resume_data: dict, output_path: str):
    """Compiles structured resume data into a strictly 1-page, high-density, breathable FAANG-standard ATS PDF."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=28,
        rightMargin=28,
        topMargin=22,
        bottomMargin=22
    )
    printable_width = 556
    col_bullet_icon = 10
    col_bullet_text = printable_width - col_bullet_icon

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        'Name',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=22,
        alignment=1, # Centered
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=2
    )
    contact_style = ParagraphStyle(
        'Contact',
        fontName='Helvetica',
        fontSize=8.1,
        leading=10.5,
        alignment=1, # Centered
        textColor=colors.HexColor('#334155'),
        spaceAfter=3
    )
    section_heading = ParagraphStyle(
        'SecHeading',
        fontName='Helvetica-Bold',
        fontSize=9.8,
        leading=11.8,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=5.0,
        spaceAfter=1.5
    )
    item_left_bold = ParagraphStyle(
        'ItemLeftBold',
        fontName='Helvetica-Bold',
        fontSize=8.3,
        leading=10.5,
        textColor=colors.HexColor('#0F172A')
    )
    item_right = ParagraphStyle(
        'ItemRight',
        fontName='Helvetica',
        fontSize=8.1,
        leading=10.5,
        alignment=2, # Right aligned
        textColor=colors.HexColor('#475569')
    )
    item_sub_left = ParagraphStyle(
        'ItemSubLeft',
        fontName='Helvetica-Oblique',
        fontSize=8.1,
        leading=10.2,
        textColor=colors.HexColor('#1E293B')
    )
    body_style = ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=8.1,
        leading=10.3,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=1.0
    )
    bullet_text_style = ParagraphStyle(
        'BText',
        fontName='Helvetica',
        fontSize=8.05,
        leading=10.25,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=0,
        firstLineIndent=0
    )
    dot_style = ParagraphStyle(
        'Dot',
        fontName='Helvetica',
        fontSize=6.5,
        leading=10.25,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )

    story = []

    # 1. Header (Jake's Resume Centered Style with subtle dividers)
    story.append(Paragraph(resume_data.get("name", "PRATHMESH UPADHYAY").upper(), name_style))
    contact_line = resume_data.get(
        "contact",
        "Jaipur, India &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
        "+91-9871057729 &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
        "<a href='mailto:prath.upadhyay08@gmail.com'><u>prath.upadhyay08@gmail.com</u></a> &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
        "<a href='https://linkedin.com/in/prathmeshupadhyay008'><u>linkedin.com/in/prathmeshupadhyay008</u></a> &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
        "<a href='https://github.com/prathmesh008'><u>github.com/prathmesh008</u></a> &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
        "<a href='https://prathmesh.me'><u>prathmesh.me</u></a>"
    )
    story.append(Paragraph(contact_line, contact_style))

    def section_header(title):
        p = Paragraph(title, section_heading)
        hr = HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#94A3B8'), spaceBefore=1.0, spaceAfter=3.0)
        return [p, hr]

    def bullet_row(text):
        t = Table(
            [[Paragraph('&#9679;', dot_style), Paragraph(text, bullet_text_style)]],
            colWidths=[col_bullet_icon, col_bullet_text]
        )
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
        ]))
        return t

    # 2. PROFESSIONAL SUMMARY
    summary = resume_data.get("summary", "")
    if summary:
        story.extend(section_header("PROFESSIONAL SUMMARY"))
        story.append(Paragraph(summary, body_style))

    # 3. TECHNICAL SKILLS
    skills = resume_data.get("skills", {})
    if skills:
        story.extend(section_header("TECHNICAL SKILLS"))
        for cat, items in skills.items():
            line = f"<b>{cat}:</b> {items}"
            story.append(Paragraph(line, body_style))

    # 4. PROFESSIONAL EXPERIENCE
    experience = resume_data.get("experience", [])
    if experience:
        story.extend(section_header("PROFESSIONAL EXPERIENCE"))
        for idx, exp in enumerate(experience):
            exp_table_data = [
                [
                    Paragraph(f"<b>{exp.get('company')}</b> &mdash; <i>{exp.get('role')}</i>", item_left_bold),
                    Paragraph(f"{exp.get('dates')} | {exp.get('location', '')}", item_right)
                ]
            ]
            t_exp = Table(exp_table_data, colWidths=[385, 171])
            t_exp.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0.8),
                ('TOPPADDING', (0,0), (-1,-1), 0.5),
            ]))
            story.append(t_exp)
            for bullet in exp.get("bullets", []):
                story.append(bullet_row(bullet))
            if idx < len(experience) - 1:
                story.append(Spacer(1, 2.5))

    # 5. KEY ENGINEERING PROJECTS
    projects = resume_data.get("projects", [])
    if projects:
        story.extend(section_header("KEY ENGINEERING PROJECTS"))
        for idx, proj in enumerate(projects):
            p_table_data = [
                [
                    Paragraph(f"<b>{proj.get('title')}</b> | <i>{proj.get('tech')}</i>", item_left_bold),
                    Paragraph(proj.get('dates', ''), item_right)
                ]
            ]
            t_p = Table(p_table_data, colWidths=[450, 106])
            t_p.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0.8),
                ('TOPPADDING', (0,0), (-1,-1), 0.5),
            ]))
            story.append(t_p)
            for b in proj.get("bullets", []):
                story.append(bullet_row(b))
            if idx < len(projects) - 1:
                story.append(Spacer(1, 2.5))

    # 6. EDUCATION
    edu = resume_data.get("education", [])
    if edu:
        story.extend(section_header("EDUCATION"))
        for e in edu:
            edu_table_data = [
                [
                    Paragraph(f"<b>{e.get('school')}</b>", item_left_bold),
                    Paragraph(e.get('location', 'Vellore, India'), item_right)
                ],
                [
                    Paragraph(f"<i>{e.get('degree')}</i>", item_sub_left),
                    Paragraph(f"<i>{e.get('dates')}</i>", item_right)
                ]
            ]
            t_edu = Table(edu_table_data, colWidths=[395, 161])
            t_edu.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0.3),
                ('TOPPADDING', (0,0), (-1,-1), 0.3),
            ]))
            story.append(t_edu)
            if e.get('coursework'):
                story.append(Paragraph(f"<b>Relevant Coursework:</b> {e.get('coursework')}", body_style))

    doc.build(story)
    return output_path


def tailor_resume_for_job(job_title: str, company_name: str, job_description: str, profile: Profile) -> str:
    """
    Analyzes the JD, extracts exact keywords, formats bullets into Google XYZ standard,
    and produces a customized, strictly 1-page FAANG-standard ATS PDF resume.
    """
    clean_company = re.sub(r'[^a-zA-Z0-9]', '_', company_name)[:20]
    clean_title = re.sub(r'[^a-zA-Z0-9]', '_', job_title)[:25]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "data", "tailored_resumes")
    output_path = os.path.join(output_dir, f"Resume_{clean_company}_{clean_title}.pdf")

    master_exp = [
        {
            "company": "Urban Culture",
            "role": "Full Stack Developer",
            "dates": "May 2026 – Present",
            "location": "Jaipur, India",
            "bullets": [
                "<b>Distributed Concurrency & Locking:</b> Engineered concurrent booking and slot-hold microservices using Redis SETNX distributed locking with automated TTL expiration, eliminating double-booking race conditions under 100+ simultaneous reservation attempts.",
                "<b>Checkout Recommendation Engine:</b> Architected personalized recommendation pipeline evaluating Apriori rule mining against ML re-ranking; conducted bootstrapped CI testing to fix data leakage, driving an 18% lift in checkout add-on conversions across 10,000+ monthly reservations.",
                "<b>Double-Entry Financial Ledger:</b> Designed high-integrity transactional wallet and ledger system in Node.js and Firestore; enforced atomic state transitions and audit logging, achieving 100% balance reconciliation accuracy across user balances, refunds, and partner payouts.",
                "<b>In-House Notification & Scheduling Engine:</b> Architected an event-driven notification platform utilizing Pub/Sub event streaming and a priority preemption algorithm to dynamically pause, restore, and re-queue user journeys; unified BigQuery OLAP with MongoDB via an LLM query layer and distributed task scheduler, driving an incremental +5 bookings/day."
            ]
        },
        {
            "company": "Mentaive",
            "role": "Full Stack Engineering Intern",
            "dates": "Feb 2026 – May 2026",
            "location": "Remote",
            "bullets": [
                "<b>Platform Engineering & Scheduling:</b> Built production assessment platform using MERN stack and Next.js; developed automated cron job scheduling engine for time-bounded examination windows and automated alerts via SendGrid, cutting manual administrative overhead by 40%.",
                "<b>API Contracts & Cross-Stack Integration:</b> Coordinated 10+ RESTful API contracts between Next.js frontend and backend services, implementing strict request validation schemas that reduced cross-team sprint integration friction by 50%.",
                "<b>Frontend Performance Optimization:</b> Profiled component render lifecycles with React DevTools; eliminated recursive DOM re-renders and implemented route-based dynamic code splitting, improving Core Web Vitals and boosting page load speeds by 30% on low-bandwidth devices."
            ]
        }
    ]

    master_projects = [
        {
            "title": "TaskFlow — Distributed Task Queue Engine",
            "tech": "Node.js, Redis, Express, WebSockets, k6, Lua",
            "dates": "Mar 2025 – May 2025",
            "bullets": [
                "<b>Cluster Hash-Slot Architecture:</b> Architected a distributed background job engine utilizing Redis Cluster hash tags {queue} to enforce hash-slot locality across 16,384 shards, completely eliminating CROSSSLOT partition failures during atomic multi-key transactions.",
                "<b>Atomic Lua Dequeuing & Orphan Reaper:</b> Authored atomic Lua scripts for deterministic single-roundtrip dequeue operations (RPOP + ZADD); engineered an autonomous Orphan Reaper daemon with heartbeat monitoring and full-jitter exponential backoff retries.",
                "<b>Benchmarking & Resilience:</b> Stress-tested under 16 concurrent workers processing 100,000 background jobs via k6; sustained 3,351 jobs/sec throughput with 0% dropped tasks, sub-9.8ms P99 latency, and 100% crash recovery under injected SIGKILL."
            ]
        },
        {
            "title": "GrabASeat — Real-Time Booking Engine",
            "tech": "Next.js 14, Node.js, Express, Socket.io, MongoDB, Python, k6",
            "dates": "Nov 2024 – Feb 2025",
            "bullets": [
                "<b>Real-Time Concurrency Control:</b> Built interactive seat reservation engine utilizing Socket.io event broadcasting and Redis distributed locking (SETNX with 10-minute TTL), guaranteeing mutual exclusion across 50+ simultaneous checkout requests.",
                "<b>ML Dynamic Pricing Microservice:</b> Developed isolated Python/Flask microservice running Random Forest regression; load-tested to 500 concurrent virtual users via k6 with P99 latency &lt;120ms; reduced MongoDB query latency by 60% via compound indexing.",
                "<b>Secure Payment & Automated Ticketing:</b> Integrated Razorpay payment gateway with automated digital ticket generation using dynamic QR code verification."
            ]
        },
        {
            "title": "ChronoStore — Time-Series Storage Engine",
            "tech": "Node.js, Express, Google Gemini API, ChromaDB",
            "dates": "Jun 2025 – Aug 2025",
            "bullets": [
                "<b>Append-Only Storage & WAL Engine:</b> Built custom append-only log file storage engine with in-memory range indexes, delivering sub-5ms query response times over 1,000,000+ data points; implemented Write-Ahead Logging (WAL) for fault-tolerant crash durability.",
                "<b>Semantic RAG Interface:</b> Designed semantic NL-to-query layer using Google Gemini function calling; embedded document context into ChromaDB vector database with hybrid search to synthesize complex analytical queries.",
                "<b>Data Compression:</b> Applied delta and run-length compression algorithms on sequential time-series timestamps and metric payloads, reducing on-disk storage footprint by 70%."
            ]
        }
    ]

    # Master Skills baseline
    master_skills = {
        "Languages": "C++, Python, JavaScript (ES6+), TypeScript, SQL, HTML5/CSS3",
        "Backend & Distributed Systems": "Node.js, Express.js, FastAPI, Redis, Distributed Locking, Message Queues (BullMQ), WebSockets, System Design, REST APIs, Microservices",
        "Databases & Storage": "PostgreSQL, MongoDB, ChromaDB (Vector DB), Redis, Write-Ahead Logging (WAL)",
        "AI & LLM Systems": "OpenAI API, Google Gemini API, LangChain, LangGraph, RAG, Vector Embeddings, Prompt Chaining",
        "DevOps & Developer Tools": "Docker, Kubernetes, Linux, Git, GitHub Actions (CI/CD), Postman, Firebase Cloud Functions, k6, Sentry"
    }

    # Baseline Summary
    default_summary = (
        f"Full Stack Engineer with production experience architecting high-throughput booking platforms, distributed task queues, "
        f"and transactional financial systems. Proven expertise in Node.js, Next.js, Python, Redis distributed locking, and event-driven microservices. "
        f"Passionate about building resilient, low-latency architectures with verified benchmarks for {company_name}."
    )

    tailored_summary = default_summary
    tailored_skills = dict(master_skills)
    tailored_exp = list(master_exp)
    tailored_projects = list(master_projects)

    # ── SURGICAL OPENAI TAILORING WITH STRICT DEFENSIVE INVARIANTS ─────────────
    # Philosophy: Job descriptions have specific technical focuses. Rather than showing
    # a sprawling list of everything, present the candidate as the EXACT match for their stack
    # while maintaining 100% adherence to verified metrics, real experience, and strict 1-page limits.
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(base_dir, ".env"))
        api_key = os.getenv("OPENAI_API_KEY")

        if api_key and job_description.strip():
            import openai
            client = openai.Client(api_key=api_key)

            system_prompt = (
                "You are an elite, highly conservative Tech Resume Tailoring Specialist.\n"
                "YOUR MISSION:\n"
                "Surgically align the candidate's existing resume to be the PERFECT, focused fit for the target job.\n"
                "Do NOT present the candidate as a generic generalist who knows everything. Present them as a focused specialist in the stack and domain this team cares about.\n\n"
                "ABSOLUTE INVARIANTS & CARDINAL RULES (CRITICAL):\n"
                "1. ZERO HALLUCINATIONS: Do NOT invent skills, tools, roles, companies, degrees, or experiences.\n"
                "2. SACROSANCT METRICS: Every number, metric, and benchmark (e.g. 3,351 jobs/sec, sub-9.8ms P99, 100,000 background jobs, 10,000+ monthly reservations, 18% lift, +5 bookings/day, 100% balance reconciliation, 40% overhead, 30% page speed, 70% storage footprint, 16,384 shards) MUST REMAIN 100% UNCHANGED. NEVER alter, delete, or round them.\n"
                "3. SLIGHT SURGICAL TWEAKS ONLY:\n"
                "   - summary: 2-3 concise sentences (max 50 words). Anchor directly on the target company and role's core domain.\n"
                "   - skills: Return the exact same 5 categories but prioritized and ordered so the categories and tools most relevant to this JD appear FIRST. Omit irrelevant buzzwords.\n"
                "   - bullet_lead_tags: A JSON dictionary mapping existing bullet bold titles to subtly refined bold titles that mirror the JD's technical lexicon without changing the underlying fact (e.g. 'Distributed Concurrency & Locking' -> 'Distributed Concurrency & State Locking').\n"
                "4. STRICT LENGTH BUDGET: The output must preserve exact word/character bounds to guarantee it fits on 1 page.\n\n"
                "Return JSON ONLY with this schema:\n"
                "{\n"
                "  \"tailored_summary\": \"...\",\n"
                "  \"tailored_skills\": {\"Category Name\": \"item, item, item\", ...},\n"
                "  \"bullet_tag_replacements\": {\"Original Tag\": \"Refined Tag\"}\n"
                "}"
            )

            user_content = (
                f"Target Role: {job_title}\n"
                f"Target Company: {company_name}\n"
                f"Job Description Excerpt:\n{job_description[:3500]}\n\n"
                f"Candidate Baseline Summary:\n{default_summary}\n\n"
                f"Candidate Baseline Skills:\n{json.dumps(master_skills, indent=2)}\n\n"
                f"Candidate Existing Bullet Titles:\n"
                "- Distributed Concurrency & Locking\n"
                "- Checkout Recommendation Engine\n"
                "- Double-Entry Financial Ledger\n"
                "- In-House Notification & Scheduling Engine\n"
                "- Platform Engineering & Scheduling\n"
                "- API Contracts & Cross-Stack Integration\n"
                "- Frontend Performance Optimization\n"
                "- Cluster Hash-Slot Architecture\n"
                "- Atomic Lua Dequeuing & Orphan Reaper\n"
                "- Benchmarking & Resilience\n"
                "- Real-Time Concurrency Control\n"
                "- ML Dynamic Pricing Microservice\n"
                "- Secure Payment & Automated Ticketing\n"
                "- Append-Only Storage & WAL Engine\n"
                "- Semantic RAG Interface\n"
                "- Data Compression"
            )

            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            result = json.loads(resp.choices[0].message.content)

            # 1. Apply Tailored Summary (with length sanity check)
            s = result.get("tailored_summary", "").strip()
            if s and len(s.split()) <= 65:
                tailored_summary = s

            # 2. Apply Tailored Skills (validate exactly non-empty dict)
            sk = result.get("tailored_skills")
            if isinstance(sk, dict) and len(sk) in [4, 5]:
                tailored_skills = sk

            # 3. Apply Subtle Bullet Tag Replacements (validate tags exist)
            tag_map = result.get("bullet_tag_replacements", {})
            if isinstance(tag_map, dict) and tag_map:
                # Apply to Experience
                new_exp = []
                for exp_item in master_exp:
                    updated_bullets = []
                    for b in exp_item["bullets"]:
                        updated_b = b
                        for orig_tag, new_tag in tag_map.items():
                            if f"<b>{orig_tag}:</b>" in updated_b:
                                updated_b = updated_b.replace(f"<b>{orig_tag}:</b>", f"<b>{new_tag}:</b>")
                        updated_bullets.append(updated_b)
                    new_exp.append({**exp_item, "bullets": updated_bullets})
                tailored_exp = new_exp

                # Apply to Projects
                new_proj = []
                for proj_item in master_projects:
                    updated_bullets = []
                    for b in proj_item["bullets"]:
                        updated_b = b
                        for orig_tag, new_tag in tag_map.items():
                            if f"<b>{orig_tag}:</b>" in updated_b:
                                updated_b = updated_b.replace(f"<b>{orig_tag}:</b>", f"<b>{new_tag}:</b>")
                        updated_bullets.append(updated_b)
                    new_proj.append({**proj_item, "bullets": updated_bullets})
                tailored_projects = new_proj

            print(f"   🎯 Surgical OpenAI JD alignment applied for {company_name} ({job_title})")

    except Exception as e:
        print(f"   ℹ️ OpenAI tailoring fallback to pristine baseline: {e}")
        tailored_summary = default_summary
        tailored_skills = master_skills
        tailored_exp = master_exp
        tailored_projects = master_projects

    resume_payload = {
        "name": profile.full_name,
        "contact": (
            f"Jaipur, India &nbsp;<font color='#94A3B8'>|</font>&nbsp; +91-9871057729 &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
            f"<a href='mailto:{profile.email}'><u>{profile.email}</u></a> &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
            f"<a href='https://linkedin.com/in/prathmeshupadhyay008'><u>linkedin.com/in/prathmeshupadhyay008</u></a> &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
            f"<a href='https://github.com/prathmesh008'><u>github.com/prathmesh008</u></a> &nbsp;<font color='#94A3B8'>|</font>&nbsp; "
            f"<a href='https://prathmesh.me'><u>prathmesh.me</u></a>"
        ),
        "summary": tailored_summary,
        "skills": tailored_skills,
        "experience": tailored_exp,
        "projects": tailored_projects,
        "education": [
            {
                "school": "Vellore Institute of Technology (VIT)",
                "location": "Vellore, India",
                "degree": "Bachelor of Technology in Computer Science and Engineering",
                "dates": "2022 – 2026",
                "coursework": "Data Structures & Algorithms, Operating Systems, Database Management Systems, Computer Networks, Distributed Systems, Object-Oriented Programming"
            }
        ]
    }

    pdf_path = build_ats_pdf(resume_payload, output_path)

    # Strict Fail-Safe: Verify PDF is strictly 1 page
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        if len(reader.pages) > 1:
            print(f"   ⚠️ Warning: Tailored PDF overflowed to {len(reader.pages)} pages. Re-rendering with pristine master.")
            resume_payload["summary"] = default_summary
            resume_payload["skills"] = master_skills
            resume_payload["experience"] = master_exp
            resume_payload["projects"] = master_projects
            pdf_path = build_ats_pdf(resume_payload, output_path)
    except Exception as err:
        print(f"   ⚠️ PDF verification warning: {err}")

    print(f"   📄 Dynamically tailored ATS Resume generated: {pdf_path}")
    return pdf_path
