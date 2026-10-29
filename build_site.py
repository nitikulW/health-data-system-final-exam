"""Build the offline study & mock-exam web app for 553116-168 Health Data Systems."""
from pathlib import Path
import re, json, html, hashlib, shutil

ROOT = Path(__file__).resolve().parent

META = {
    '09': {
        'shortTitle': 'เวชระเบียนอิเล็กทรอนิกส์ (EMR/EHR) และแฟ้มสุขภาพส่วนบุคคล (PHR)',
        'instructor': 'ผศ.ดร.สรวง รุ่งประกายพรรณ',
        'partLabel': 'ตอนที่ 3: EMR, EHR และ PHR (10 คะแนน)',
        'sourceDefault': 'สไลด์และวิดีโอบรรยาย บทที่ 9 (EMR, EHR, PHR, Data Quality & PDPA)'
    },
    '10': {
        'shortTitle': 'ระบบข้อมูลความปลอดภัยของผลิตภัณฑ์สุขภาพ (Pharmacovigilance)',
        'instructor': 'ภญ.พัทรียา โภคะกุล',
        'partLabel': 'ตอนที่ 1: Pharmacovigilance Data System (10 คะแนน)',
        'sourceDefault': 'เนื้อหาบทที่ 10 (HPVC, AE/ADR/SAE, Naranjo, WHO-UMC, Signal Detection, ICH E2B/MedDRA/IDMP)'
    },
    '11': {
        'shortTitle': 'ระบบบัญชีข้อมูลยาและรหัสยามาตรฐานไทย (TMT)',
        'instructor': 'ภก.กิตติ อัคควัฒนกุล',
        'partLabel': 'เชื่อมโยงตอนที่ 1 (PV) และ ตอนที่ 2 (Standards & TMT)',
        'sourceDefault': 'วิดีโอบรรยายและใบงานการบ้าน บทที่ 11 (TMT 7-8 ระดับ, Check Digit/CRC-32/SHA-1, TBox/ABox, Docker)'
    },
    '12': {
        'shortTitle': 'มาตรฐานข้อมูลและการทำงานร่วมกัน (Interoperability & Standards)',
        'instructor': 'รศ.ดร.ภก.วีรยุทธ์ เลิศนที',
        'partLabel': 'ตอนที่ 2: มาตรฐานข้อมูลและการทำงานร่วมกัน (10 คะแนน)',
        'sourceDefault': 'สไลด์บทที่ 12 หน้า 1–40 (Data Standards, 4 Levels Interoperability, FHIR, SNOMED CT, ICD-10, LOINC, DICOM, IDMP, 43 แฟ้ม/HDC, TMT/TMLT)'
    },
}

def format_math(s: str) -> str:
    s = re.sub(r'\$\$(.+?)\$\$', lambda m: f'<strong>{m.group(1)}</strong>', s)
    s = re.sub(r'\\text\{([^}]*)\}', r'\1', s)
    s = s.replace(r'\longrightarrow', '→').replace(r'\rightarrow', '→')
    s = s.replace(r'\ge', '≥').replace(r'\le', '≤')
    s = s.replace('$', '')
    return s

def inline(s: str) -> str:
    s = html.escape(s)
    s = format_math(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    return s

def markdown(s: str) -> str:
    out, lines, i = [], s.splitlines(), 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        if not line:
            i += 1
            continue
        if line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append('<pre class="codeblock">' + '\n'.join(code_lines) + '</pre>')
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*', c) for c in cells):
                    tag = 'th' if not rows else 'td'
                    rows.append('<tr>' + ''.join(f'<{tag}>{inline(c.strip())}</{tag}>' for c in cells) + '</tr>')
                i += 1
            out.append('<div class="table-wrap"><table>' + ''.join(rows) + '</table></div>')
            continue
        if line.startswith('>'):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                cleaned = lines[i].strip().lstrip('>').strip()
                i += 1
                if re.match(r'^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]$', cleaned):
                    continue
                bq_lines.append(inline(cleaned))
            out.append('<blockquote>' + '<br>'.join(bq_lines) + '</blockquote>')
            continue
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            out.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>')
        elif re.fullmatch(r'[-*_]{3,}', line):
            out.append('<hr>')
        elif re.match(r'^[-*]\s+', line):
            out.append('<p class="bullet">• ' + inline(line[2:]) + '</p>')
        elif re.match(r'^\d+[.)]\s+', line):
            out.append('<p class="bullet">' + inline(line) + '</p>')
        else:
            out.append('<p>' + inline(line) + '</p>')
        i += 1
    return '\n'.join(out)

def clean_plain(s: str) -> str:
    s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', s)
    return s.strip()

chapters = []
manifest = []

for f in sorted(ROOT.glob('บท*.md')):
    text = f.read_text(encoding='utf-8-sig')
    chap_id = re.search(r'บท(\d+)', f.name)[1]
    meta = META[chap_id]

    summary_part, exam_part = re.split(r'^## แนวข้อสอบจำลอง.*$', text, maxsplit=1, flags=re.M)
    summary_part = summary_part.strip()

    if '## ส่วนที่ 1' in summary_part:
        _, sec1_body = summary_part.split('## ส่วนที่ 1', 1)
        sec1_body = '## ส่วนที่ 1' + sec1_body
    else:
        sec1_body = summary_part

    q_headers = list(re.finditer(r'^### ข้อที่\s+(\d+)\s*(⭐+)?\s*$', exam_part, flags=re.M))
    qs = []
    for ix, m in enumerate(q_headers):
        qnum = int(m.group(1))
        stars = len(m.group(2)) if m.group(2) else 2
        block = exam_part[m.end():q_headers[ix + 1].start() if ix + 1 < len(q_headers) else len(exam_part)].strip()

        det_split = re.split(r'<details>\s*<summary>.*?</summary>', block, maxsplit=1, flags=re.S)
        assert len(det_split) == 2, f'Missing <details> in {f.name} Q{qnum}'
        q_and_opts = det_split[0].strip()
        exp_raw = det_split[1].replace('</details>', '').strip()

        opt_parts = re.split(r'(?:^|\n)-\s*([กขคง])\.\s*', q_and_opts)
        assert len(opt_parts) == 9, (f.name, qnum, len(opt_parts), opt_parts)
        assert opt_parts[1::2] == list('กขคง'), (f.name, qnum)

        q_text = clean_plain(opt_parts[0])
        choices = [clean_plain(c) for c in opt_parts[2::2]]

        ans_match = re.search(r'\*\*คำตอบที่ถูกต้อง:\s*([กขคง])\.\*\*', exp_raw)
        assert ans_match, f'Missing answer key in {f.name} Q{qnum}'
        a_idx = 'กขคง'.index(ans_match.group(1))

        exp_lines = []
        for eline in exp_raw.splitlines():
            eline = eline.strip()
            if not eline or eline.startswith('**คำตอบที่ถูกต้อง:'):
                continue
            eline = re.sub(r'^-\s*', '• ', eline)
            exp_lines.append(clean_plain(eline))
        exp_text = ' | '.join(exp_lines)

        qs.append(dict(
            q=q_text,
            c=choices,
            a=a_idx,
            e=exp_text,
            stars=stars,
            source=meta['sourceDefault'],
            topicId=chap_id,
            topicTitle=f'บทที่ {int(chap_id)}: {meta["shortTitle"]}',
            partLabel=meta['partLabel']
        ))

    assert len(qs) == 30, f'{f.name} has {len(qs)} questions instead of 30'
    title = summary_part.splitlines()[0].lstrip('# ').strip()
    chapters.append(dict(
        id=chap_id,
        title=title,
        shortTitle=meta['shortTitle'],
        instructor=meta['instructor'],
        partLabel=meta['partLabel'],
        summary=markdown(summary_part),
        checklistHtml=markdown(sec1_body),
        bodyHtml=markdown(sec1_body),
        questions=qs,
        filename=f.name
    ))
    manifest.append(dict(
        file=f.name,
        sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
        total=len(qs),
        stars_3=sum(1 for q in qs if q['stars'] == 3),
        stars_2=sum(1 for q in qs if q['stars'] == 2),
        stars_1=sum(1 for q in qs if q['stars'] == 1),
    ))

# Build the 30-question Full Final Exam Simulation matching ใบปะหน้า.jpg (30 points, 3 Parts)
# ตอนที่ 1: Pharmacovigilance Data System (10 คะแนน) -> 8 ข้อจากบทที่ 10 + 2 ข้อจากบทที่ 11 (การผูกแพ้ยาระดับ SUBS/VTM & ISO IDMP)
# ตอนที่ 2: มาตรฐานข้อมูลและการทำงานร่วมกัน (10 คะแนน) -> 6 ข้อจากบทที่ 12 + 4 ข้อจากบทที่ 11 (TMT Hierarchy, TBox/ABox, Check Digit/SHA-1)
# ตอนที่ 3: EMR, EHR และ PHR (10 คะแนน) -> 10 ข้อจากบทที่ 9 (EMR/EHR/PHR, Meaningful Use, Health Link, หมอพร้อม, Data Quality 6 มิติ, Penicillin Case, PDPA, Data Security)

def pick_curated(chap_id, indices, part_label):
    ch = next(c for c in chapters if c['id'] == chap_id)
    out = []
    for idx in indices:
        q_copy = dict(ch['questions'][idx])
        q_copy['partLabel'] = part_label
        out.append(q_copy)
    return out

exam30_questions = (
    pick_curated('10', [0, 3, 5, 7, 9, 11, 16, 20], 'ตอนที่ 1: Pharmacovigilance Data System (10 คะแนน)') +
    pick_curated('11', [1, 24], 'ตอนที่ 1: Pharmacovigilance Data System (10 คะแนน)') +
    pick_curated('12', [1, 3, 4, 7, 9, 22], 'ตอนที่ 2: มาตรฐานข้อมูลและการทำงานร่วมกัน (10 คะแนน)') +
    pick_curated('11', [2, 6, 10, 11], 'ตอนที่ 2: มาตรฐานข้อมูลและการทำงานร่วมกัน (10 คะแนน)') +
    pick_curated('09', [0, 1, 4, 6, 8, 10, 12, 17, 19, 22], 'ตอนที่ 3: EMR, EHR และ PHR (10 คะแนน)')
)
assert len(exam30_questions) == 30, len(exam30_questions)

exam30_summary_md = """# จำลองสอบปลายภาคจริง 30 ข้อ 30 คะแนน (ตามโครงสร้างใบปะหน้าข้อสอบ `ใบปะหน้า.jpg`)

> **รหัสวิชา:** `553116-168 ระบบข้อมูลสุขภาพ (HEALTH DATA SYSTEMS)` — วท.บ. (สุขภาพดิจิทัล) ชั้นปีที่ 2  
> **วันและเวลาสอบจริง:** วันที่ 31 ตุลาคม 2569 เวลา 09.00 – 10.00 น. (เวลาสอบ 1 ชั่วโมง / 60 นาที)  
> **รูปแบบข้อสอบ:** ข้อสอบปรนัย 4 ตัวเลือก จำนวน 7 หน้า **คะแนนเต็ม 30 คะแนน แบ่งออกเป็น 3 ตอน ตอนละ 10 คะแนน**

---

## โครงสร้างข้อสอบปลายภาคทั้ง 3 ตอน และโพยสรุปจุดเน้นก่อนเข้าห้องสอบ ⭐⭐⭐

| ตอนที่ | หัวข้อตามใบปะหน้าข้อสอบ | คะแนน | บทเรียนที่เกี่ยวข้อง | ประเด็นเก็งข้อสอบที่ต้องจำให้แม่น (⭐⭐⭐) |
| :---: | :--- | :---: | :--- | :--- |
| **ตอนที่ 1** | **Pharmacovigilance Data System** | **10 คะแนน** (ข้อ 1–10) | **บทที่ 10** (ภญ.พัทรียา) + **บทที่ 11** (TMT) | - นิยาม PV 4 เสาหลัก (`Detection, Assessment, Understanding, Prevention`) และข้อจำกัด `5 Too's` ของ Clinical Trials<br>- ความแตกต่างของ **AE vs ADR vs ADE vs Medication Error (Near Miss)** และ **Type A (Augmented) vs Type B (Bizarre)**<br>- เกณฑ์ **Serious AE 6 ข้อ**, องค์ประกอบขั้นต่ำของรายงาน **ICSR 4 ข้อ (ICH E2B)**, ข้อจำกัดของระบบ **SRS (Under-reporting & คำนวณ Incidence Rate ไม่ได้)** vs **Active Surveillance (SMP)**<br>- การประเมิน **Naranjo (`>=9` Definite, `5-8` Probable, `1-4` Possible, `<=0` Doubtful)** และ **WHO-UMC**, การทำ **Signal Detection (PRR, ROR, IC/BCPNN)** ในฐานข้อมูล **HPVC / WHO VigiBase** และรหัส **MedDRA / ISO IDMP / TMT (`SUBS`/`VTM`)** |
| **ตอนที่ 2** | **มาตรฐานข้อมูลและการทำงานร่วมกัน (Standards & Interoperability)** | **10 คะแนน** (ข้อ 11–20) | **บทที่ 12** (รศ.ดร.ภก.วีรยุทธ์) + **บทที่ 11** (ภก.กิตติ) | - องค์ประกอบ 8 ข้อ และประเภทมาตรฐานข้อมูล 5 ประเภท (`Content, Syntactic, Semantic, Terminology, Security`)<br>- **4 ระดับของ Interoperability** (`Foundational -> Structural/Syntactic -> Semantic -> Organizational`) และเหตุผลว่าทำไม **"การมี API ไม่ได้หมายความว่ามี Semantic Interoperability"**<br>- ระบบนิเวศมาตรฐานสากล: **HL7 FHIR** (Resources: `Patient, Encounter, Condition, Observation, Medication`), **SNOMED CT** (`44054006` บันทึกคลินิก) vs **ICD-10** (`E11` จำแนกโรค/สถิติ/เบิกจ่าย), **LOINC** (`2345-7` Glucose, `718-7` Hb) + **UCUM** (`mg/dL`), **DICOM** (`Patient -> Study -> Series -> Image`, PACS/RIS), **ISO IDMP 5 มาตรฐาน** (`11615, 11616, 11238, 11239, 11240`)<br>- มาตรฐานไทยโดย **THIS**: โครงสร้าง **43 แฟ้ม** + คลังข้อมูล **HDC**, รหัสแล็บ **TMLT** (`GLU/FBS/BS -> TMLT00001 -> LOINC 2345-7`), และรหัสยา **TMT 8 ระดับ** (`SUBS -> VTM -> GP -> GPU -> GPP` และ `TP -> TPU -> TPP`), `TBox` vs `ABox`, `Check Digit / CRC-32 / SHA-1` |
| **ตอนที่ 3** | **EMR, EHR และ PHR** | **10 คะแนน** (ข้อ 21–30) | **บทที่ 9** (ผศ.ดร.สรวง) | - บทบาทเวชระเบียน 2 ด้าน (`Continuity of Care` & `Legal/Administrative Proof`), หน้าจอ **HOSxP (HN vs CID)**, **5 เสาหลัก Meaningful Use**, วิวัฒนาการ `Paperless -> Basic EMR -> Integrated EMR -> Meaningful Uses -> EMR + Big Data`<br>- ตารางเปรียบเทียบ **EMR (รพ.เดียว) vs EHR (เชื่อมข้าม รพ. ระยะยาว เช่น Health Link ของ BDI) vs PHR (ผู้ป่วยดูแลเอง + Wearables เช่น หมอพร้อม Super App)** และแผนภาพ `EMR (A,B,C) -> EHR <-> PHR`<br>- **Data Quality 6 มิติ** (`Accuracy, Completeness, Consistency, Timeliness, Validity, Uniqueness`) และกรณีศึกษาผู้ป่วยแพ้ยา **Penicillin (Anaphylaxis)** ข้ามโรงพยาบาล<br>- **Data Privacy 6 หลักการ**, **ข้อยกเว้น PDPA 4 กรณีในบริบทสุขภาพ** (ฉุกเฉินต่อชีวิต, การตรวจรักษาโดยวิชาชีพ, สาธารณสุข/ควบคุมโรค, วิจัยที่ทำ De-identification) และ **Data Security (CIA Triad, RBAC, Encryption, Audit Log, Backup)** |
"""

chapters.append(dict(
    id='exam30',
    title='จำลองสอบปลายภาคจริง 30 ข้อ (ตามใบปะหน้า 3 ตอน · 30 คะแนน)',
    shortTitle='ตอนที่ 1 (10) + ตอนที่ 2 (10) + ตอนที่ 3 (10)',
    instructor='ครบทั้ง 3 ตอนตามใบปะหน้า',
    partLabel='ครบทั้ง 3 ตอนตามใบปะหน้า (30 คะแนน)',
    summary=markdown(exam30_summary_md),
    checklistHtml=markdown(exam30_summary_md),
    bodyHtml='',
    questions=exam30_questions,
    filename='ใบปะหน้า.jpg'
))

template = (ROOT / 'template.html').read_text(encoding='utf-8')
payload = json.dumps(chapters, ensure_ascii=False).replace('</', '<\\/')
html_out = template.replace('/*__DATA__*/', payload)

(ROOT / 'index.html').write_text(html_out, encoding='utf-8')
(ROOT / 'build_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

how_to_open = """วิธีเปิดใช้งานเว็บสรุปเนื้อหาและจำลองข้อสอบปลายภาค (553116-168 ระบบข้อมูลสุขภาพ - HEALTH DATA SYSTEMS)
====================================================================================================

1. ดับเบิลคลิกเปิดไฟล์ "index.html" ในโฟลเดอร์นี้ด้วยเว็บเบราว์เซอร์ใดก็ได้ (เช่น Google Chrome, Microsoft Edge, Safari, Firefox)
   - ทำงานแบบออฟไลน์ 100% เปิดอ่านและทำข้อสอบได้ทันทีโดยไม่ต้องใช้อินเทอร์เน็ต
2. โครงสร้างการใช้งานภายในเว็บ (ออกแบบตามความต้องการ: แยกข้อสอบตามบท และวางเนื้อหาไว้อ่านด้านบนข้อสอบจำลอง):
   - แถบเมนูด้านซ้ายแยกตามบทเรียนครบทั้ง 4 บทเรียน (บทที่ 9, 10, 11, 12) และ "🎯 จำลองสอบปลายภาคจริง (30 ข้อ 30 คะแนน ตามใบปะหน้า)"
   - ในแต่ละบทเรียน: ด้านบนสุดของหน้าจะแสดง "เนื้อหาสรุปฉบับสมบูรณ์ประจำบท" เพื่อให้อ่านทบทวนก่อนสอบ และเมื่อเลื่อนลงมาด้านล่างจะพบ "แบบจำลองข้อสอบประจำบท (30 ข้อ)" ต่อเนื่องกันทันที
   - ภายในส่วนข้อสอบจำลอง ยังมีกล่องพับเก็บ "เปิดดูเนื้อหาสรุปประจำบทระหว่างทำข้อสอบ" เพื่อให้เปิดดูโพยเทียบขณะทำข้อสอบข้อท้ายๆ ได้สะดวก
   - มีป้ายดาว (⭐⭐⭐ ออกสอบเน้นย้ำ, ⭐⭐ มีโอกาสออกสูง, ⭐ เก็บตกครบเนื้อหา) และปุ่มกรองเฉพาะข้อสอบ ⭐⭐⭐
   - โหมดจำลองสอบปลายภาคจริง 30 ข้อ แบ่งเป็น 3 ตอนตรงตามใบปะหน้าข้อสอบจริง (ตอนที่ 1 Pharmacovigilance 10 คะแนน, ตอนที่ 2 Standards & Interoperability 10 คะแนน, ตอนที่ 3 EMR/EHR/PHR 10 คะแนน) พร้อมปุ่มสุ่มชุดข้อสอบใหม่จากคลัง 120 ข้อได้ไม่จำกัดครั้ง
"""
(ROOT / 'วิธีเปิดเว็บ.txt').write_text(how_to_open, encoding='utf-8')

# Mirror into subfolder สรุปและแนวข้อสอบ for consistency with sibling course folders
SUB = ROOT / 'สรุปและแนวข้อสอบ'
SUB.mkdir(exist_ok=True)
for fname in ['index.html', 'template.html', 'build_site.py', 'build_manifest.json', 'PRODUCT.md', 'DESIGN.md', 'วิธีเปิดเว็บ.txt']:
    shutil.copy2(ROOT / fname, SUB / fname)
for md_file in ROOT.glob('บท*.md'):
    shutil.copy2(md_file, SUB / md_file.name)

print(f'Successfully built {len(chapters)-1} chapters ({sum(len(c["questions"]) for c in chapters if c["id"]!="exam30")} questions) + 30-question Full Exam Blueprint mode!')
