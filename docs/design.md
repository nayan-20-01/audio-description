# Design Guidelines
## Streamlit Dashboard — Academic, Accessible UI/UX

### 1. Design Philosophy
The interface serves an accessibility-focused educational tool — it should read as **calm, credible, and institutional**, not consumer-flashy. Visual hierarchy should prioritize clarity and status feedback (upload progress, processing stage, errors) over decoration, since part of the user base cares about screen-reader compatibility and low visual noise.

### 2. Color Palette

**Primary (Academic Blue/Navy)**
- Primary: `#1B3A5C` (deep navy — headers, primary buttons)
- Primary Light: `#3D6E9E` (hover states, links)
- Primary Accent: `#4A90D9` (progress bars, active states)

**Neutral Base**
- Background: `#FAFAF8` (warm off-white, reduces eye strain vs. pure white)
- Surface/Card: `#FFFFFF`
- Border: `#E0E0DC`
- Text Primary: `#1A1A1A`
- Text Secondary: `#5C5C5C`

**Semantic**
- Success: `#2E7D4F` (job complete)
- Warning: `#B8860B` (segment skipped / low confidence OCR)
- Error: `#C0392B` (job failed)
- Info: `#2C6E9E` (processing in progress)

Rationale: navy + warm neutral background reads as academic/institutional (aligned with NPTEL/IIT branding conventions) rather than a generic SaaS product, while maintaining strong contrast ratios for accessibility (WCAG AA minimum).

### 3. Typography
- **Headers:** `IBM Plex Sans` or `Source Sans Pro` — clean, technical, excellent readability, free/open-source (Google Fonts)
- **Body text:** `Inter` or `Source Sans Pro` — high legibility at small sizes
- **Monospace (for LaTeX/status logs):** `IBM Plex Mono` or `JetBrains Mono` — for displaying extracted LaTeX strings, job IDs, logs

Suggested scale:
- H1 (Page title): 28px, semi-bold
- H2 (Section headers): 20px, semi-bold
- Body: 16px, regular
- Caption/meta (timestamps, job IDs): 13px, regular, secondary text color

### 4. Layout Structure
- **Left sidebar:** App branding/title, brief description of the tool, navigation (Upload / Job History / About).
- **Main panel, top:** Upload widget (drag-and-drop video file) — large, clearly bordered, generous padding.
- **Main panel, processing state:** Stepper/progress component showing current pipeline stage (Extracting Audio → Detecting Silence → Detecting Scenes → Reading Board Content → Generating Descriptions → Synthesizing Audio → Assembling Video), each stage checked off as completed.
- **Main panel, complete state:** Video preview player + prominent "Download Accessible Video" button + summary stats (e.g., "12 descriptions generated, 4m 32s of audio added").

### 5. Accessibility Considerations (important given the project's purpose)
- Minimum 4.5:1 contrast ratio for all text (WCAG AA).
- All interactive elements (buttons, upload zone) must have visible focus states for keyboard navigation.
- Status updates during processing should be announced via `st.status`/`st.toast` in a way compatible with screen readers, not just visual color changes (pair color with icons/text labels — never color alone to indicate success/error).
- Avoid dense multi-column layouts; keep a single clear reading order top-to-bottom.

### 6. Tone
Interface copy should be plain, direct, and reassuring — e.g., "Reading the board content..." rather than jargon like "Running Pix2Text OCR inference." The target end-user of the *output* is visually impaired; the target user of the *dashboard* (uploading videos) is likely an instructor or accessibility staff member who needs confidence the tool is working correctly, not technical detail.
