# UC San Diego Web Brand Reference

Sources:

- Main brand site: https://brand.ucsd.edu/
- Logos: https://brand.ucsd.edu/logos/index.html
- Primary campus logo: https://brand.ucsd.edu/logos/primary-campus-logo/index.html
- Colors: https://brand.ucsd.edu/visual-brand/color/index.html
- Typography: https://brand.ucsd.edu/visual-brand/typography/index.html
- Web and digital: https://brand.ucsd.edu/using-the-brand/web-and-digital/index.html
- Accessibility guidance: https://accessibility.ucsd.edu/

## Core Colors

Primary:

| Token | Hex | Use |
| --- | --- | --- |
| `ucsd-navy` | `#182B49` | Primary identity, headers, nav, footer, major UI anchors |
| `ucsd-blue` | `#00629B` | Primary supporting blue, links, secondary actions |
| `ucsd-yellow` | `#FFCD00` | Primary bright accent, highlights, selected states, key calls to action |
| `ucsd-gold` | `#C69214` | Formal accent, rule line color in the primary logo |

Accents:

| Token | Hex |
| --- | --- |
| `ucsd-teal` | `#00C6D7` |
| `ucsd-magenta` | `#D462AD` |
| `ucsd-sand` | `#F5F0E6` |
| `ucsd-citron` | `#F3E500` |
| `ucsd-orange` | `#FC8900` |
| `ucsd-green` | `#6E963B` |

Neutrals:

| Token | Hex |
| --- | --- |
| `ucsd-white` | `#FFFFFF` |
| `ucsd-black` | `#000000` |
| `ucsd-cool-gray` | `#747678` |
| `ucsd-warm-gray` | `#B6B1A9` |

## CSS Tokens

Use these as a starting point, then adapt names to the project convention:

```css
:root {
  --ucsd-navy: #182B49;
  --ucsd-blue: #00629B;
  --ucsd-yellow: #FFCD00;
  --ucsd-gold: #C69214;
  --ucsd-teal: #00C6D7;
  --ucsd-magenta: #D462AD;
  --ucsd-sand: #F5F0E6;
  --ucsd-citron: #F3E500;
  --ucsd-orange: #FC8900;
  --ucsd-green: #6E963B;
  --ucsd-cool-gray: #747678;
  --ucsd-warm-gray: #B6B1A9;
  --ucsd-white: #FFFFFF;
  --ucsd-black: #000000;

  --color-brand-primary: var(--ucsd-navy);
  --color-brand-accent: var(--ucsd-yellow);
  --color-link: var(--ucsd-blue);
  --color-focus: var(--ucsd-yellow);
}
```

## Contrast Notes

Verify contrast in the actual UI state, not just in the palette. UC San Diego's accessibility site points web teams to WCAG 2.1 AA standards.

Known useful pairings:

| Foreground | Background | Notes |
| --- | --- | --- |
| `#FFFFFF` | `#182B49` | Strong for nav, hero, footer, and dark panels |
| `#182B49` | `#FFCD00` | Strong for yellow callouts or button text |
| `#182B49` | `#FFFFFF` | Strong for body text |
| `#00629B` | `#FFFFFF` | Usually acceptable for links and actions |
| `#000000` | `#FFCD00` | Strong, but less distinctly UCSD than navy on gold |

Avoid light accent colors as text on white. Avoid gold/yellow text on white. Always check hover, active, disabled, and focus states.

## Typography

Use UCSD's official type guidance in a practical web stack. Brix Sans is the primary brand font. For web, Roboto is the recommended substitute when Brix is not licensed or available. Use a traditional sans-serif stack as backup.

Recommended default pattern:

```css
body {
  font-family: Roboto, "Helvetica Neue", Helvetica, Arial, sans-serif;
}

h1,
h2,
h3,
h4,
h5,
h6 {
  font-family: Roboto, "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-weight: 700;
}
```

If the project already has approved Brix Sans or UCSD template font loading, keep it. Do not add external font services without checking project policy, licensing, privacy, and performance impact.

## Logo And Identity

- Use official UC San Diego logo files from the brand site, official downloads, or approved local assets.
- Preserve logo proportions, clear space, and legibility.
- Do not rebuild the logo with text, SVG approximations, or CSS.
- Do not recolor the logo outside approved variants.
- Do not reproduce the logo in solid gold or yellow.
- Keep the logo at least 125px wide in web and digital applications.
- Put the UC San Diego identity in a predictable header/masthead or footer when the site represents the university, a UCSD unit, or an official program.
- For department or program sites, keep UC San Diego identity clear while allowing the unit name to carry page-specific hierarchy.

## Web Implementation Checklist

Before shipping a UCSD-branded web page or app:

- Header or masthead uses approved UC San Diego identity assets.
- Colors use official UCSD tokens or justified neutral support colors.
- Links, buttons, focus rings, selected states, and alerts meet contrast requirements.
- Typography follows UCSD guidance or an approved local site convention.
- Navigation is predictable, keyboard-accessible, and responsive.
- Page hierarchy is clear: one meaningful `h1`, structured headings, readable body text.
- Images include meaningful alt text or are correctly decorative.
- Footer includes appropriate UCSD or unit identity and required links for the context.
- Mobile layout preserves logo legibility and does not hide essential identity.
- Browser inspection or screenshot review confirms there are no layout collisions.
- Accessibility review covers WCAG 2.1 AA basics for color contrast, keyboard use, labels, headings, alt text, and responsive behavior.

## Review Output Format

When reviewing a site, report:

1. Brand blockers: issues that clearly violate UCSD brand or accessibility expectations.
2. Recommended fixes: scoped implementation changes with file paths.
3. Nice-to-have refinements: optional polish that improves brand fit.
4. Checks run: script commands, build/lint/browser checks, and anything not run.

Do not overstate certification. Say "aligned with the checked UCSD brand guidance" rather than "officially approved" unless an authorized UCSD brand review has happened.
