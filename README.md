# Coursera Downloader Pro: Custom UI/UX Redesign

> **Acknowledgments & Credits:** The core downloading engine of this application, was developed by touhid314. 
> 
> **My Contribution:** This specific fork focuses entirely on a visual overhaul and UI/UX modernization of the original PyQt5 interface to provide a more polished and intuitive user experience.

## Overview

This project is a custom graphical frontend built on top of a highly capable Coursera downloading engine. While the original repository provided excellent core functionality for archiving courses, my goal was to enhance the presentation layer. 

I redesigned the PyQt5 interface to make the tool feel more like a modern, premium desktop application, focusing on layout improvements, visual feedback, and overall aesthetic consistency.

## Tech Stack (Frontend Focus)

* **GUI Framework:** `PyQt5` (Focus on custom styling, layout management, and visual widgets).
* **Core Engine (Original Author):** Python, `requests`, `browser_cookie3` (Authentication), `BeautifulSoup4`.

## UI/UX Enhancements (My Contributions)

### 1. Visual Modernization
* Redesigned the main window layout to maximize screen real estate and improve the visual hierarchy of the configuration options.
* Applied custom Qt stylesheets (QSS) to give the application a more modern, cohesive, and visually appealing color palette and typography.

### 2. Improved User Feedback
* Enhanced the visual states of progress bars and console log outputs so users can track the downloading process of large courses more comfortably.
* Refined padding, margins, and widget alignment to ensure the interface looks professional across different screen resolutions.

## Core Engine Features (Powered by touhid314)
*The underlying engine inherited from the original repository includes:*
* **Seamless Cookie Extraction:** Automatic bypassing of complex login screens using `browser_cookie3`.
* **Smart Batch Processing:** Background downloading with resume capabilities.
* **Content Filtering:** Automatic resolution selection and subtitle downloading.

## Interface Showcase

*(Add your screenshots here showing your beautiful UI changes!)*
---
*UI/UX Customization by RoX452* | *Core Logic by touhid314*

<!--
Original License: CC BY-NC 4.0 / GPLv3 (See COPYING.txt)
-->