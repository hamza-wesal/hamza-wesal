#!/usr/bin/env python3
"""Build README.md: neofetch-style layout (ASCII face left, stats right),
tech-stack badges, github-readme-stats cards, and a highlights section.
"""
import html

USERNAME = "hamza-wesal"

with open("face_ascii.txt") as f:
    raw_lines = f.read().split("\n")
while raw_lines and raw_lines[-1] == "":
    raw_lines.pop()
ascii_lines = [html.escape(l, quote=False) for l in raw_lines if l.strip() != ""]
ascii_block = "\n".join(ascii_lines)

stats_lines = [
    f"{USERNAME}@github",
    "-" * (len(USERNAME) + 7),
    "OS:         IIT Delhi (B.Tech)",
    "Domain:     Robotics & Embedded Systems",
    "Languages:  Python, C++",
    "Frameworks: ROS2, OpenCV, PyTorch",
    "Currently:  WiFi CSI sensing research",
    "Building:   ABU Robocon 2026 bot",
    "Shell:      bash / python3",
]
stats_block = "\n".join(html.escape(l, quote=False) for l in stats_lines)

badges = [
    ("Python", "3776AB", "python", "white"),
    ("C++", "00599C", "cplusplus", "white"),
    ("ROS2", "22314E", "ros", "white"),
    ("OpenCV", "5C3EE8", "opencv", "white"),
    ("PyTorch", "EE4C2C", "pytorch", "white"),
    ("Linux", "FCC624", "linux", "black"),
    ("Ubuntu", "E95420", "ubuntu", "white"),
    ("Raspberry Pi", "A22846", "raspberrypi", "white"),
    ("Git", "F05032", "git", "white"),
]
badge_md = " ".join(
    f'<img src="https://img.shields.io/badge/{label.replace(" ", "%20")}-{color}?style=for-the-badge&logo={logo}&logoColor={logo_color}" alt="{label}" />'
    for label, color, logo, logo_color in badges
)

readme = f"""<h1 align="center">Hamza Wesal</h1>
<p align="center">B.Tech student, IIT Delhi &middot; Robotics &amp; Embedded Systems</p>

<table>
<tr>
<td valign="top">

<pre>
{ascii_block}
</pre>

</td>
<td valign="top">

<pre>
{stats_block}
</pre>

</td>
</tr>
</table>

## Tech Stack

<p align="left">
{badge_md}
</p>

## GitHub Stats

<p align="left">
<img height="165" src="https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&theme=default" alt="{USERNAME}'s GitHub stats" />
<img height="165" src="https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&layout=compact&theme=default" alt="Top languages" />
</p>

## Highlights

- Robotics focus: perception (OpenCV, PyTorch) through to control (ROS2)
- Researching WiFi CSI sensing
- Building for **ABU Robocon 2026**
- Building a coaxial swerve-drive robot on ROS2 Humble, sim-first in RViz before hardware bring-up on a Raspberry Pi
"""

with open("README.md", "w") as f:
    f.write(readme)

print("Wrote README.md (%d bytes)" % len(readme))
