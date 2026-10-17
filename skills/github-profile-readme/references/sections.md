# README section snippets

GitHub strips CSS and `style`; only `align`, `width`, `height` and tables work. Replace `<user>` and names.

## Card + navigation

```html
<div align="center">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="./card-light.svg">
    <img src="./card.svg" alt="Profile card: <name>, <course or role>" width="820">
  </picture>
  <br><br>
  <a href="#selected-work">Work</a> &nbsp;·&nbsp; <a href="#stack">Stack</a> &nbsp;·&nbsp; <a href="#education">Education</a> &nbsp;·&nbsp; <a href="#contact">Contact</a>
</div>

<sub>**How to read the card.** One sentence on the scale, what the colors mean, and "Updated daily."</sub>
```

## Selected work (2x2 cards, 800x400 thumbnails)

```html
<table>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/<user>/<repo>"><img src="./assets/work/<repo>.png" alt="<repo>"></a><br>
      <b><a href="https://github.com/<user>/<repo>"><repo></a></b> &nbsp;<sub>Python</sub><br>
      One line: what it does and the measurable fact.<br>
      <a href="https://example.com/demo">Live demo</a>
    </td>
    <td width="50%" valign="top"> ...second card... </td>
  </tr>
  <tr> ...two more... </tr>
</table>
```

## Stack badges (grouped; `logoColor` black for light-colored logos)

```html
**Languages** &nbsp;<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"> <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript">
```

Groups: Languages, AI/ML, Games/graphics, Tools. Only what the user really uses.

## Contact buttons

```html
<a href="https://www.linkedin.com/in/<handle>/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
```

Use only contact data the user already publishes.

## Certifications

```html
<details>
<summary>Certifications</summary>
<br>

Name (issuer), name (issuer).

<img src="./certificates/<file>.png" width="260" alt="<certificate name>">

</details>
```

## Optional extra

A decorative element (e.g. a pixel-art bonsai grown from the commit history) goes last, small, with a visible credit line to the tool and its author.
