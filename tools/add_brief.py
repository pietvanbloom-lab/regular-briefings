#!/usr/bin/env python3
"""Place a generated daily brief into the portal: ensure the shared enhance include,
save as briefs/<DATE>.html. Usage: add_brief.py <YYYY-MM-DD> <path-to-brief.html>"""
import sys, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INC = '<script src="../assets/brief-enhance.js"></script>'

def main():
    if len(sys.argv) != 3:
        print("usage: add_brief.py <YYYY-MM-DD> <brief.html>"); sys.exit(1)
    date, path = sys.argv[1], sys.argv[2]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        print("date must be YYYY-MM-DD"); sys.exit(1)
    html = open(path, encoding="utf-8").read()
    if INC not in html:
        html = html.replace("</body>", "  " + INC + "\n</body>", 1) if "</body>" in html else html + "\n" + INC
    out = os.path.join(ROOT, "briefs", date + ".html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print("wrote", out)

if __name__ == "__main__":
    main()
