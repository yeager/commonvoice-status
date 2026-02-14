# Common Voice Status

A GTK4/Adwaita application for viewing Mozilla Common Voice recording statistics per language.

![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)

## Features

- View statistics per language: recorded hours, validated hours, speakers, sentences
- Compare Nordic languages (sv, no, da, fi) side by side
- Sort by most validated, most recorded, or most speakers
- Gap analysis — how much more is needed to reach the next milestone
- Direct link to contribute recordings on Common Voice
- Local cache with 1-hour TTL (~/.cache/commonvoice-status/)

## Installation

### From .deb (Debian/Ubuntu)

```bash
curl -s https://yeager.github.io/debian-repo/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/yeager.gpg
echo "deb [signed-by=/usr/share/keyrings/yeager.gpg] https://yeager.github.io/debian-repo stable main" | sudo tee /etc/apt/sources.list.d/yeager.list
sudo apt update && sudo apt install commonvoice-status
```

### From .rpm (Fedora)

```bash
sudo dnf config-manager --add-repo https://yeager.github.io/rpm-repo/yeager.repo
sudo dnf install commonvoice-status
```

### From source

```bash
pip install .
commonvoice-status
```

## Requirements

- Python 3.10+
- GTK 4
- libadwaita 1
- PyGObject

## Data Source

Statistics are fetched from the [Common Voice API](https://commonvoice.mozilla.org/api/v1/stats/languages).

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).

## Author

Daniel Nylander <daniel@danielnylander.se>

## Translation

Translations are managed via [Transifex](https://app.transifex.com/danielnylander/commonvoice-status/). See [po/README.md](po/README.md) for details.
