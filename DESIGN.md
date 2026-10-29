# DESIGN.md — ระบบการออกแบบ Editorial Clinical Data Study Sheet

## 1. แนวคิดการออกแบบ (Aesthetic Direction)
- **Persona**: **"Editorial Clinical Informatics Study Sheet"** — ผสมผสานความน่าเชื่อถือของระบบสารสนเทศทางการแพทย์และคลังข้อมูลสุขภาพ (Health Data Systems) เข้ากับความสบายตาของสมุดสรุปเนื้อหาวิชาการระดับบรรณาธิการ
- **Tone & Mood**: สะอาดตา คมชัด มีลำดับขั้นของข้อมูล (Information Hierarchy) ที่ชัดเจน ช่วยลดความเมื่อยล้าของสายตาในการอ่านสรุปเนื้อหาจำนวนมากและฝึกทำข้อสอบปรนัยต่อเนื่อง

## 2. ระบบสี (Color Tokens — Warm Paper & Clinical Teal/Indigo)
- **Light Mode (Warm Alabaster Paper)**:
  - `--bg`: `#f7f6f2` (สีกระดาษถนอมสายตา)
  - `--bg-elevated`: `#ffffff` (พื้นหลังการ์ดเนื้อหาและข้อสอบ)
  - `--bg-subtle`: `#eeece4` (พื้นหลังส่วนหัวตารางและแถบเมนูย่อย)
  - `--text`: `#182026` (สีหมึกเข้มคมชัด)
  - `--text-secondary`: `#45505b` (สีข้อความอธิบายเสริม)
  - `--primary`: `#0d6e6e` (Clinical Deep Teal — สีหลักประจำวิชา Health Data Systems)
  - `--primary-soft`: `#e6f4f4`
  - `--accent`: `#b45309` (Warm Amber สำหรับเน้นจุดสำคัญและดาว `⭐⭐⭐`)
- **Dark Mode (Midnight Clinical Slate)**:
  - `--bg`: `#0f1419`
  - `--bg-elevated`: `#182029`
  - `--bg-subtle`: `#212c38`
  - `--text`: `#e6edf3`
  - `--primary`: `#2dd4bf`

## 3. ระบบตัวอักษรและการจัดหน้า (Typography & Layout)
- **Font Stack**: `'Sarabun'`, `'IBM Plex Sans Thai'`, `'Noto Sans Thai'`, system-ui, sans-serif สำหรับเนื้อหาภาษาไทย และ `'JetBrains Mono'`, monospace สำหรับรหัสมาตรฐาน (`ICD-10`, `SNOMED CT`, `LOINC`, `TMTID`, `FHIR JSON`)
- **Reading Width**: จำกัดความกว้างคอลัมน์เนื้อหาไว้ที่ `940px` เพื่อให้ความยาวบรรทัดเหมาะสมที่สุดสำหรับการอ่านเร็วและจำแม่น
- **Study-First Layout**: แสดงเนื้อหาสรุป (`#summary-section`) อยู่ด้านบนของข้อสอบจำลอง (`#quiz-section`) เสมอในโหมดเริ่มต้นของแต่ละบท พร้อมแถบนำทางด่วน (Quick Jump Bar) และสารบัญย่อย
