import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def create_report():
    doc = Document()

    # Page setup - Margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Base Styles
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(12)
    style_normal.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    style_normal.paragraph_format.line_spacing = 1.5
    style_normal.paragraph_format.space_after = Pt(6)

    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(18)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(20)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x02, 0x84, 0xC7)
        return p

    def add_subtitle(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(24)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)
        return p

    def add_chapter_heading(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(12)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        return p

    def add_section_heading(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x02, 0x84, 0xC7)
        return p

    def add_body(text, bold_prefix=""):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)
        if bold_prefix:
            r_prefix = p.add_run(bold_prefix)
            r_prefix.font.bold = True
            r_prefix.font.name = 'Times New Roman'
        r_text = p.add_run(text)
        r_text.font.name = 'Times New Roman'
        return p

    def add_formula_box(eq_text, label_text):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, 'F1F5F9')
        
        cp = cell.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(6)
        
        r_eq = cp.add_run(eq_text)
        r_eq.font.name = 'Cambria Math'
        r_eq.font.size = Pt(12.5)
        r_eq.font.bold = True
        r_eq.font.color.rgb = RGBColor(0x03, 0x69, 0xA1)
        
        if label_text:
            cp_label = cell.add_paragraph()
            cp_label.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp_label.paragraph_format.space_after = Pt(6)
            r_lbl = cp_label.add_run(f"({label_text})")
            r_lbl.font.name = 'Times New Roman'
            r_lbl.font.size = Pt(10)
            r_lbl.font.italic = True
            r_lbl.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

        doc.add_paragraph() # Spacing

    # HEADER & TITLE
    add_title("RESCUEGRID: MULTI-REGION EMERGENCY RESPONSE & RELIEF PLATFORM FOR INDIA")
    add_subtitle("MATHEMATICAL MODELING & SIMULATION EQUATIONS SPECIFICATION")

    # ABSTRACT
    add_chapter_heading("ABSTRACT")
    add_body(
        "This document details the mathematical formulations, simulation equations, and computational derivations governing the four core operational models of the RescueGrid platform: (1) Emergency Priority Scoring Model, (2) Automated Resource Allocation Engine Model, (3) Operational Response Time & Performance Model, and (4) GDACS Spatial Hazard Relevance & Proximity Model. All equations are presented as text-formatted mathematical representations to support precise simulation, code verification, and academic documentation."
    )

    doc.add_page_break()

    # CHAPTER 4: MATHEMATICAL MODELING & SIMULATION FORMULAS
    add_chapter_heading("CHAPTER 4: MATHEMATICAL MODELING & SIMULATION FORMULAS")
    add_body(
        "The RescueGrid platform executes four inter-connected simulation and operational models to manage disaster triage, supply allocation, dispatch performance, and hazard spatial relevance:"
    )

    # MODEL 1
    add_section_heading("4.1 MODEL 1: EMERGENCY PRIORITY SCORING MODEL (PS)")
    add_body("The Emergency Priority Scoring Model quantifies incident urgency on a 0 to 100 continuous scale using five weighted parameters:")
    
    add_formula_box("PS = 0.35 · S + 0.25 · P + 0.20 · W + 0.10 · R + 0.10 · D", "Equation 4.1 - Overall Priority Score Governing Formula")

    add_body("Individual Component Derivations:")
    add_body("1. Severity Factor (S): Derived from user/facility severity rating (1 to 5):")
    add_formula_box("S = (Severity_Rating / 5.0) · 100", "Equation 4.2 - Severity Rating Component")

    add_body("2. Population Impact Factor (P): Logarithmic scaling for affected individuals:")
    add_formula_box("P = min(100.0, (Affected_People / 50.0) · 100.0)", "Equation 4.3 - Affected Population Component")

    add_body("3. Waiting Time Factor (W): Time elapsed since initial intake:")
    add_formula_box("W = min(100.0, ((T_current - T_reported) / 12.0) · 100.0)", "Equation 4.4 - Waiting Time Component")

    add_body("4. Resource Shortage Factor (R): Ratio of unmet supply demand:")
    add_formula_box("R = max(0.0, ((Quantity_Requested - Quantity_Available) / Quantity_Requested) · 100.0)", "Equation 4.5 - Resource Shortage Component")

    add_body("5. Distance Isolation Factor (D): Distance penalty to nearest facility:")
    add_formula_box("D = min(100.0, (Distance_km / 50.0) · 100.0)", "Equation 4.6 - Distance Isolation Component")

    add_body("Priority Level Classification Rule:")
    add_formula_box("Level = 'Critical' (if PS >= 75), 'High' (if 55 <= PS < 75), 'Medium' (if 35 <= PS < 55), 'Low' (if PS < 35)", "Equation 4.7 - Priority Classification Rule")

    doc.add_page_break()

    # MODEL 2
    add_section_heading("4.2 MODEL 2: AUTOMATED RESOURCE ALLOCATION ENGINE MODEL (RA)")
    add_body("The Automated Resource Allocation Engine optimizes supply matching between warehouse stock and high-priority pending requests:")

    add_body("1. Allocated Quantity Equation for Request i from Warehouse Stock k:")
    add_formula_box("A_i = min( Q_requested_i , Q_warehouse_available_k )", "Equation 4.8 - Allocation Unit Formula")

    add_body("2. Post-Allocation Warehouse Stock Update:")
    add_formula_box("Q_warehouse_available_k(new) = Q_warehouse_available_k(old) - sum( A_i )", "Equation 4.9 - Inventory Stock Update Equation")

    add_body("3. Request Fulfillment Percentage Metric:")
    add_formula_box("Fulfillment_Pct = ( Quantity_Fulfilled / Quantity_Requested ) · 100 %", "Equation 4.10 - Supply Fulfillment Metric")

    # MODEL 3
    add_section_heading("4.3 MODEL 3: OPERATIONAL RESPONSE TIME & PERFORMANCE MODEL (RT)")
    add_body("The Operational Performance Model tracks dispatch latency, response duration, and system mean time to resolve (MTTR):")

    add_body("1. Incident Response Time Duration:")
    add_formula_box("T_response = T_resolved - T_reported  (in minutes)", "Equation 4.11 - Response Time Duration")

    add_body("2. Dispatch Latency Delay:")
    add_formula_box("T_dispatch_delay = T_assigned - T_reported  (in minutes)", "Equation 4.12 - Dispatch Latency Metric")

    add_body("3. Mean System Response Time (MTTR):")
    add_formula_box("MTTR = (1 / N) · sum( T_response_i )  for i = 1 to N", "Equation 4.13 - System Mean Time To Resolve")

    doc.add_page_break()

    # MODEL 4
    add_section_heading("4.4 MODEL 4: GDACS SPATIAL HAZARD RELEVANCE & PROXIMITY MODEL (GH)")
    add_body("The GDACS Spatial Hazard Model calculates great-circle distance between incident locations and disaster alert epicenters, as well as spatial bounding box rules:")

    add_body("1. Haversine Great-Circle Proximity Distance Formula:")
    add_formula_box("a = sin²(Δlat / 2) + cos(lat1) · cos(lat2) · sin²(Δlon / 2)", "Equation 4.14a - Haversine Spherical Term")
    add_formula_box("c = 2 · atan2( √a , √(1 - a) )", "Equation 4.14b - Angular Distance Term")
    add_formula_box("d_km = R_earth · c   (where R_earth = 6371.0 km)", "Equation 4.14c - Distance in Kilometers")

    add_body("2. India Geographic Coordinate Bounding Box Rule:")
    add_formula_box("Is_India = True if (6.0° <= Latitude <= 37.5° AND 68.0° <= Longitude <= 97.5°) else False", "Equation 4.15 - India Spatial Filter")

    add_body("3. Tamil Nadu Demonstration Region Bounding Box Rule:")
    add_formula_box("Is_Tamil_Nadu = True if (8.0° <= Latitude <= 13.5° AND 76.0° <= Longitude <= 80.5°) else False", "Equation 4.16 - Tamil Nadu Spatial Filter")

    doc.save(r"C:\Users\91812\.gemini\antigravity\brain\0df4f4ad-09b5-47a4-9e39-9ae1ab094f6e\RescueGrid_4_Simulation_Models.docx")
    print("4 Simulation Models docx created successfully!")

if __name__ == '__main__':
    create_report()
