"""
PDF Generator for:
1. Mini Project Final Review Official Circular / Notice (with evaluation slip)
2. EventQR Complete Uniform Final Review Report (with marks /10, attendance %, guide sign)
"""

import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page numbers"""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress page number on cover page
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 40, 30, page_text)
        self.drawString(40, 30, "Pondicherry University • Dept. of Computer Science • MCA Final Review")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 42, A4[0] - 40, 42)
        self.restoreState()

def create_notice_pdf(filename="Mini_Project_Final_Review_Notice.pdf"):
    print(f"[*] Generating {filename}...")
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    uni_title = ParagraphStyle(
        'UniTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        alignment=1,
        textColor=colors.HexColor('#0f2942')
    )
    uni_sub = ParagraphStyle(
        'UniSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        alignment=1,
        textColor=colors.HexColor('#334155')
    )
    dept_title = ParagraphStyle(
        'DeptTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=1,
        textColor=colors.HexColor('#1e3a8a')
    )
    circular_badge = ParagraphStyle(
        'CircularBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=1,
        textColor=colors.HexColor('#b91c1c')
    )
    subject_style = ParagraphStyle(
        'SubjectStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#0f172a')
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor('#1e293b')
    )
    callout_style = ParagraphStyle(
        'CalloutStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#1e3a8a')
    )
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1e3a8a')
    )
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )
    table_bold = ParagraphStyle(
        'TableBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # 1. Official Header
    story.append(Paragraph("PONDICHERRY UNIVERSITY", uni_title))
    story.append(Paragraph("(A Central University Established by an Act of Parliament, 1985)", uni_sub))
    story.append(Spacer(1, 3))
    story.append(Paragraph("SCHOOL OF ENGINEERING & TECHNOLOGY — DEPARTMENT OF COMPUTER SCIENCE", dept_title))
    story.append(Paragraph("R.V. Nagar, Kalapet, Puducherry – 605 014 | www.pondiuni.edu.in", uni_sub))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=8))

    # 2. Reference & Date Line
    meta_table = [
        [
            Paragraph("<strong>Ref. No.:</strong> PU/CS/MCA/MINI-PROJ/2026/FINAL-REV", table_text),
            Paragraph("<strong>Date:</strong> 03.11.2026", ParagraphStyle('R', parent=table_text, alignment=2))
        ]
    ]
    t_meta = Table(meta_table, colWidths=[340, 175])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # 3. Circular Title
    story.append(Paragraph("OFFICIAL CIRCULAR / NOTIFICATION", circular_badge))
    story.append(Spacer(1, 6))

    # 4. Subject Box
    sub_table = [
        [Paragraph("<strong>SUBJECT:</strong> SCHEDULE FOR FINAL REVIEW, WORKING DEMONSTRATION, ATTENDANCE VERIFICATION & EVALUATION (10 MARKS) — MCA 2ND YEAR (3RD SEMESTER) MINI PROJECT", subject_style)]
    ]
    t_sub = Table(sub_table, colWidths=[515])
    t_sub.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_sub)
    story.append(Spacer(1, 10))

    # 5. Announcement Message Box (Exact text from prompt emphasized)
    announcement_text = """
    <strong>Official Announcement:</strong><br/>
    <i>"Dear all, the final review for mini project is scheduled on 03.11.26. You are expected to submit your final report in proper uniform format & content and show the demonstration of your completed project to your guides. Get your reports evaluated and signed by your guides. Stick onto the schedule. Get your marks (for 10), attendance percentage and guide signature well ahead before the mentioned date. Late submissions will not be accepted."</i>
    """
    ann_table = [
        [Paragraph(announcement_text, callout_style)]
    ]
    t_ann = Table(ann_table, colWidths=[515])
    t_ann.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1.2, colors.HexColor('#3b82f6')),
        ('LINELEFT', (0,0), (0,0), 4, colors.HexColor('#1d4ed8')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_ann)
    story.append(Spacer(1, 12))

    # 6. Key Instructions Section
    story.append(Paragraph("Mandatory Instructions for MCA Students", h2_style))
    story.append(Spacer(1, 4))
    
    inst_points = [
        "<strong>1. Final Review Date & Timing:</strong> The final review will be conducted on <strong>03.11.2026</strong> from <strong>09:30 AM to 04:30 PM</strong> in the Department Computing Laboratories.",
        "<strong>2. Uniform Format Report:</strong> Students must submit the comprehensive project report bound/formatted strictly as per department guidelines (Title page, Project specifications, Layered architecture, Modules, Test logs, and Sign-off sheet).",
        "<strong>3. Working Software Demonstration:</strong> Live demonstration of all implemented features (UI, database operations, QR generation & webcam scanning, role management) must be presented directly to the guide.",
        "<strong>4. Attendance Percentage Requirement:</strong> Cumulative attendance percentage must be verified from department records and entered in the scorecard prior to marks sign-off.",
        "<strong>5. Evaluation (Total: 10 Marks):</strong> Guides will award marks out of 10 based on implementation, report quality, and viva defense. Late submissions will strictly not be accepted.",
    ]
    for pt in inst_points:
        story.append(Paragraph(f"• {pt}", body_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 8))

    # 7. Evaluation Rubric Table (Out of 10 Marks)
    story.append(Paragraph("Final Review Marking Scheme (Total: 10 Marks)", h2_style))
    story.append(Spacer(1, 4))
    
    rubric_data = [
        [Paragraph("<strong>Assessment Component</strong>", table_bold), Paragraph("<strong>Max Marks</strong>", table_bold), Paragraph("<strong>Evaluation Criteria</strong>", table_bold)],
        [Paragraph("Working Software Demonstration & Code Quality", table_text), Paragraph("<strong>4 Marks</strong>", table_text), Paragraph("Live demo, zero-error execution, real-time QR scanning, database integrity", table_text)],
        [Paragraph("Final Project Report & Documentation", table_text), Paragraph("<strong>3 Marks</strong>", table_text), Paragraph("Uniform format compliance, system design, architectural diagrams, test logs", table_text)],
        [Paragraph("Technical Viva Defense & Attendance", table_text), Paragraph("<strong>3 Marks</strong>", table_text), Paragraph("Subject mastery, answers to viva questions, verified attendance compliance", table_text)],
        [Paragraph("<strong>Total Score</strong>", table_bold), Paragraph("<strong>10 Marks</strong>", table_bold), Paragraph("<strong>Official Mark Entry for 3rd Semester Grade Record</strong>", table_bold)],
    ]
    t_rubric = Table(rubric_data, colWidths=[200, 75, 240])
    t_rubric.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_rubric)
    story.append(Spacer(1, 14))

    # 8. Student Evaluation Slip / Sign-off Scorecard
    story.append(Paragraph("Student Final Evaluation Record & Scorecard (Slip)", h2_style))
    story.append(Spacer(1, 4))

    eval_data = [
        [Paragraph("<strong>Candidate Name:</strong>", table_bold), Paragraph("Hardik Gupta", table_text), Paragraph("<strong>Register / Roll No:</strong>", table_bold), Paragraph("25MCA00PY0031", table_text)],
        [Paragraph("<strong>Course & Semester:</strong>", table_bold), Paragraph("MCA — 2nd Year, 3rd Semester", table_text), Paragraph("<strong>Department:</strong>", table_bold), Paragraph("Computer Science", table_text)],
        [Paragraph("<strong>Project Title:</strong>", table_bold), Paragraph("EventQR: AI-Powered Student Verification & Entry System", table_text), Paragraph("<strong>Review Date:</strong>", table_bold), Paragraph("03.11.2026", table_text)],
        [Paragraph("<strong>Verified Attendance %:</strong>", table_bold), Paragraph("<strong>94 %</strong> (Eligible)", table_text), Paragraph("<strong>Internal Guide:</strong>", table_bold), Paragraph("Dr. S. Joseph", table_text)],
        [Paragraph("<strong>Marks Awarded:</strong>", table_bold), Paragraph("<strong>______ / 10 Marks</strong>", table_bold), Paragraph("<strong>Guide Sign & Date:</strong>", table_bold), Paragraph("___________________", table_text)],
    ]
    t_eval = Table(eval_data, colWidths=[130, 160, 115, 110])
    t_eval.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1e3a8a')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#fef3c7')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_eval)
    story.append(Spacer(1, 24))

    # 9. Signatures Block
    sig_data = [
        [
            Paragraph("<strong>Dr. S. Joseph</strong><br/>Project Supervisor / Guide<br/>Dept. of Computer Science", table_text),
            Paragraph("<strong>Project Coordinator</strong><br/>MCA Mini Project Committee<br/>Pondicherry University", ParagraphStyle('C', parent=table_text, alignment=1)),
            Paragraph("<strong>Head of Department</strong><br/>Department of Computer Science<br/>Pondicherry University", ParagraphStyle('R', parent=table_text, alignment=2))
        ]
    ]
    t_sig = Table(sig_data, colWidths=[175, 165, 175])
    t_sig.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_sig)

    doc.build(story)
    print(f"[+] Successfully generated: {filename}")

if __name__ == '__main__':
    create_notice_pdf()
