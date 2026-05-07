---
name: ucsd-brand-compliance
description: Use for UC San Diego web development, redesign, code review, visual QA, CSS/theme work, or accessibility checks where a website, app, landing page, dashboard, or component must follow UCSD brand guidelines. Helps apply official UC San Diego logo, color, typography, layout, tone, and web accessibility requirements; review existing HTML/CSS/React/Vue/Svelte/static sites for brand compliance; and produce brand-safe design tokens or implementation notes.
---

# UCSD Brand Compliance

## Purpose

Use this skill to make UC San Diego web interfaces look and behave like official UCSD properties while staying accessible and implementation-practical.

## Workflow

1. Inspect the target app structure first. Find the relevant CSS/theme files, layout/header components, typography setup, and any logo/image assets.
2. Read `references/ucsd-web-brand.md` when you need exact brand colors, typography, logo rules, web expectations, or a review checklist.
3. Prefer existing project conventions. Add UCSD tokens to the current theme system instead of inventing a parallel styling layer.
4. Use official UCSD colors and type guidance. Avoid approximate blues/yellows, gradient-heavy generic styling, or unofficial logo recreations.
5. Treat accessibility as part of brand compliance. Check text contrast, focus states, keyboard behavior, responsive layout, and semantic headings.
6. Run `scripts/check_ucsd_brand.py` on relevant source files when practical to find non-brand hex colors or calculate contrast ratios.
7. If the work is public-facing or high-stakes, re-check the official brand site at `https://brand.ucsd.edu/` before finalizing because institutional standards can change.

## Implementation Guidance

- Use `#182B49` as UC San Diego navy, `#00629B` as UC San Diego blue, `#FFCD00` as UC San Diego yellow, and `#C69214` as UC San Diego gold. Use accent colors sparingly and intentionally.
- Do not recolor, redraw, stretch, crop, or compose the UC San Diego logo manually. Use official downloads or existing approved assets in the repo.
- Keep the site identity clear in the first viewport: official mark, UC San Diego name, department/program name, or another approved identity element should be visible where appropriate.
- Use clean, institutional layouts: restrained color, clear hierarchy, generous readable spacing, high contrast, and functional navigation.
- Use UCSD type guidance in a web-safe way. Prefer the official fallback stacks from the reference unless the project already has approved font loading.
- Avoid decorative one-note blue/gold theming. UCSD brand should read through identity, hierarchy, and precise color use, not just broad color tinting.
- Do not claim full compliance from source review alone. For meaningful UI work, run or view the page and check desktop/mobile rendering.

## Script

Run the color helper from the skill directory:

```bash
python3 scripts/check_ucsd_brand.py path/to/src path/to/index.html
```

Useful options:

```bash
python3 scripts/check_ucsd_brand.py --contrast '#182B49' '#FFCD00'
python3 scripts/check_ucsd_brand.py --json path/to/src
```

Use script output as a starting point, not a complete brand audit. It only sees literal hex colors and contrast pairs you ask it to calculate.
