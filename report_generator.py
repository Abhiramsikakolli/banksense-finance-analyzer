from fpdf import FPDF
from datetime import datetime

# custom pdf class with header and footer
class MyReport(FPDF):

    def header(self):
        self.set_fill_color(24, 95, 165)
        self.rect(0, 0, 210, 20, 'F')
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 20, 'BankSense - Finance Report', align='C', ln=True)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'BankSense | {datetime.now().strftime("%d %b %Y")} | Page {self.page_no()}', align='C')

    def section(self, title):
        self.ln(5)
        self.set_fill_color(230, 241, 251)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(24, 95, 165)
        self.cell(0, 9, f'  {title}', fill=True, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    # draws the 4 summary boxes at the top
    def summary_boxes(self, items):
        w = 190 / len(items)
        for label, val, color in items:
            x, y = self.get_x(), self.get_y()
            self.set_fill_color(*color)
            self.rect(x, y, w - 2, 18, 'F')
            self.set_font('Helvetica', '', 8)
            self.set_text_color(80, 80, 80)
            self.set_xy(x + 2, y + 2)
            self.cell(w - 4, 5, label)
            self.set_font('Helvetica', 'B', 11)
            self.set_text_color(30, 30, 30)
            self.set_xy(x + 2, y + 8)
            self.cell(w - 4, 8, val)
            self.set_xy(x + w, y)
        self.ln(22)


def generate_pdf_report(s, cat_df, mon_df, anom_df, tips):
    pdf = MyReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # report date
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%d %B %Y, %I:%M %p")}', ln=True)
    pdf.ln(2)

    # top summary
    pdf.section('Financial Summary')
    pdf.summary_boxes([
        ('Total Income',   f'Rs {s["total_income"]:,.0f}',   (234, 243, 222)),
        ('Total Expenses', f'Rs {s["total_expense"]:,.0f}',  (252, 235, 235)),
        ('Net Savings',    f'Rs {s["net_savings"]:,.0f}',    (230, 241, 251)),
        ('Savings Rate',   f'{s["savings_rate"]:.1f}%',      (250, 238, 218)),
    ])

    # category table
    pdf.section('Spending by Category')
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(24, 95, 165)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 8, 'Category', fill=True)
    pdf.cell(50, 8, 'Amount (Rs)', fill=True)
    pdf.cell(45, 8, '% of Total', fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)

    total = cat_df['Amount'].sum()
    for i, row in cat_df.iterrows():
        bg = (245, 248, 252) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(95, 7, str(row['Category']), fill=True)
        pdf.cell(50, 7, f'Rs {row["Amount"]:,.0f}', fill=True)
        pct = (row['Amount'] / total * 100) if total > 0 else 0
        pdf.cell(45, 7, f'{pct:.1f}%', fill=True, ln=True)
    pdf.ln(3)

    # monthly table
    pdf.section('Monthly Breakdown')
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(24, 95, 165)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(60, 8, 'Month', fill=True)
    pdf.cell(50, 8, 'Income', fill=True)
    pdf.cell(50, 8, 'Expense', fill=True)
    pdf.cell(30, 8, 'Savings', fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)

    for i, row in mon_df.iterrows():
        bg = (245, 248, 252) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_font('Helvetica', '', 9)
        saved = row['Income'] - row['Expense']
        pdf.cell(60, 7, str(row['Month']), fill=True)
        pdf.cell(50, 7, f'Rs {row["Income"]:,.0f}', fill=True)
        pdf.cell(50, 7, f'Rs {row["Expense"]:,.0f}', fill=True)
        pdf.set_text_color(0, 128, 0) if saved >= 0 else pdf.set_text_color(200, 0, 0)
        pdf.cell(30, 7, f'Rs {saved:,.0f}', fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # anomalies if any
    if len(anom_df) > 0:
        pdf.section('Unusual Transactions')
        pdf.set_font('Helvetica', '', 9)
        pdf.set_fill_color(252, 235, 235)
        for _, row in anom_df.head(5).iterrows():
            line = f"  {row['Date'].strftime('%d %b %Y')}  |  {row['Description']}  |  Rs {row['Amount']:,.0f}  |  Z: {row['ZScore']:.1f}"
            pdf.cell(0, 7, line, fill=True, ln=True)
            pdf.ln(1)
        pdf.ln(2)

    # saving tips
    pdf.section('Saving Recommendations')
    pdf.set_font('Helvetica', '', 10)
    for tip in tips:
        pdf.multi_cell(0, 8, f'  {tip}')
        pdf.ln(1)

    return pdf.output(dest='S').encode('latin-1')
