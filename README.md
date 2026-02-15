# Common Voice Status

A GTK4/Adwaita application for viewing Mozilla Common Voice recording and validation statistics per language.

![Screenshot](data/screenshots/screenshot-01.png)

## Features

- View statistics per language: recorded hours, validated hours, speakers, sentences
- Compare Nordic languages (sv, no, da, fi) side by side
- Sort by most validated, most recorded, or most speakers
- Gap analysis — how much more is needed to reach the next milestone
- Direct link to contribute recordings on Common Voice
- Local cache with 1-hour TTL

## Installation

### Debian/Ubuntu

```bash
# Add repository
curl -fsSL https://yeager.github.io/debian-repo/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/yeager-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/yeager-archive-keyring.gpg] https://yeager.github.io/debian-repo stable main" | sudo tee /etc/apt/sources.list.d/yeager.list
sudo apt update
sudo apt install commonvoice-status
```

### Fedora/RHEL

```bash
sudo dnf config-manager --add-repo https://yeager.github.io/rpm-repo/yeager.repo
sudo dnf install commonvoice-status
```

### From source

```bash
pip install .
commonvoice-status
```

## 🌍 Contributing Translations

Help translate this app into your language! All translations are managed via Transifex.

**→ [Translate on Transifex](https://app.transifex.com/danielnylander/commonvoice-status/)**

### How to contribute:
1. Visit the [Transifex project page](https://app.transifex.com/danielnylander/commonvoice-status/)
2. Create a free account (or log in)
3. Select your language and start translating

### Currently supported languages:
Arabic, Czech, Danish, German, Spanish, Finnish, French, Italian, Japanese, Korean, Norwegian Bokmål, Dutch, Polish, Brazilian Portuguese, Russian, Swedish, Ukrainian, Chinese (Simplified)

### Notes:
- Please do **not** submit pull requests with .po file changes — they are synced automatically from Transifex
- Source strings are pushed to Transifex daily via GitHub Actions
- Translations are pulled back and included in releases

New language? Open an [issue](https://github.com/yeager/commonvoice-status/issues) and we'll add it!

## License

GPL-3.0-or-later — Daniel Nylander <daniel@danielnylander.se>
