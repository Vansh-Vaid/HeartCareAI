# HeartCareAI IEEE TeX Prompt Bundle

This bundle contains a ready-to-use mega prompt for generating an IEEE conference-style LaTeX paper ZIP for the HeartCareAI app.

## Files

- `MEGA_PROMPT_HeartCareAI_IEEE_TeX.md` - full prompt to create the LaTeX paper ZIP
- `PROJECT_FACTS_HeartCareAI.md` - project facts extracted from the local HeartCareAI repository
- `SCREENSHOT_CHECKLIST.md` - screenshot plan for app pages and paper figures
- `template_screenshots/` - optional screenshots extracted from the IEEE template PDF, if available

## How to Use

Give the mega prompt to the AI/tool that will generate the `.tex` project. Attach or provide access to:

- The HeartCareAI app folder
- The IEEE conference template PDF
- The app screenshots listed in `SCREENSHOT_CHECKLIST.md`
- The existing chart images under `app/static/charts/`

Ask the tool to return:

`HeartCareAI_IEEE_LaTeX_Paper.zip`

The generated paper should be original, properly cited, and clear that HeartCareAI is a screening support tool rather than a diagnostic medical device.
