# Open Graph Images

`og.html` is the source for the link-preview images used by GitHub Pages:

- `.github/pages/assets/og-image-en.png` (English page)
- `.github/pages/assets/og-image-ja.png` (Japanese page)

It reuses `.github/pages/assets/site.css` and the hero image, so update the images whenever the landing-page heading, tagline, or hero image changes. Keep the English and Japanese images equivalent.

Regenerate both images at 1200 × 630 from the repository root:

```bash
for lang in en ja; do
  google-chrome --headless=new --hide-scrollbars --allow-file-access-from-files \
    --window-size=1200,630 --virtual-time-budget=5000 \
    --screenshot=".github/pages/assets/og-image-$lang.png" \
    "file://$PWD/.github/og-image/og.html?lang=$lang"
done
```

This directory is not deployed; the workflow publishes only `.github/pages/`.
