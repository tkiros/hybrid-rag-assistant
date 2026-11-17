"""Generate the synthetic corpus and the eval set:  python -m data.generate

Writes two PDFs to data/pdfs/ (git-ignored) and 120 questions to evals/sets/{dev,test}.jsonl.
A fixed seed and a fixed PDF creation date make every run byte-identical.

Every planted fact has a "needle": a string that occurs exactly once in the corpus. The eval
looks each needle up after ingestion to find the gold chunk id, so labels survive re-chunking.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF, XPos, YPos

from data import content as C

SEED = 20261117
ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
SETS_DIR = ROOT / "evals" / "sets"
MANUAL, HANDBOOK = "rs-service-manual", "returns-warranty-handbook"
PDF_DATE = datetime(2026, 1, 1, tzinfo=UTC)  # fixed, so the PDF bytes never change
DEV_COUNTS = {"exact_id": 13, "paraphrased": 13, "multi_chunk": 7, "unanswerable": 7}
TYPE_COUNTS = {"exact_id": 40, "paraphrased": 40, "multi_chunk": 20, "unanswerable": 20}


@dataclass
class Part:
    pn: str
    heading: str  # catalog heading, e.g. "GASKET, INLET VALVE"
    label: str  # how procedures refer to it, e.g. "gasket for the inlet valve"
    description: str
    category: str
    price: str
    wclass: str
    interval: int

    @property
    def needle(self) -> str:
        return f"Part No. {self.pn}"


@dataclass
class Component:
    category: str
    name: str
    alt_name: str
    fastener: str
    role: str
    torque: str
    part: Part

    @property
    def needle(self) -> str:
        return C.TORQUE_SENTENCE.format(fastener=self.fastener, c=self.name, torque=self.torque)


@dataclass
class ErrorCode:
    code: str
    title: str
    text: str
    part: Part

    @property
    def needle(self) -> str:
        return f"Corrective action for {self.code}:"


@dataclass
class PolicyFact:
    clause: str  # e.g. "§4.2.1"
    sentence: str  # the planted sentence; also the needle
    kind: str
    value: int
    paraphrase: str


class Outline:
    """Collects a document's blocks and numbers its headings (6, 6.2, 6.2.3 ...)."""

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.blocks: list[tuple[str, ...]] = []
        self.counters: list[int] = []

    def heading(self, level: int, title: str) -> str:
        self.counters = self.counters[:level] + [0] * (level - len(self.counters))
        self.counters[level - 1] += 1
        number = self.prefix + ".".join(str(n) for n in self.counters)
        self.blocks.append(("heading", number, title))
        return number

    def text(self, paragraph: str) -> None:
        self.blocks.append(("text", paragraph))


# ---------------------------------------------------------------- corpus facts

def new_part_number(rng: random.Random, prefix: str, used: set[str]) -> str:
    while True:
        pn = f"{prefix}-{rng.randint(1000, 9999)}-{rng.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}"
        if pn not in used:
            used.add(pn)
            return pn


def make_part(rng, used, category, heading, label, description, price_range) -> Part:
    return Part(
        pn=new_part_number(rng, C.CATEGORIES[category][1], used),
        heading=heading,
        label=label,
        description=description,
        category=category,
        price=f"{rng.uniform(*price_range):.2f}",
        wclass=rng.choice(["W1", "W2", "W3", "W4", "W5"]),
        interval=rng.randrange(1000, 20001, 250),
    )


def make_components(rng: random.Random) -> tuple[list[Component], list[Part]]:
    """One main part per component plus six extra catalog parts (gaskets, kits ...)."""
    used: set[str] = set()
    torques = rng.sample([x / 2 for x in range(16, 400)], len(C.COMPONENTS))
    components, parts = [], []
    for (category, name, alt, fastener, role), torque in zip(C.COMPONENTS, torques, strict=True):
        main = make_part(rng, used, category, name.upper(), name, f"{name}, which {role}",
                         (120, 4800))
        parts.append(main)
        components.append(Component(category, name, alt, fastener, role, f"{torque:g}", main))
        kinds = C.EXTRA_PART_KINDS.get(category, C.EXTRA_PART_KINDS["default"])
        for kind in kinds:
            label = f"{kind.lower()} for the {name}"
            parts.append(make_part(rng, used, category, f"{kind}, {name.upper()}", label, label,
                                   (6, 240)))
    return components, parts


def make_errors(rng: random.Random, components: list[Component], parts: list[Part],
                count: int = 110) -> list[ErrorCode]:
    categories = list(C.CATEGORIES)
    errors, seen_titles, seen_codes = [], set(), set()
    while len(errors) < count:
        comp = rng.choice(components)
        suffix, trigger = rng.choice(C.SYMPTOMS)
        title = f"{comp.name.upper()} {suffix}"
        code = f"E-{categories.index(comp.category) + 1}{rng.randint(100, 999)}"
        if title in seen_titles or code in seen_codes:
            continue
        seen_titles.add(title)
        seen_codes.add(code)
        part = rng.choice([p for p in parts if comp.name in p.label])
        text = (
            f"The controller shows {code} when "
            f"{trigger.format(c=comp.name, n=rng.randint(2, 9) * 5)}. "
            f"Probable cause: {rng.choice(C.CAUSES)}. "
            f"Corrective action for {code}: replace the {part.label} (part {part.pn}). "
            f"Reset: {rng.choice(C.RESETS)}."
        )
        errors.append(ErrorCode(code, title, text, part))
    return sorted(errors, key=lambda e: e.code)


# ---------------------------------------------------------------- manual

def steps(rng: random.Random, pool: list[str], k: int, comp: Component) -> list[str]:
    """k sentences from pool, in pool order, with the component's details filled in."""
    chosen = sorted(rng.sample(range(len(pool)), k))
    fill = {"c": comp.name, "panel": rng.choice(C.PANELS), "conn": rng.choice(C.CONNECTIONS),
            "n": rng.choice([10, 15, 20, 30]), "mm": rng.choice(["0.2", "0.3", "0.5", "0.8"])}
    return [pool[i].format(**fill) for i in chosen]


def numbered(lines: list[str]) -> str:
    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1))


def component_section(out: Outline, rng: random.Random, comp: Component) -> None:
    out.heading(2, comp.name.upper())
    out.heading(3, "DESCRIPTION")
    extra = " ".join(steps(rng, C.DESCRIPTION_EXTRA, 2, comp))
    out.text(f"The {comp.name} {comp.role}. {extra} "
             f"The replacement {comp.name} is part {comp.part.pn}.")
    out.heading(3, "REMOVAL")
    out.text(numbered(steps(rng, C.REMOVAL_STEPS, 6, comp)))
    out.heading(3, "INSTALLATION")
    install = steps(rng, C.INSTALL_STEPS, 5, comp)
    install.insert(4, comp.needle)  # the planted torque value
    out.text(numbered(install))
    out.heading(3, "INSPECTION")
    out.text(" ".join(steps(rng, C.INSPECTION_STEPS, 4, comp)))
    out.heading(3, "TROUBLESHOOTING")
    out.text(" ".join(steps(rng, C.TROUBLESHOOTING_STEPS, 4, comp)))


def catalog_entry(part: Part, models: list[str]) -> str:
    return (f"{part.needle}\nDescription: {part.description}.\n"
            f"Fits models: {', '.join(models)}.\nUnit price: ${part.price}. "
            f"Warranty class: {part.wclass}. "
            f"Replacement interval: {part.interval} operating hours.")


def manual_blocks(rng, components, parts, errors) -> list[tuple[str, ...]]:
    out = Outline()
    for chapter, sections in C.MANUAL_INTRO.items():
        out.heading(1, chapter)
        for title, paragraphs in sections:
            out.heading(2, title)
            for p in paragraphs:
                out.text(p)
        if chapter == "INTRODUCTION":
            out.heading(2, "MODEL SPECIFICATIONS")
            for i, model in enumerate(C.MODELS):
                out.text(C.SPEC_LINE.format(
                    model=model, bar=rng.choice(["7.5", "8.5", "10", "13"]),
                    fad=f"{2.5 + i * 3 + rng.random():.1f}", kw=[30, 45, 55, 75, 90][i],
                    oil=18 + i * 6, kg=820 + i * 260 + rng.randint(0, 60)))

    out.heading(1, "CONTROLLER AND ERROR CODES")
    out.heading(2, "READING THE DISPLAY")
    out.text("Alarms are shown as a code starting with E- followed by four digits. The first "
             "digit identifies the system: 1 air end, 2 lubrication, 3 cooling, 4 drive, "
             "5 filtration, 6 electrical and controls, 7 pressure system.")
    out.heading(2, "ERROR CODE LIST")
    for err in errors:
        out.heading(3, f"{err.code} {err.title}")
        out.text(err.text)

    for category, (chapter, _) in C.CATEGORIES.items():
        out.heading(1, chapter)
        for comp in components:
            if comp.category == category:
                component_section(out, rng, comp)

    out.heading(1, "MAINTENANCE SCHEDULE")
    for title, paragraphs in C.MAINTENANCE_SCHEDULE:
        out.heading(2, title)
        for p in paragraphs:
            out.text(p)

    out.heading(1, "PARTS CATALOG")
    for category, (chapter, _) in C.CATEGORIES.items():
        out.heading(2, f"{chapter} PARTS")
        for part in parts:
            if part.category == category:
                out.heading(3, part.heading)
                models = [m for m in C.MODELS if rng.random() < 0.6] or [C.MODELS[2]]
                out.text(catalog_entry(part, models))
    return out.blocks


# ---------------------------------------------------------------- handbook

def handbook_blocks(rng: random.Random) -> tuple[list, list[PolicyFact], dict[str, int]]:
    """Return the handbook's blocks, its planted facts and the warranty months per class."""
    used: set[int] = set()

    def draw(kind: str) -> int:
        lo, hi = C.VALUE_RANGES[kind]
        while (v := rng.randint(lo, hi)) in used:
            pass
        used.add(v)
        return v

    class_months = {f"W{i}": draw("months") for i in range(1, 6)}
    out, facts = Outline(prefix="§"), []
    for chapter, sections in C.POLICY_OUTLINE:
        out.heading(1, chapter)
        for section in sections:
            out.heading(2, section)
            for fact in [f for f in C.POLICY_FACTS if f[:2] == (chapter, section)]:
                _, _, title, template, kind, paraphrase = fact
                value = draw(kind)
                sentence = template.format(v=value)
                clause = out.heading(3, title)
                filler = " ".join(rng.sample(C.POLICY_FILLER, rng.randint(1, 2)))
                out.text(f"{sentence} {filler}")
                facts.append(PolicyFact(clause, sentence, kind, value, paraphrase))
            if section == "WARRANTY CLASSES":
                for wc, months in class_months.items():
                    out.heading(3, f"CLASS {wc} COMPONENTS")
                    out.text(C.WARRANTY_CLASS_SENTENCE.format(wc=wc, v=months) + " The class "
                             "of each part is printed in the parts catalog of the service manual.")
            for title, text in C.POLICY_STATIC.get((chapter, section), []):
                out.heading(3, title)
                out.text(text)
    return out.blocks, facts, class_months


# ---------------------------------------------------------------- questions

def question(type_, text, answer=None, must_contain=None, needles=()) -> dict:
    return {"type": type_, "question": text, "answer": answer,
            "must_contain": must_contain, "gold_needles": list(needles)}


PART_ATTRIBUTES = [  # (question about part X, answer as printed, token the answer must contain)
    ("What is the unit price of part {pn}?", lambda p: f"${p.price}", lambda p: p.price),
    ("Which warranty class does part {pn} belong to?", lambda p: p.wclass, lambda p: p.wclass),
    ("After how many operating hours should part {pn} be replaced?",
     lambda p: f"{p.interval} operating hours", lambda p: str(p.interval)),
]
CLAUSE_QUESTIONS = {
    "days": "How many days does {clause} specify?",
    "hours": "How many hours does {clause} specify?",
    "op_hours": "How many operating hours does {clause} specify?",
    "months": "How many months does {clause} specify?",
    "pct": "What percentage does {clause} specify?",
    "amount": "What dollar amount does {clause} specify?",
    "km": "What distance in km does {clause} specify?",
}
TORQUE_QUESTIONS = [
    "How tight should the fixings be when I put the {alt} back in?",
    "What torque goes on the fasteners after reinstalling the {alt}?",
    "When refitting the {alt}, what tightening torque is required?",
    "I'm reassembling the {alt}. How many newton-metres should I use?",
]


def value_text(fact: PolicyFact) -> str:
    if fact.kind == "amount":
        return f"${fact.value}"
    if fact.kind == "pct":
        return f"{fact.value}%"
    return f"{fact.value} {C.UNIT_WORDS[fact.kind]}"


def part_question(type_, template, part, extra_needles=()) -> dict:
    ask, answer, token = PART_ATTRIBUTES[template]
    return question(type_, ask.format(pn=part.pn), answer(part), token(part),
                    [*extra_needles, part.needle])


def make_questions(rng, components, parts, errors, facts, class_months,
                   corpus_text) -> list[dict]:
    qs: list[dict] = []
    picked_parts = rng.sample(parts, 24)
    picked_errors = rng.sample(errors, 23)
    picked_facts = rng.sample(facts, 33)
    picked_components = rng.sample(components, 20)

    # exact identifier: 14 part numbers, 13 error codes, 13 clause numbers
    for i, part in enumerate(picked_parts[:14]):
        qs.append(part_question("exact_id", i % 3, part))
    for err in picked_errors[:13]:
        qs.append(question("exact_id", f"Which part number does error code {err.code} tell you "
                           "to replace?", err.part.pn, err.part.pn, [err.needle]))
    for fact in picked_facts[:13]:
        qs.append(question("exact_id", CLAUSE_QUESTIONS[fact.kind].format(clause=fact.clause),
                           value_text(fact), str(fact.value), [fact.sentence]))

    # paraphrased: 20 torque values (other names for the part), 20 policy rules (plain words)
    for i, comp in enumerate(picked_components):
        ask = TORQUE_QUESTIONS[i % len(TORQUE_QUESTIONS)].format(alt=comp.alt_name)
        qs.append(question("paraphrased", ask, f"{comp.torque} Nm", comp.torque, [comp.needle]))
    for fact in picked_facts[13:]:
        qs.append(question("paraphrased", fact.paraphrase, value_text(fact), str(fact.value),
                           [fact.sentence]))

    # multi-chunk: error code -> part -> catalog value, and part -> class -> warranty months
    for i, err in enumerate(picked_errors[13:]):
        q = part_question("multi_chunk", i % 3, err.part, [err.needle])
        q["question"] = (f"Error code {err.code} calls for a replacement part. "
                         + q["question"].replace(f"part {err.part.pn}", "that part"))
        qs.append(q)
    for part in picked_parts[14:]:
        months = class_months[part.wclass]
        sentence = C.WARRANTY_CLASS_SENTENCE.format(wc=part.wclass, v=months)
        qs.append(question("multi_chunk", f"How many months of warranty cover does part "
                           f"{part.pn} get?", f"{months} months", str(months),
                           [part.needle, sentence]))

    # unanswerable: identifiers that don't exist, and topics the documents never cover
    fakes: list[str] = []
    used_pns = {p.pn for p in parts}
    for i in range(7):
        fake = new_part_number(rng, rng.choice(list(C.CATEGORIES.values()))[1], used_pns)
        fakes.append(fake)
        qs.append(question("unanswerable", PART_ATTRIBUTES[i % 3][0].format(pn=fake)))
    while len(fakes) < 11:
        code = f"E-{rng.randint(8, 9)}{rng.randint(100, 999)}"  # systems 8 and 9 don't exist
        if code not in fakes:
            fakes.append(code)
            qs.append(question("unanswerable", f"Which part number does error code {code} "
                               "tell you to replace?"))
    while len(fakes) < 14:
        number = f"{rng.randint(1, 9)}.{rng.randint(4, 6)}.{rng.randint(1, 3)}"
        if number not in fakes and not occurs(number, corpus_text):
            fakes.append(number)
            qs.append(question("unanswerable", f"How many days does §{number} specify?"))
    for text, _ in C.OFF_CORPUS:
        qs.append(question("unanswerable", text))

    check_unanswerable(fakes, corpus_text)
    return qs


def occurs(token: str, text: str) -> bool:
    """True if token appears as a whole identifier ("2.4.2" does not occur in "12.4.2")."""
    return re.search(rf"(?<![\w.]){re.escape(token)}(?![\w]|\.\d)", text) is not None


def check_unanswerable(fakes: list[str], corpus_text: str) -> None:
    """Fail loudly if an 'unanswerable' question is in fact covered by the corpus."""
    for fake in fakes:
        assert not occurs(fake, corpus_text), f"made-up identifier {fake} exists in the corpus"
    lower = corpus_text.lower()
    for _, absent in C.OFF_CORPUS:
        for word in absent:
            assert word not in lower, f"off-corpus keyword {word!r} appears in the corpus"


def split(rng: random.Random, qs: list[dict]) -> tuple[list[dict], list[dict]]:
    """Give each question an id, then put DEV_COUNTS of each type in dev and the rest in test."""
    dev, test = [], []
    for type_, total in TYPE_COUNTS.items():
        of_type = [q for q in qs if q["type"] == type_]
        assert len(of_type) == total, (type_, len(of_type))
        for i, q in enumerate(of_type, 1):
            q["id"] = f"{type_}-{i:02d}"
        rng.shuffle(of_type)
        dev += of_type[:DEV_COUNTS[type_]]
        test += of_type[DEV_COUNTS[type_]:]
    return sorted(dev, key=lambda q: q["id"]), sorted(test, key=lambda q: q["id"])


# ---------------------------------------------------------------- rendering

class Pdf(FPDF):
    def __init__(self, footer_text: str):
        super().__init__(format="A4")
        self.footer_text = footer_text

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", size=8)
        self.cell(0, 10, f"{self.footer_text} | Page {self.page_no()}", align="C")


def render(blocks, title: str, subtitle: str, footer: str, path: Path) -> int:
    """Write blocks to a PDF; returns the page count. Level-1 headings start a new page."""
    pdf = Pdf(footer)
    pdf.set_creation_date(PDF_DATE)
    pdf.set_title(footer)
    pdf.set_auto_page_break(True, margin=22)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.ln(60)
    pdf.multi_cell(0, 12, title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, subtitle, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    for block in blocks:
        if block[0] == "heading":
            _, number, heading = block
            level = number.count(".") + 1
            if level == 1 or pdf.will_page_break(30):
                pdf.add_page()
            pdf.set_font("Helvetica", "B", {1: 15, 2: 12.5, 3: 11}[level])
            pdf.ln(2)
            pdf.cell(0, 8, f"{number} {heading}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_font("Helvetica", size=11)
            with pdf.unbreakable() as doc:  # a paragraph never splits across pages
                doc.multi_cell(0, 6, block[1], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)
    pdf.output(str(path))
    return pdf.pages_count


def block_text(blocks) -> str:
    return " ".join(" ".join(b[1:]) for b in blocks)


def build(seed: int = SEED) -> tuple[dict, list[dict], list[dict]]:
    """Return ({doc_id: blocks}, dev questions, test questions). Pure: writes nothing."""
    rng = random.Random(seed)
    components, parts = make_components(rng)
    errors = make_errors(rng, components, parts)
    docs = {MANUAL: manual_blocks(rng, components, parts, errors)}
    docs[HANDBOOK], facts, class_months = handbook_blocks(rng)

    corpus = " ".join(" ".join(block_text(b).split()) for b in docs.values())
    qs = make_questions(rng, components, parts, errors, facts, class_months, corpus)
    for q in qs:
        for needle in q["gold_needles"]:
            assert corpus.count(needle) == 1, f"needle not unique: {needle!r}"
    dev, test = split(rng, qs)
    return docs, dev, test


def write_jsonl(path: Path, rows: list[dict]) -> None:
    keys = ["id", "type", "question", "answer", "must_contain", "gold_needles"]
    path.write_text("".join(json.dumps({k: r[k] for k in keys}) + "\n" for r in rows))


def main() -> None:
    docs, dev, test = build()
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    titles = {  # title, subtitle, footer
        MANUAL: ("HALVARD RS-SERIES PARTS AND SERVICE MANUAL",
                 "Rotary screw compressors RS-30 to RS-90", "Halvard RS-Series Service Manual"),
        HANDBOOK: ("HALVARD RETURNS AND WARRANTY HANDBOOK",
                   "Orders, returns, warranty claims and refunds", "Halvard Warranty Handbook"),
    }
    note = "\nSynthetic document for a portfolio project. Halvard Machine Works is fictional."
    for doc_id, blocks in docs.items():
        title, subtitle, footer = titles[doc_id]
        pages = render(blocks, title, subtitle + note, footer, PDF_DIR / f"{doc_id}.pdf")
        print(f"data/pdfs/{doc_id}.pdf: {pages} pages")
    SETS_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(SETS_DIR / "dev.jsonl", dev)
    write_jsonl(SETS_DIR / "test.jsonl", test)
    print(f"evals/sets: {len(dev)} dev + {len(test)} test questions")


if __name__ == "__main__":
    main()
