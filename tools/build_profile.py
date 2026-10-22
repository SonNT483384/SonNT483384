# -*- coding: utf-8 -*-
"""Render the profile README panels as SVG, in a dark and a light variant.

GitHub strips CSS from README markdown, so the card / pill look is drawn as SVG
and embedded with <picture>. Text is measured with PIL so lines wrap correctly.

    python tools/build_profile.py
"""

import os
import re

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(ROOT, "assets", "icons")
OUT_DIR = os.path.join(ROOT, "assets")

W = 880  # README content width
FONT_STACK = (
    "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',"
    "Helvetica,Arial,sans-serif"
)

WIN_FONTS = r"C:\Windows\Fonts"
_font_cache = {}
_icon_cache = {}

EMOJI = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\u2b00-\u2bff]")
ZERO_WIDTH = "\ufe0f\u200d"


def _font(size, bold):
    key = (size, bold)
    if key not in _font_cache:
        name = "arialbd.ttf" if bold else "arial.ttf"
        _font_cache[key] = ImageFont.truetype(os.path.join(WIN_FONTS, name), size)
    return _font_cache[key]


def tw(text, size, bold=False):
    """Approximate rendered width in px (Arial metrics: slightly generous)."""
    total = 0.0
    run = ""
    for ch in text:
        if ch in ZERO_WIDTH:
            continue
        if EMOJI.match(ch):
            if run:
                total += _font(size, bold).getlength(run)
                run = ""
            total += size * 1.25
        else:
            run += ch
    if run:
        total += _font(size, bold).getlength(run)
    return total


def wrap(text, size, max_w, bold=False):
    lines, cur = [], ""
    for word in text.split():
        nxt = (cur + " " + word).strip()
        if not cur or tw(nxt, size, bold) <= max_w:
            cur = nxt
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def esc(s):
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def icon_path(slug):
    if slug not in _icon_cache:
        with open(os.path.join(ICON_DIR, slug + ".svg"), encoding="utf-8") as fh:
            _icon_cache[slug] = re.search(r'\sd="([^"]+)"', fh.read()).group(1)
    return _icon_cache[slug]


# --------------------------------------------------------------------------- colour

def _hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Blend colour a towards b by t (0..1)."""
    ra, rb = _hx(a), _hx(b)
    return "#%02x%02x%02x" % tuple(round(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))


THEMES = {
    "dark": dict(
        text="#e6edf3",
        muted="#9198a1",
        subtle="#6e7681",
        border="#30363d",
        card="#161b22",
        rule="#21262d",
        accent="#2f81f7",
        ink="#0d1117",
        chip_alpha=0.18,
        chip_lift=0.40,
        dark_brand="#1c2128",
        dark_brand_edge="#424a53",
    ),
    "light": dict(
        text="#1f2328",
        muted="#59636e",
        subtle="#818b98",
        border="#d1d9e0",
        card="#f6f8fa",
        rule="#d1d9e0",
        accent="#0969da",
        ink="#ffffff",
        chip_alpha=0.14,
        chip_lift=0.0,
        dark_brand="#24292f",
        dark_brand_edge=None,
    ),
}

BLACKISH = {"#000000", "#010101", "#000020", "#092e20", "#2b037a"}


# --------------------------------------------------------------------------- svg bits

def rect(x, y, w, h, r, fill, stroke=None, opacity=None):
    s = '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s"' % (
        x, y, w, h, r, fill,
    )
    if opacity is not None:
        s += ' fill-opacity="%.2f"' % opacity
    if stroke:
        s += ' stroke="%s" stroke-width="1"' % stroke
    return s + "/>"


def text(x, y, s, size, fill, bold=False, anchor="start", opacity=None):
    out = (
        '<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" fill="%s"'
        % (x, y, FONT_STACK, size, fill)
    )
    if bold:
        out += ' font-weight="600"'
    if anchor != "start":
        out += ' text-anchor="%s"' % anchor
    if opacity is not None:
        out += ' opacity="%.2f"' % opacity
    return out + ">%s</text>" % esc(s)


def glyph(slug, x, y, size, fill):
    s = size / 24.0
    return '<g transform="translate(%.2f,%.2f) scale(%.4f)"><path d="%s" fill="%s"/></g>' % (
        x, y, s, icon_path(slug), fill,
    )


def section_title(x, y, label, th):
    """Heading in the same rhythm as GitHub's own h2."""
    return [text(x, y, label, 19, th["text"], bold=True)]


# --------------------------------------------------------------------------- content

TECH = [
    ("Languages", [
        ("TypeScript", "typescript", "#3178C6", "#ffffff"),
        ("JavaScript", "javascript", "#F7DF1E", "#111418"),
        ("Python", "python", "#3776AB", "#ffffff"),
        ("C#", None, "#68217A", "#ffffff"),
        ("Java", "openjdk", "#E76F00", "#ffffff"),
        ("SQL", None, "#336791", "#ffffff"),
    ]),
    ("Backend", [
        ("NestJS", "nestjs", "#E0234E", "#ffffff"),
        ("TypeORM", "typeorm", "#FE0803", "#ffffff"),
        ("Express", "express", "#000000", "#ffffff"),
        (".NET Core", "dotnet", "#512BD4", "#ffffff"),
        ("Django", "django", "#092E20", "#ffffff"),
        ("Socket.IO", "socketdotio", "#010101", "#ffffff"),
    ]),
    ("Frontend", [
        ("React", "react", "#087EA4", "#ffffff"),
        ("Next.js", "nextdotjs", "#000000", "#ffffff"),
        ("Ant Design", "antdesign", "#0170FE", "#ffffff"),
        ("TanStack Query", "reactquery", "#FF4154", "#ffffff"),
        ("Tailwind CSS", "tailwindcss", "#06B6D4", "#ffffff"),
        ("Expo", "expo", "#000020", "#ffffff"),
    ]),
    ("Data & AI", [
        ("PostgreSQL", "postgresql", "#336791", "#ffffff"),
        ("pgvector", None, "#4A6FA5", "#ffffff"),
        ("MS SQL", None, "#CC2927", "#ffffff"),
        ("MySQL", "mysql", "#4479A1", "#ffffff"),
        ("MongoDB", "mongodb", "#47A248", "#ffffff"),
        ("Redis", "redis", "#DC382D", "#ffffff"),
        ("OpenAI", "openai", "#000000", "#ffffff"),
        ("Gemini", "googlegemini", "#4285F4", "#ffffff"),
    ]),
    ("DevOps & Testing", [
        ("Docker", "docker", "#2496ED", "#ffffff"),
        ("GitHub Actions", "githubactions", "#2088FF", "#ffffff"),
        ("Nginx", "nginx", "#009639", "#ffffff"),
        ("PM2", "pm2", "#2B037A", "#ffffff"),
        ("Linux", "linux", "#FCC624", "#111418"),
        ("Jest", "jest", "#C21325", "#ffffff"),
        ("Playwright", None, "#2EAD33", "#ffffff"),
    ]),
]

FEATURED = [
    dict(
        emoji="\U0001f3d9\ufe0f",
        title="Urban Sanitation Fee Platform",
        body="Household registry, field surveys, pricing, receivables, POS collection, "
             "e-invoicing and staff KPI / salary for a waste-collection company.",
        chips=[("NestJS", "#E0234E"), ("PostgreSQL", "#336791"), ("React", "#087EA4")],
        meta="Bmedical \u00b7 Xu\u00e2n Mai Urenco \u00b7 2026",
    ),
    dict(
        emoji="\U0001f4ac",
        title="CRM & AI Assistant",
        body="Clinic CRM with an omnichannel inbox for Facebook, Pancake and Zalo OA, "
             "plus a RAG customer-service assistant built on pgvector.",
        chips=[("NestJS", "#E0234E"), ("pgvector", "#4A6FA5"), ("Next.js", "#6e7681")],
        meta="Bmedical \u00b7 V-Life Beauty Clinic \u00b7 2026",
    ),
    dict(
        emoji="\U0001fa7a",
        title="Healthcare Content Platform",
        body="Medical content platform and a nationwide doctor directory with KYC "
             "verification, deployed and operated on cloud servers.",
        chips=[("NestJS", "#E0234E"), ("Next.js", "#6e7681"), ("PM2", "#2B037A")],
        meta="Bmedical \u00b7 B\u00e1c S\u0129 \u01a0i \u00b7 2025\u20132026",
    ),
]

EXPERIENCE = [
    dict(
        company="Bmedical",
        role="Full Stack Engineer",
        period="09/2025 \u2013 Present",
        projects=[
            dict(
                name="Xu\u00e2n Mai Urenco \u2014 Urban Sanitation Fee Management Platform",
                period="07/2026 \u2013 Present",
                stack="NestJS \u00b7 TypeORM \u00b7 PostgreSQL \u00b7 React \u00b7 Ant Design",
                bullets=[
                    "Lead contributor across backend and frontend; module structure and "
                    "role-based access.",
                    "Designed the pricing and receivables engine: regional price lists, "
                    "multiple charge bases, automatic recalculation with audit trail.",
                    "Built survey-to-registry reconciliation with configurable criteria; "
                    "an indexed matcher cut a 58-second run down to 1.3 s.",
                    "Implemented the field-staff salary and KPI engine; integrated MISA "
                    "e-invoicing and SePay / VietQR bank webhooks.",
                ],
            ),
            dict(
                name="V-Life Beauty Clinic \u2014 CRM & AI customer-service assistant",
                period="04/2026 \u2013 09/2026",
                stack="NestJS \u00b7 PostgreSQL \u00b7 Socket.IO \u00b7 Next.js",
                bullets=[
                    "Built the CRM (leads, appointments, patients, contracts) and an "
                    "omnichannel inbox for Facebook, Pancake and Zalo OA.",
                    "Owned the AI assistant: RAG on pgvector with Gemini / OpenAI, "
                    "knowledge ingestion, safety rules and a public API.",
                ],
            ),
            dict(
                name="V-Life \u2014 B\u00e1c S\u0129 \u01a0i (healthcare content platform "
                     "& doctor directory)",
                period="09/2025 \u2013 2026",
                stack="NestJS \u00b7 Next.js \u00b7 PostgreSQL",
                bullets=[
                    "Healthcare content platform and a nationwide doctor directory with "
                    "KYC verification.",
                    "Deployed and operated with PM2 and Nginx on cloud servers; CI/CD "
                    "with GitHub Actions.",
                ],
            ),
        ],
    ),
    dict(
        company="Luong Hoa Tien",
        role="Full Stack Engineer",
        period="08/2024 \u2013 08/2025",
        projects=[
            dict(
                name="School management systems",
                period="08/2024 \u2013 08/2025",
                stack=".NET Core \u00b7 Entity Framework \u00b7 MS SQL \u00b7 ReactJS",
                bullets=[
                    "Built student records, classes, schedules and academic reports; "
                    "wrote unit tests.",
                    "Worked with business analysts to analyse requirements and configure "
                    "the system for each school.",
                ],
            ),
        ],
    ),
]

PROJECTS = [
    dict(
        title="Multi-account Operations Automation Toolkit",
        body="Runs many social-media and mail accounts from one machine: browser "
             "automation over isolated profiles, Android UI automation, and a Gmail "
             "manager with OAuth, scheduling and a Telegram control bot.",
        chips=["Python", "Playwright", "uiautomator2 / ADB", "Gmail API"],
    ),
    dict(
        title="AI Video Search & Frame Extraction Tool",
        body="Keyword-based video ingestion, FFmpeg frame sampling and AI-vision "
             "cropping, with a review dashboard for the content team.",
        chips=["Python", "Django", "Celery + Redis", "Gemini", "Docker"],
    ),
    dict(
        title="Assets & Equipment Repair Management (Capstone)",
        body="Repair-request workflows, reports and statistics for Company 35; "
             "front-end development plus SRS / SDS documentation.",
        chips=["NestJS", "ReactJS", "PostgreSQL"],
    ),
    dict(
        title="AI Attendance",
        body="Facial-recognition attendance with an admin website and a mobile app "
             "for teachers and school managers.",
        chips=["NestJS", "ReactJS", "React Native Expo", "MySQL", "Gemini"],
    ),
    dict(
        title="Project Management System (Jira clone)",
        body="Projects, members, task tracking and in-task chat with auto-generated "
             "statistics.",
        chips=["Next.js", "Socket.IO", "Express", "MongoDB"],
    ),
    dict(
        title="Internal DevOps & Automation Toolkit",
        body="Scheduled crawling, reports and deployments through Python scripts and "
             "Django mini-apps, shipped with CI/CD on Linux servers.",
        chips=["Python", "Django", "Bash", "Docker", "GitHub Actions"],
    ),
]

STATS = [
    ("2+", "Years of experience", "Full-stack, production systems"),
    ("4", "Production platforms", "Healthcare & public utility"),
    ("44\u00d7", "Faster reconciliation", "58 s \u2192 1.3 s indexed matcher"),
]

CERTS = [
    "CertNexus Certified Ethical Emerging Technologist",
    "Software Development Lifecycle \u2014 University of Minnesota",
    "Web Design for Everybody \u2014 University of Michigan",
    "Computer Communications \u2014 University of Colorado System",
    "Academic Skills for University Success \u2014 The University of Sydney",
    "Object-Oriented Programming in Java \u00b7 Data Structures and Algorithms",
    "Software Requirements \u00b7 Software Testing",
]


# --------------------------------------------------------------------------- pieces

PILL_H = 32
PILL_R = 9


def pill(x, y, label, slug, bg, fg, th):
    """Brand pill: rounded, icon on the left, label on the right."""
    dark_brand = bg.lower() in BLACKISH
    fill = th["dark_brand"] if dark_brand else bg
    edge = th["dark_brand_edge"] if dark_brand else None
    pad = 11
    icon_w = 15 if slug else 0
    gap = 7 if slug else 0
    label_w = tw(label, 12.5, bold=True)
    w = pad + icon_w + gap + label_w + pad
    out = [rect(x, y, w, PILL_H, PILL_R, fill, stroke=edge)]
    if slug:
        out.append(glyph(slug, x + pad, y + (PILL_H - 15) / 2, 15, fg))
    out.append(
        text(x + pad + icon_w + gap, y + PILL_H / 2 + 4.4, label, 12.5, fg, bold=True)
    )
    return out, w


def chip(x, y, label, color, th, size=11):
    """Small tinted tag used inside cards."""
    fg = mix(color, "#ffffff", th["chip_lift"]) if th["chip_lift"] else color
    pad = 8
    h = 20
    w = pad * 2 + tw(label, size, bold=True)
    out = [
        rect(x, y, w, h, 6, color, opacity=th["chip_alpha"]),
        text(x + pad, y + h / 2 + 3.9, label, size, fg, bold=True),
    ]
    return out, w


def date_tag(x_right, y, label, th):
    pad = 9
    h = 22
    w = pad * 2 + tw(label, 11.5)
    x = x_right - w
    return [
        rect(x, y, w, h, 7, th["card"], stroke=th["border"]),
        text(x + pad, y + h / 2 + 4, label, 11.5, th["muted"]),
    ], w


# --------------------------------------------------------------------------- panels

def panel_header(th):
    o = []
    y = 34
    o.append(text(0, y, "\U0001f44b Hi there, I'm Nguyen Thai Son!", 30, th["text"], bold=True))
    y += 30
    lead = "Software Engineer \u00b7 Full Stack at "
    o.append(text(0, y, lead, 16, th["muted"]))
    x = tw(lead, 16)
    o.append(text(x, y, "Bmedical", 16, th["accent"], bold=True))
    x += tw("Bmedical", 16, True) + 14
    for i, c in enumerate(("#f78166", "#2f81f7", "#3fb950")):
        o.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s"/>' % (x + i * 16, y - 5, c))
    y += 20
    o.append(rect(0, y, W, 1, 0.5, th["rule"]))
    y += 26
    intro = (
        "Full-stack engineer with 2+ years building production systems for healthcare "
        "and public-utility clients. I own features end to end \u2014 data model, business "
        "rules, API, UI, tests and deployment \u2014 and enjoy turning messy real-world "
        "rules into reliable software."
    )
    for line in wrap(intro, 14.5, W):
        o.append(text(0, y, line, 14.5, th["muted"]))
        y += 22
    return o, y - 8


def panel_tech(th):
    o = section_title(0, 20, "Tech Stack", th)
    y = 44
    for group, items in TECH:
        o.append(text(0, y + 10, group, 11.5, th["subtle"], bold=True))
        y += 20
        x = 0
        for label, slug, bg, fg in items:
            parts, w = pill(x, y, label, slug, bg, fg, th)
            if x + w > W:  # wrap the row
                x = 0
                y += PILL_H + 9
                parts, w = pill(x, y, label, slug, bg, fg, th)
            o += parts
            x += w + 9
        y += PILL_H + 18
    return o, y - 4


def panel_featured(th):
    o = section_title(0, 20, "Featured Work", th)
    top = 42
    gap = 16
    cw = (W - gap * 2) / 3.0
    ch = 206
    for i, card in enumerate(FEATURED):
        x = i * (cw + gap)
        o.append(rect(x, top, cw, ch, 12, th["card"], stroke=th["border"]))
        o.append(text(x + 18, top + 36, card["emoji"], 17, th["text"]))
        ty = top + 36
        for line in wrap(card["title"], 14.5, cw - 62, bold=True):
            o.append(text(x + 44, ty, line, 14.5, th["text"], bold=True))
            ty += 19
        by = ty + 8
        for line in wrap(card["body"], 12.5, cw - 36)[:5]:
            o.append(text(x + 18, by, line, 12.5, th["muted"]))
            by += 18
        cy = top + ch - 56
        cx = x + 18
        for label, color in card["chips"]:
            parts, w = chip(cx, cy, label, color, th)
            o += parts
            cx += w + 6
        o.append(text(x + 18, top + ch - 16, card["meta"], 11, th["subtle"]))
    return o, top + ch + 6


def panel_experience(th):
    o = section_title(0, 20, "Work Experience", th)
    y = 56
    for ci, job in enumerate(EXPERIENCE):
        if ci:
            y += 10
            o.append(rect(0, y, W, 1, 0.5, th["rule"]))
            y += 26
        head = job["company"]
        o.append(text(0, y, head, 16.5, th["text"], bold=True))
        x = tw(head, 16.5, True) + 10
        o.append(text(x, y, "\u2014  " + job["role"], 14, th["muted"]))
        tag, _ = date_tag(W, y - 16, job["period"], th)
        o += tag
        y += 26
        for pj in job["projects"]:
            start = y
            block = []  # drawn after the rail, whose height we only know at the end
            for line in wrap(pj["name"], 13.5, W - 170, bold=True):
                block.append(text(18, y + 10, line, 13.5, th["text"], bold=True))
                y += 19
            tag, _ = date_tag(W, start - 4, pj["period"], th)
            block += tag
            y += 2
            block.append(text(18, y + 10, pj["stack"], 11.5, th["subtle"]))
            y += 22
            for b in pj["bullets"]:
                block.append(
                    '<circle cx="22.5" cy="%.1f" r="2.1" fill="%s"/>' % (y + 6, th["subtle"])
                )
                for line in wrap(b, 12.5, W - 46):
                    block.append(text(32, y + 10, line, 12.5, th["muted"]))
                    y += 18
                y += 3
            o.append(rect(0, start + 2, 3, y - start - 8, 1.5, th["rule"]))
            o += block
            y += 12
    return o, y


def panel_projects(th):
    o = section_title(0, 20, "Projects", th)
    top = 42
    gap = 16
    cw = (W - gap) / 2.0
    ch = 148
    y = top
    for i, p in enumerate(PROJECTS):
        col = i % 2
        if col == 0 and i:
            y += ch + gap
        x = col * (cw + gap)
        o.append(rect(x, y, cw, ch, 12, th["card"], stroke=th["border"]))
        ty = y + 30
        for line in wrap(p["title"], 14, cw - 36, bold=True):
            o.append(text(x + 18, ty, line, 14, th["text"], bold=True))
            ty += 19
        ty += 6
        for line in wrap(p["body"], 12.5, cw - 36)[:4]:
            o.append(text(x + 18, ty, line, 12.5, th["muted"]))
            ty += 18
        cx = x + 18
        cy = y + ch - 32
        for label in p["chips"]:
            parts, w = chip(cx, cy, label, th["accent"], th, size=10.5)
            if cx + w > x + cw - 14:
                break
            o += parts
            cx += w + 6
    return o, y + ch + 6


def panel_stats(th):
    o = section_title(0, 20, "By the numbers", th)
    top = 42
    gap = 16
    cw = (W - gap * 2) / 3.0
    ch = 104
    for i, (value, label, sub) in enumerate(STATS):
        x = i * (cw + gap)
        o.append(rect(x, top, cw, ch, 12, th["card"], stroke=th["border"]))
        o.append(text(x + cw / 2, top + 48, value, 32, th["text"], bold=True, anchor="middle"))
        o.append(text(x + cw / 2, top + 72, label, 13, th["text"], anchor="middle"))
        o.append(text(x + cw / 2, top + 90, sub, 11, th["subtle"], anchor="middle"))
    return o, top + ch + 6


def panel_education(th):
    o = section_title(0, 20, "Education, Certificates & Languages", th)
    top = 42
    gap = 16
    cw = (W - gap) / 2.0
    ch = 206
    # left card
    o.append(rect(0, top, cw, ch, 12, th["card"], stroke=th["border"]))
    o.append(text(18, top + 32, "\U0001f393 Education", 13.5, th["text"], bold=True))
    o.append(text(18, top + 58, "FPT University \u2014 Software Engineering", 13, th["text"]))
    o.append(text(18, top + 78, "11/2021 \u2013 12/2025  \u00b7  GPA 3.0 / 4.0", 12, th["muted"]))
    o.append(rect(18, top + 96, cw - 36, 1, 0.5, th["rule"]))
    o.append(text(18, top + 124, "\U0001f310 Languages", 13.5, th["text"], bold=True))
    cx = 18
    for label, color in (("English \u00b7 B2+", "#2f81f7"), ("Vietnamese \u00b7 Native", "#da251d")):
        parts, w = chip(cx, top + 138, label, color, th, size=11.5)
        o += parts
        cx += w + 8
    o.append(text(18, top + 182, "\U0001f4cd Ha Dong, Ha Noi \u2014 open to full-stack roles",
                  11.5, th["subtle"]))
    # right card
    x = cw + gap
    o.append(rect(x, top, cw, ch, 12, th["card"], stroke=th["border"]))
    o.append(text(x + 18, top + 32, "\U0001f4dc Courses & Certificates", 13.5, th["text"], bold=True))
    y = top + 56
    for i, c in enumerate(CERTS):
        colour = th["text"] if i == 0 else th["muted"]
        o.append('<circle cx="%.1f" cy="%.1f" r="2.1" fill="%s"/>' % (x + 21, y - 4, th["subtle"]))
        for line in wrap(c, 11.8, cw - 56)[:1]:
            o.append(text(x + 30, y, line, 11.8, colour, bold=(i == 0)))
        y += 20
    return o, top + ch + 6


def panel_contact(th):
    o = section_title(0, 20, "Contact", th)
    y = 38
    parts, w = pill(0, y, "sonnguyen04082003@gmail.com", "gmail", "#D14836", "#ffffff", th)
    o += parts
    parts2, w2 = pill(w + 10, y, "github.com/SonNT483384", "github", "#000000", "#ffffff", th)
    o += parts2
    o.append(text(w + w2 + 30, y + PILL_H / 2 + 4.4, "Ha Dong, Ha Noi", 12.5, th["subtle"]))
    return o, y + PILL_H + 8


PANELS = [
    ("header", panel_header),
    ("tech", panel_tech),
    ("featured", panel_featured),
    ("experience", panel_experience),
    ("projects", panel_projects),
    ("stats", panel_stats),
    ("education", panel_education),
    ("contact", panel_contact),
]


def render():
    os.makedirs(OUT_DIR, exist_ok=True)
    sizes = {}
    for name, fn in PANELS:
        for theme, th in THEMES.items():
            body, height = fn(th)
            height = int(round(height))
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
                'viewBox="0 0 %d %d" fill="none">%s</svg>'
            ) % (W, height, W, height, "".join(p for p in body if p))
            with open(os.path.join(OUT_DIR, "%s-%s.svg" % (name, theme)), "w",
                      encoding="utf-8") as fh:
                fh.write(svg)
            sizes[name] = height
    for name, h in sizes.items():
        print("%-12s %d x %d" % (name, W, h))


if __name__ == "__main__":
    render()
