"""
Acquisition brief generator — uses GPT-4.1-nano to produce editorial briefs
for the top-ranked candidates. Each brief includes subtitle angle + 2-3 paragraph
intellectual context for the production pipeline.
"""
import json
from openai import OpenAI


def generate_briefs(candidates, config, output_path):
    client = OpenAI(api_key=config["openai_api_key"])
    lines = []
    lines.append("# Heritage Research — Acquisition Briefs\n")

    for i, c in enumerate(candidates, 1):
        author = c.get("author", "Unknown")
        title = c.get("title", "Unknown")
        why_now = c.get("why_now", "")
        signals = "\n".join(f"- {s}" for s in c.get("signals", []))

        prompt = f"""You are an acquisitions editor for Heritage Canon, a philosophical annotated editions series.

A research scan has flagged the following public domain work as a high-priority candidate:
Author: {author}
Title: {title}
Why now: {why_now}
Signals:
{signals}

Produce a brief acquisition memo with:
1. A subtitle angle (4–8 words, the contemporary hook — e.g. "The Bureaucratic Lie We Agree to Live")
2. A 2–3 paragraph intellectual brief for the intro writer: the central argument the introduction should make, the philosophical tradition it sits in, and the key contemporary parallels that make this work urgent now.

Be concrete and specific. Avoid generic praise. Show the tension."""

        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are a literary acquisitions editor specialising in philosophical annotated editions of public domain works."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=400,
            )
            brief_text = resp.choices[0].message.content.strip()
        except Exception as e:
            brief_text = f"[Brief generation failed: {e}]"

        lines.append(f"## {i}. {author} — {title}")
        lines.append(f"**Score**: {c.get('score', 0):.1f} | **Sources**: {', '.join(set(c.get('sources', [])))}")
        lines.append(f"**Why now**: {why_now}\n")
        lines.append(brief_text)
        lines.append("\n---\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
