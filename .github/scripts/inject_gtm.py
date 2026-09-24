"""Inject Google Tag Manager into the generated GitHub Pages artifact."""

import os
import re
import sys
from pathlib import Path


GTM_ID_PATTERN = re.compile(r"GTM-[A-Z0-9]+\Z")


def inject_gtm(page: Path, gtm_id: str) -> None:
    html = page.read_text(encoding="utf-8")
    head_tag = (
        "  <!-- Google Tag Manager -->\n"
        "  <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\n"
        "  new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\n"
        "  j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n"
        "  'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);\n"
        f"  }})(window,document,'script','dataLayer','{gtm_id}');</script>\n"
        "  <!-- End Google Tag Manager -->\n"
    )
    body_tag = (
        "  <!-- Google Tag Manager (noscript) -->\n"
        f'  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id={gtm_id}" '
        'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n'
        "  <!-- End Google Tag Manager (noscript) -->\n"
    )

    html, head_count = re.subn(r"</head>", head_tag + "</head>", html, count=1, flags=re.IGNORECASE)
    html, body_count = re.subn(r"(<body\b[^>]*>)", r"\1\n" + body_tag, html, count=1, flags=re.IGNORECASE)
    if head_count != 1 or body_count != 1:
        raise ValueError(f"Could not find the head and body insertion points in {page}")
    page.write_text(html, encoding="utf-8")


def main() -> None:
    gtm_id = os.environ.get("GTM_ID", "").strip()
    if not gtm_id:
        print("GTM_ID is unset; deploying without Google Tag Manager.")
        return
    if not GTM_ID_PATTERN.fullmatch(gtm_id):
        raise ValueError("GTM_ID must match the format GTM- followed by uppercase letters or digits")

    pages_dir = Path(sys.argv[1])
    for relative_page in ("index.html", "ja/index.html"):
        page = pages_dir / relative_page
        inject_gtm(page, gtm_id)
        print(f"Injected Google Tag Manager into {page}")


if __name__ == "__main__":
    main()
