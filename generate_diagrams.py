"""
Script to generate publication-grade UML, Architecture, and Data Flow Diagrams
for EventQR Mini Project Report using Matplotlib.
All diagrams are rendered in high resolution (300 DPI) with clean academic styling.
"""

import os
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), '.mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch

def setup_canvas(width=10, height=6.5):
    fig, ax = plt.subplots(figsize=(width, height), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    return fig, ax

def draw_box(ax, x, y, w, h, title, subtitle=None, bg_color='#f8fafc', edge_color='#1e293b', title_color='#0f172a', title_size=10, sub_size=8, lw=1.5, radius=1.5):
    # Rounded box
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0.5,rounding_size={radius}",
                         facecolor=bg_color, edgecolor=edge_color, linewidth=lw)
    ax.add_patch(box)
    
    if subtitle:
        ax.text(x + w/2, y + h*0.62, title, ha='center', va='center', fontsize=title_size, fontweight='bold', color=title_color)
        ax.text(x + w/2, y + h*0.32, subtitle, ha='center', va='center', fontsize=sub_size, color='#475569')
    else:
        ax.text(x + w/2, y + h/2, title, ha='center', va='center', fontsize=title_size, fontweight='bold', color=title_color)

def draw_arrow(ax, x1, y1, x2, y2, label=None, color='#1e293b', lw=1.3, style='->', label_pos=0.5, label_offset=2.5, fontsize=8):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style, mutation_scale=11,
                            color=color, linewidth=lw)
    ax.add_patch(arrow)
    if label:
        lx = x1 + (x2 - x1) * label_pos
        ly = y1 + (y2 - y1) * label_pos + label_offset
        ax.text(lx, ly, label, ha='center', va='center', fontsize=fontsize, color='#334155',
                bbox=dict(boxstyle='square,pad=0.15', facecolor='white', edgecolor='none', alpha=0.9))

# =============================================================================
# 1. SYSTEM ARCHITECTURE DIAGRAM (3-Tier Layered Architecture)
# =============================================================================
def make_architecture_diagram():
    fig, ax = setup_canvas(10, 6.8)
    
    # Title
    ax.text(50, 96, "EventQR: 3-Tier Layered System Architecture", ha='center', va='center', fontsize=13, fontweight='bold', color='#0f172a')
    
    # Tier 1: Presentation Tier
    draw_box(ax, 5, 72, 90, 18, "", bg_color='#f1f5f9', edge_color='#64748b', lw=1.2, radius=1.0)
    ax.text(7, 87, "PRESENTATION TIER (CLIENT INTERFACE)", fontsize=9, fontweight='bold', color='#1e3a8a')
    draw_box(ax, 8, 74, 26, 11, "Student Web Portal", "Responsive HTML5 / TailwindCSS", bg_color='#ffffff')
    draw_box(ax, 37, 74, 26, 11, "Faculty Control Desk", "Roster & Quota Management", bg_color='#ffffff')
    draw_box(ax, 66, 74, 26, 11, "Admin Console / Scanner HUD", "Webcam Gate HUD & Approvals", bg_color='#ffffff')
    
    # Arrows Tier 1 -> Tier 2
    draw_arrow(ax, 21, 72, 21, 62, "HTTP / JSON", lw=1.2)
    draw_arrow(ax, 50, 72, 50, 62, "Session / REST", lw=1.2)
    draw_arrow(ax, 79, 72, 79, 62, "POST /api/verify", lw=1.2)

    # Tier 2: Application / Business Logic Tier
    draw_box(ax, 5, 34, 90, 28, "", bg_color='#e2e8f0', edge_color='#475569', lw=1.2, radius=1.0)
    ax.text(7, 58.5, "APPLICATION & BUSINESS LOGIC TIER (FLASK BACKEND)", fontsize=9, fontweight='bold', color='#1e3a8a')
    
    draw_box(ax, 8, 45, 26, 10, "Authentication Subsystem", "Role Auth & 6-Digit Email OTP", bg_color='#ffffff')
    draw_box(ax, 37, 45, 26, 10, "Event & Quota Manager", "Capacity Limits & Moderation", bg_color='#ffffff')
    draw_box(ax, 66, 45, 26, 10, "Waitlist Engine (FIFO)", "Automated Seat Reallocation", bg_color='#ffffff')

    draw_box(ax, 8, 36, 26, 7.5, "Token Issuance Engine", "CSPRNG 32-char Tokens", bg_color='#ffffff')
    draw_box(ax, 37, 36, 26, 7.5, "QR Generation Pipeline", "Reed-Solomon Level H", bg_color='#ffffff')
    draw_box(ax, 66, 36, 26, 7.5, "OpenCV & pyzbar Service", "Video Frame Extraction", bg_color='#ffffff')

    # Arrows Tier 2 -> Tier 3
    draw_arrow(ax, 25, 34, 25, 22, "ACID Reads/Writes", lw=1.2)
    draw_arrow(ax, 50, 34, 50, 22, "Atomic Transactions", lw=1.2)
    draw_arrow(ax, 75, 34, 75, 22, "Audit Logging", lw=1.2)

    # Tier 3: Data & Infrastructure Tier
    draw_box(ax, 5, 4, 90, 18, "", bg_color='#f1f5f9', edge_color='#64748b', lw=1.2, radius=1.0)
    ax.text(7, 19, "DATA PERSISTENCE & INFRASTRUCTURE TIER", fontsize=9, fontweight='bold', color='#1e3a8a')
    
    draw_box(ax, 8, 6, 26, 10.5, "Relational Database", "SQLite3 / PostgreSQL Engine", bg_color='#ffffff')
    draw_box(ax, 37, 6, 26, 10.5, "Media & Ticket Storage", "Static PNG QR Codes & Passes", bg_color='#ffffff')
    draw_box(ax, 66, 6, 26, 10.5, "SMTP Mail Gateway", "Campus Email SMTP / TLS", bg_color='#ffffff')

    plt.tight_layout()
    fig.savefig("diagram_architecture.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_architecture.png")

# =============================================================================
# 2. UML USE CASE DIAGRAM
# =============================================================================
def make_use_case_diagram():
    fig, ax = setup_canvas(10.5, 7.2)
    
    # Title
    ax.text(50, 97, "UML Use Case Diagram: EventQR Platform", ha='center', va='center', fontsize=13, fontweight='bold', color='#0f172a')
    
    # System Boundary Box
    system_box = FancyBboxPatch((28, 4), 44, 90,
                                boxstyle="round,pad=0.5,rounding_size=1.0",
                                facecolor='#f8fafc', edgecolor='#334155', linewidth=1.5, linestyle='--')
    ax.add_patch(system_box)
    ax.text(50, 91.5, "System Boundary: EventPass Core", ha='center', va='center', fontsize=10, fontweight='bold', color='#1e293b')

    # Actors (Left: Student & Organizer; Right: Administrator & Gate Camera)
    def draw_actor(ax, x, y, name):
        # Head
        circle = Circle((x, y + 4), 1.8, facecolor='#ffffff', edgecolor='#0f172a', linewidth=1.5)
        ax.add_patch(circle)
        # Body
        ax.plot([x, x], [y + 2.2, y - 2.5], color='#0f172a', lw=1.8)
        # Arms
        ax.plot([x - 2.5, x + 2.5], [y + 0.8, y + 0.8], color='#0f172a', lw=1.8)
        # Legs
        ax.plot([x, x - 2.2], [y - 2.5, y - 6.5], color='#0f172a', lw=1.8)
        ax.plot([x, x + 2.2], [y - 2.5, y - 6.5], color='#0f172a', lw=1.8)
        # Name
        ax.text(x, y - 9.5, name, ha='center', va='center', fontsize=9, fontweight='bold', color='#0f172a')

    draw_actor(ax, 12, 70, "Student\nAttendee")
    draw_actor(ax, 12, 28, "Faculty\nOrganizer")
    draw_actor(ax, 88, 70, "System\nAdministrator")
    draw_actor(ax, 88, 28, "Gate Scanner\n(Hardware/Device)")

    # Use Case Ellipses
    def draw_use_case(ax, x, y, text):
        ellipse = patches.Ellipse((x, y), 28, 6.5, facecolor='#ffffff', edgecolor='#1e3a8a', linewidth=1.4)
        ax.add_patch(ellipse)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='semibold', color='#0f172a')

    cases = [
        (50, 84, "Sign In via Password / Email OTP"),
        (50, 74, "Browse & Search Campus Events"),
        (50, 64, "Register for Event & Claim Pass"),
        (50, 54, "Join Dynamic FIFO Waitlist"),
        (50, 44, "Create & Configure Campus Event"),
        (50, 34, "Review Registration Rosters"),
        (50, 24, "Moderate & Approve Events"),
        (50, 14, "Scan QR Code & Validate Entry"),
    ]

    for cx, cy, cname in cases:
        draw_use_case(ax, cx, cy, cname)

    # Actor-to-Use-Case lines
    # Student
    ax.plot([15, 36], [70, 84], color='#475569', lw=1.1)
    ax.plot([15, 36], [70, 74], color='#475569', lw=1.1)
    ax.plot([15, 36], [70, 64], color='#475569', lw=1.1)
    ax.plot([15, 36], [70, 54], color='#475569', lw=1.1)

    # Faculty Organizer
    ax.plot([15, 36], [28, 44], color='#475569', lw=1.1)
    ax.plot([15, 36], [28, 34], color='#475569', lw=1.1)
    ax.plot([15, 36], [28, 14], color='#475569', lw=1.1)

    # Administrator
    ax.plot([85, 64], [70, 84], color='#475569', lw=1.1)
    ax.plot([85, 64], [70, 24], color='#475569', lw=1.1)
    ax.plot([85, 64], [70, 34], color='#475569', lw=1.1)

    # Gate Scanner
    ax.plot([85, 64], [28, 14], color='#475569', lw=1.1)

    plt.tight_layout()
    fig.savefig("diagram_use_case.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_use_case.png")

# =============================================================================
# 3. UML CLASS DIAGRAM
# =============================================================================
def make_class_diagram():
    fig, ax = setup_canvas(10.5, 7.5)
    
    ax.text(50, 97, "UML Class Diagram: EventQR Data Model & Domain Entities", ha='center', va='center', fontsize=13, fontweight='bold', color='#0f172a')

    def draw_uml_class(ax, x, y, w, h, class_name, attributes, methods):
        # Outer box
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=0.8", facecolor='#ffffff', edgecolor='#0f172a', linewidth=1.3)
        ax.add_patch(rect)
        # Header box
        hdr_h = 4.5
        hdr = Rectangle((x, y + h - hdr_h), w, hdr_h, facecolor='#f1f5f9', edgecolor='#0f172a', linewidth=1.1)
        ax.add_patch(hdr)
        ax.text(x + w/2, y + h - hdr_h/2, class_name, ha='center', va='center', fontsize=9, fontweight='bold', color='#0f172a')
        
        # Attributes
        attr_y = y + h - hdr_h - 2.5
        for a in attributes:
            ax.text(x + 1.2, attr_y, a, ha='left', va='center', fontsize=7.5, color='#334155', fontfamily='monospace')
            attr_y -= 2.2
            
        # Divider line
        div_y = y + len(methods) * 2.2 + 2.5
        ax.plot([x, x + w], [div_y, div_y], color='#94a3b8', lw=0.8)
        
        # Methods
        meth_y = div_y - 2.2
        for m in methods:
            ax.text(x + 1.2, meth_y, m, ha='left', va='center', fontsize=7.5, color='#0f766e', fontfamily='monospace')
            meth_y -= 2.2

    # Classes
    # User Class
    u_attrs = ["- id: int (PK)", "- name: string", "- email: string", "- roll_number: string", "- department: string", "- role: string"]
    u_meths = ["+ verify_password()", "+ generate_otp()", "+ is_authenticated()"]
    draw_uml_class(ax, 5, 52, 26, 38, "User", u_attrs, u_meths)

    # Event Class
    e_attrs = ["- id: int (PK)", "- title: string", "- organizer_id: int (FK)", "- venue: string", "- capacity: int", "- status: string", "- date: string"]
    e_meths = ["+ get_confirmed_count()", "+ is_seat_available()", "+ promote_waitlist()"]
    draw_uml_class(ax, 40, 52, 28, 38, "Event", e_attrs, e_meths)

    # Registration Class
    r_attrs = ["- id: int (PK)", "- user_id: int (FK)", "- event_id: int (FK)", "- status: string", "- token: string (Unique)", "- waitlist_pos: int"]
    r_meths = ["+ cancel_seat()", "+ mint_security_token()", "+ get_admission_pass()"]
    draw_uml_class(ax, 74, 52, 24, 38, "Registration", r_attrs, r_meths)

    # EmailOTP Class
    o_attrs = ["- id: int (PK)", "- email: string", "- otp_hash: string", "- expires_at: datetime"]
    o_meths = ["+ validate_code()", "+ is_expired()"]
    draw_uml_class(ax, 5, 10, 26, 24, "EmailOTP", o_attrs, o_meths)

    # EntryLog Class
    l_attrs = ["- id: int (PK)", "- registration_id: int (FK)", "- event_id: int (FK)", "- check_in_time: timestamp"]
    l_meths = ["+ record_entry()", "+ audit_replays()"]
    draw_uml_class(ax, 40, 10, 28, 24, "EntryLog", l_attrs, l_meths)

    # QRCodeManager Class
    q_attrs = ["- token_seed: string", "- error_correction: Level_H", "- finder_mask: int"]
    q_meths = ["+ render_png()", "+ scan_video_frame()"]
    draw_uml_class(ax, 74, 10, 24, 24, "QRCodeManager", q_attrs, q_meths)

    # Associations
    # User -> Registration (1 to *)
    draw_arrow(ax, 31, 71, 74, 71, "1..*", style='->', lw=1.2)
    # Event -> Registration (1 to *)
    draw_arrow(ax, 68, 71, 74, 71, "", style='->', lw=1.2)
    # Registration -> EntryLog (1 to 0..1)
    draw_arrow(ax, 86, 52, 68, 24, "1..0,1", style='->', lw=1.2)
    # User -> EmailOTP (1 to *)
    draw_arrow(ax, 18, 52, 18, 34, "1..*", style='->', lw=1.2)
    # Registration -> QRCodeManager
    draw_arrow(ax, 86, 52, 86, 34, "generates", style='->', lw=1.2)

    plt.tight_layout()
    fig.savefig("diagram_class.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_class.png")

# =============================================================================
# 4. UML SEQUENCE DIAGRAM
# =============================================================================
def make_sequence_diagram():
    fig, ax = setup_canvas(10.5, 7.2)
    
    ax.text(50, 97, "UML Sequence Diagram: Registration, Token Issuance & Gate Scan", ha='center', va='center', fontsize=12.5, fontweight='bold', color='#0f172a')

    # Lifelines
    lifelines = [
        (12, "Student\nBrowser"),
        (35, "Flask Web\nServer"),
        (58, "Relational\nDatabase"),
        (78, "SMTP Email\nService"),
        (92, "Webcam Gate\nScanner"),
    ]

    for lx, lname in lifelines:
        draw_box(ax, lx - 7, 86, 14, 8, lname, bg_color='#f1f5f9', title_size=8, radius=0.6)
        ax.plot([lx, lx], [86, 8], color='#94a3b8', linestyle='--', lw=1.0)

    # Sequence Messages
    steps = [
        (82, 12, 35, "1. Request OTP / Submit Roll No", False),
        (76, 35, 58, "2. Query User Verification", False),
        (70, 35, 78, "3. Dispatch 6-digit OTP", False),
        (64, 78, 12, "4. Deliver OTP Email to Inbox", True),
        (58, 12, 35, "5. Submit Received OTP", False),
        (52, 35, 58, "6. Verify OTP Hash & Mint Token", False),
        (46, 35, 12, "7. Render High-Density QR Pass", True),
        (38, 12, 92, "8. Present Pass to Gate Webcam", False),
        (30, 92, 35, "9. Send Scanned Token Payload", False),
        (22, 35, 58, "10. Query entry_logs for Replay", False),
        (16, 58, 35, "11. Replay=0: Record Single-Entry Log", True),
        (10, 35, 92, "12. Return VALID (Green HUD & Chime)", True),
    ]

    for y, x1, x2, msg, is_dashed in steps:
        style = '-->' if is_dashed else '->'
        col = '#0284c7' if is_dashed else '#0f172a'
        arrow = FancyArrowPatch((x1, y), (x2, y),
                                arrowstyle='->', mutation_scale=10,
                                color=col, linewidth=1.2,
                                linestyle='--' if is_dashed else '-')
        ax.add_patch(arrow)
        mid_x = (x1 + x2) / 2
        ax.text(mid_x, y + 1.6, msg, ha='center', va='center', fontsize=7.2, color='#1e293b',
                bbox=dict(boxstyle='square,pad=0.1', facecolor='white', edgecolor='none', alpha=0.9))

    plt.tight_layout()
    fig.savefig("diagram_sequence.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_sequence.png")

# =============================================================================
# 5. ACTIVITY DIAGRAM 1: Multi-Modal Registration & Email OTP Workflow
# =============================================================================
def make_activity_1():
    fig, ax = setup_canvas(10, 7.5)
    ax.text(50, 97, "Activity Diagram 1: Multi-Modal Registration & Email OTP Workflow", ha='center', va='center', fontsize=12, fontweight='bold', color='#0f172a')

    # Initial node
    init = Circle((50, 91), 2.0, facecolor='#0f172a', edgecolor='#0f172a')
    ax.add_patch(init)
    draw_arrow(ax, 50, 89, 50, 82, lw=1.2)

    # Action 1: User submits credentials
    draw_box(ax, 32, 76, 36, 6, "User Inputs Email / Roll Number", bg_color='#ffffff')
    draw_arrow(ax, 50, 76, 50, 69, lw=1.2)

    # Decision 1: Auth Mode
    draw_box(ax, 36, 63, 28, 6, "Auth Mode Selected?", bg_color='#e0f2fe', edge_color='#0284c7')
    
    # Left Branch: Password Auth
    draw_arrow(ax, 36, 66, 18, 66, "Password", lw=1.2)
    draw_arrow(ax, 18, 66, 18, 56, lw=1.2)
    draw_box(ax, 6, 50, 24, 6, "Verify PBKDF2 Password", bg_color='#ffffff')
    draw_arrow(ax, 18, 50, 18, 42, lw=1.2)

    # Right Branch: Real-Time OTP Auth
    draw_arrow(ax, 64, 66, 82, 66, "Email OTP", lw=1.2)
    draw_arrow(ax, 82, 66, 82, 56, lw=1.2)
    draw_box(ax, 68, 50, 28, 6, "Generate 6-Digit OTP & Send SMTP", bg_color='#ffffff')
    draw_arrow(ax, 82, 50, 82, 42, lw=1.2)

    # Decision: OTP Validation
    draw_box(ax, 70, 36, 24, 6, "OTP Correct & < 300s?", bg_color='#e0f2fe', edge_color='#0284c7')
    draw_arrow(ax, 82, 42, 82, 42, lw=1.2)

    # Reject branch
    draw_arrow(ax, 94, 39, 97, 39, "No", lw=1.0)
    draw_arrow(ax, 97, 39, 97, 79, lw=1.0)
    draw_arrow(ax, 97, 79, 68, 79, "Retry Limit", lw=1.0)

    # Pass branch to Merge
    draw_arrow(ax, 70, 39, 56, 28, "Yes (Valid)", lw=1.2)
    draw_arrow(ax, 18, 42, 44, 28, "Match", lw=1.2)

    # Merge Node / Action: Issue Session
    draw_box(ax, 35, 22, 30, 6, "Establish Authenticated Session", bg_color='#ffffff')
    draw_arrow(ax, 50, 22, 50, 15, lw=1.2)

    # Final Action: Redirect to Role Dashboard
    draw_box(ax, 30, 9, 40, 6, "Redirect: Student / Organizer / Admin Desk", bg_color='#f1f5f9')
    draw_arrow(ax, 50, 9, 50, 4, lw=1.2)

    # Final Node
    out_c = Circle((50, 2.5), 2.0, facecolor='none', edgecolor='#0f172a', linewidth=1.5)
    in_c = Circle((50, 2.5), 1.2, facecolor='#0f172a', edgecolor='#0f172a')
    ax.add_patch(out_c)
    ax.add_patch(in_c)

    plt.tight_layout()
    fig.savefig("diagram_activity_1.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_activity_1.png")

# =============================================================================
# 6. ACTIVITY DIAGRAM 2: Computer Vision Gate Scan & Replay Defense
# =============================================================================
def make_activity_2():
    fig, ax = setup_canvas(10, 7.5)
    ax.text(50, 97, "Activity Diagram 2: Computer Vision Gate Scan & Replay Attack Defense", ha='center', va='center', fontsize=12, fontweight='bold', color='#0f172a')

    # Initial node
    init = Circle((50, 92), 2.0, facecolor='#0f172a', edgecolor='#0f172a')
    ax.add_patch(init)
    draw_arrow(ax, 50, 90, 50, 83, lw=1.2)

    # Frame Capture
    draw_box(ax, 30, 77, 40, 6, "OpenCV Captures Frame via Webcam (cv2)", bg_color='#ffffff')
    draw_arrow(ax, 50, 77, 50, 70, lw=1.2)

    # Grayscale & pyzbar
    draw_box(ax, 28, 64, 44, 6, "Grayscale Conversion & pyzbar Finder Localization", bg_color='#ffffff')
    draw_arrow(ax, 50, 64, 50, 57, lw=1.2)

    # Decision 1: QR Found?
    draw_box(ax, 35, 51, 30, 6, "QR Code Decoded?", bg_color='#e0f2fe', edge_color='#0284c7')
    
    # Loop back if not found
    draw_arrow(ax, 65, 54, 78, 54, "No", lw=1.0)
    draw_arrow(ax, 78, 54, 78, 80, lw=1.0)
    draw_arrow(ax, 78, 80, 70, 80, "Next Frame", lw=1.0)

    # Found: Query Database
    draw_arrow(ax, 50, 51, 50, 44, "Yes: 32-char Token", lw=1.2)
    draw_box(ax, 28, 38, 44, 6, "Query DB: Check Token Exists & Event Match", bg_color='#ffffff')
    draw_arrow(ax, 50, 38, 50, 31, lw=1.2)

    # Decision 2: Already Scanned?
    draw_box(ax, 33, 25, 34, 6, "Token Already in entry_logs?", bg_color='#fee2e2', edge_color='#ef4444')
    
    # Replay Detected (Reject)
    draw_arrow(ax, 67, 28, 82, 28, "Yes: Replay Attempt", lw=1.2)
    draw_box(ax, 74, 15, 24, 7, "REJECT ADMISSION\nRed Alert HUD & Error Audio", bg_color='#fee2e2', edge_color='#ef4444')

    # Valid Entry (Grant)
    draw_arrow(ax, 33, 28, 18, 28, "No: First Scan", lw=1.2)
    draw_box(ax, 6, 15, 24, 7, "GRANT ENTRY\nInsert entry_logs & Green HUD", bg_color='#dcfce7', edge_color='#22c55e')

    # Merge to Final Node
    draw_arrow(ax, 18, 15, 45, 4, lw=1.1)
    draw_arrow(ax, 86, 15, 55, 4, lw=1.1)

    out_c = Circle((50, 3.5), 2.0, facecolor='none', edgecolor='#0f172a', linewidth=1.5)
    in_c = Circle((50, 3.5), 1.2, facecolor='#0f172a', edgecolor='#0f172a')
    ax.add_patch(out_c)
    ax.add_patch(in_c)

    plt.tight_layout()
    fig.savefig("diagram_activity_2.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_activity_2.png")

# =============================================================================
# 7. ACTIVITY DIAGRAM 3: Quota Saturation & FIFO Waitlist Auto-Promotion
# =============================================================================
def make_activity_3():
    fig, ax = setup_canvas(10, 7.5)
    ax.text(50, 97, "Activity Diagram 3: Quota Saturation & FIFO Waitlist Auto-Promotion", ha='center', va='center', fontsize=12, fontweight='bold', color='#0f172a')

    # Initial node
    init = Circle((50, 91), 2.0, facecolor='#0f172a', edgecolor='#0f172a')
    ax.add_patch(init)
    draw_arrow(ax, 50, 89, 50, 82, lw=1.2)

    # Student registers
    draw_box(ax, 30, 76, 40, 6, "Student Submits Registration for Event", bg_color='#ffffff')
    draw_arrow(ax, 50, 76, 50, 69, lw=1.2)

    # Capacity check
    draw_box(ax, 32, 63, 36, 6, "Confirmed Count < Capacity Limit?", bg_color='#e0f2fe', edge_color='#0284c7')
    
    # Path A: Seats Available
    draw_arrow(ax, 32, 66, 18, 66, "Yes", lw=1.2)
    draw_arrow(ax, 18, 66, 18, 56, lw=1.2)
    draw_box(ax, 6, 50, 24, 6, "Assign status='confirmed'\nMint Token & QR Pass", bg_color='#dcfce7')
    draw_arrow(ax, 18, 50, 18, 38, lw=1.2)

    # Path B: Quota Full -> Waitlist
    draw_arrow(ax, 68, 66, 82, 66, "No (Quota Full)", lw=1.2)
    draw_arrow(ax, 82, 66, 82, 56, lw=1.2)
    draw_box(ax, 68, 50, 28, 6, "Enqueue in Waitlist\npos = max(waitlist_pos) + 1", bg_color='#fef3c7')
    draw_arrow(ax, 82, 50, 82, 38, lw=1.2)

    # Event Cancellation trigger
    draw_box(ax, 25, 32, 50, 6, "Trigger: Confirmed Attendee Cancels Registration", bg_color='#f1f5f9', edge_color='#64748b', lw=1.3)
    draw_arrow(ax, 50, 32, 50, 25, lw=1.2)

    # Automated Promotion Logic
    draw_box(ax, 20, 18, 60, 7, "Auto-Promote Head of Waitlist (MIN waitlist_pos)\nStatus -> 'confirmed', Mint Token, Send Email Notification", bg_color='#ffffff', edge_color='#0284c7', lw=1.4)
    draw_arrow(ax, 50, 18, 50, 10, lw=1.2)

    # Final Node
    out_c = Circle((50, 5), 2.0, facecolor='none', edgecolor='#0f172a', linewidth=1.5)
    in_c = Circle((50, 5), 1.2, facecolor='#0f172a', edgecolor='#0f172a')
    ax.add_patch(out_c)
    ax.add_patch(in_c)

    plt.tight_layout()
    fig.savefig("diagram_activity_3.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_activity_3.png")

# =============================================================================
# 8. DATA FLOW DIAGRAMS: Level 0 and Level 1
# =============================================================================
def make_dfd_diagrams():
    # DFD Level 0 (Context)
    fig, ax = setup_canvas(10, 6.5)
    ax.text(50, 96, "Data Flow Diagram – Level 0: Context Level Diagram", ha='center', va='center', fontsize=12.5, fontweight='bold', color='#0f172a')

    # Central Process
    proc = Circle((50, 50), 14, facecolor='#f1f5f9', edgecolor='#1e3a8a', linewidth=2.0)
    ax.add_patch(proc)
    ax.text(50, 52, "0.0\nEventQR\nPlatform", ha='center', va='center', fontsize=11, fontweight='bold', color='#1e3a8a')

    # Entities
    # Student
    draw_box(ax, 6, 70, 22, 12, "Student Attendee", bg_color='#ffffff', edge_color='#0f172a')
    # Faculty Organizer
    draw_box(ax, 6, 18, 22, 12, "Faculty Organizer", bg_color='#ffffff', edge_color='#0f172a')
    # Admin
    draw_box(ax, 72, 70, 22, 12, "Central Administrator", bg_color='#ffffff', edge_color='#0f172a')
    # Gate Scanner
    draw_box(ax, 72, 18, 22, 12, "Gate Optical Scanner", bg_color='#ffffff', edge_color='#0f172a')

    # Data Flows
    draw_arrow(ax, 28, 76, 38, 58, "Credentials / Reg", lw=1.2)
    draw_arrow(ax, 38, 54, 28, 72, "Digital QR Pass", lw=1.2)

    draw_arrow(ax, 28, 24, 38, 44, "Event Proposal", lw=1.2)
    draw_arrow(ax, 38, 40, 28, 20, "Roster / Attendance", lw=1.2)

    draw_arrow(ax, 62, 58, 72, 76, "System Metrics", lw=1.2)
    draw_arrow(ax, 72, 72, 62, 54, "Event Moderation", lw=1.2)

    draw_arrow(ax, 72, 24, 62, 44, "Scanned QR Token", lw=1.2)
    draw_arrow(ax, 62, 40, 72, 20, "Admission Status", lw=1.2)

    plt.tight_layout()
    fig.savefig("diagram_dfd_level0.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_dfd_level0.png")

# =============================================================================
# 9. ENTITY-RELATIONSHIP (ER) DIAGRAM
# =============================================================================
def make_er_diagram():
    fig, ax = setup_canvas(10.5, 7.2)
    ax.text(50, 97, "Entity-Relationship (ER) Schema Cardinality Model", ha='center', va='center', fontsize=13, fontweight='bold', color='#0f172a')

    def draw_entity(ax, x, y, w, h, name, attrs):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=0.6", facecolor='#ffffff', edgecolor='#0f172a', linewidth=1.3)
        ax.add_patch(box)
        hdr = Rectangle((x, y + h - 3.8), w, 3.8, facecolor='#e2e8f0', edgecolor='#0f172a', linewidth=1.0)
        ax.add_patch(hdr)
        ax.text(x + w/2, y + h - 1.9, name, ha='center', va='center', fontsize=9, fontweight='bold', color='#0f172a')
        
        ay = y + h - 6.0
        for a in attrs:
            ax.text(x + 1.2, ay, a, ha='left', va='center', fontsize=7.2, color='#334155', fontfamily='monospace')
            ay -= 2.0

    # Entities
    u_attrs = ["id: int (PK)", "name: text", "email: text (UQ)", "roll_no: text (UQ)", "department: text", "role: text"]
    draw_entity(ax, 5, 52, 26, 22, "USERS", u_attrs)

    e_attrs = ["id: int (PK)", "title: text", "organizer_id: (FK)", "capacity: int", "venue: text", "status: text", "date: text"]
    draw_entity(ax, 40, 52, 26, 24, "EVENTS", e_attrs)

    r_attrs = ["id: int (PK)", "user_id: (FK)", "event_id: (FK)", "status: text", "token: text (UQ)", "waitlist_pos: int"]
    draw_entity(ax, 74, 52, 24, 24, "REGISTRATIONS", r_attrs)

    l_attrs = ["id: int (PK)", "registration_id: (FK)", "event_id: (FK)", "check_in_time: ts"]
    draw_entity(ax, 74, 12, 24, 18, "ENTRY_LOGS", l_attrs)

    o_attrs = ["id: int (PK)", "email: text", "otp_hash: text", "created_at: ts", "expires_at: ts"]
    draw_entity(ax, 5, 12, 26, 20, "EMAIL_OTPS", o_attrs)

    m_attrs = ["id: int (PK)", "roll_no: text (UQ)", "name: text", "department: text"]
    draw_entity(ax, 40, 12, 26, 18, "ELIGIBILITY_MASTER", m_attrs)

    # Relationships & Cardinalities
    # USERS -> REGISTRATIONS (1:N)
    draw_arrow(ax, 31, 65, 74, 65, "1 : N (registers)", lw=1.2)
    # EVENTS -> REGISTRATIONS (1:N)
    draw_arrow(ax, 66, 65, 74, 65, "", lw=1.2)
    # USERS -> EVENTS (1:N organizer)
    draw_arrow(ax, 31, 58, 40, 58, "1 : N (organizes)", lw=1.2)
    # REGISTRATIONS -> ENTRY_LOGS (1:1)
    draw_arrow(ax, 86, 52, 86, 30, "1 : 0..1 (single gate scan)", lw=1.2)
    # USERS -> EMAIL_OTPS (1:N)
    draw_arrow(ax, 18, 52, 18, 32, "1 : N (requests)", lw=1.2)

    plt.tight_layout()
    fig.savefig("diagram_er.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[+] Generated diagram_er.png")

if __name__ == '__main__':
    print("[*] Generating all UML and Architectural Diagrams...")
    make_architecture_diagram()
    make_use_case_diagram()
    make_class_diagram()
    make_sequence_diagram()
    make_activity_1()
    make_activity_2()
    make_activity_3()
    make_dfd_diagrams()
    make_er_diagram()
    print("[SUCCESS] All 9 high-resolution diagrams generated successfully!")
