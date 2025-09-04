import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime, timedelta
import customtkinter as ctk
from database import DatabaseManager
import sqlite3

class ReportGenerator:
    def __init__(self, db: DatabaseManager):
        self.db = db
        
    def get_daily_collections(self, start_date, end_date):
        """Get daily collection data for a date range"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT payment_date, SUM(amount) as daily_total
            FROM fee_payments 
            WHERE payment_date BETWEEN ? AND ?
            GROUP BY payment_date
            ORDER BY payment_date
        ''', (start_date, end_date))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_weekly_collections(self, year, week_num):
        """Get weekly collection data"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Calculate week start and end dates
        jan_1 = datetime(year, 1, 1)
        week_start = jan_1 + timedelta(weeks=week_num-1)
        week_end = week_start + timedelta(days=6)
        
        cursor.execute('''
            SELECT SUM(amount) as weekly_total, COUNT(*) as payment_count
            FROM fee_payments 
            WHERE payment_date BETWEEN ? AND ?
        ''', (week_start.date(), week_end.date()))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total': result[0] if result[0] else 0,
            'count': result[1] if result[1] else 0,
            'week_start': week_start.date(),
            'week_end': week_end.date()
        }
    
    def get_yearly_summary(self, year):
        """Get yearly collection summary"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                strftime('%m', payment_date) as month,
                SUM(amount) as monthly_total,
                COUNT(*) as payment_count
            FROM fee_payments 
            WHERE strftime('%Y', payment_date) = ?
            GROUP BY strftime('%m', payment_date)
            ORDER BY month
        ''', (str(year),))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_class_wise_collections(self, year, month):
        """Get class-wise collection data"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        month_year = f"{year}-{month:02d}"
        
        cursor.execute('''
            SELECT 
                s.class_name,
                SUM(fp.amount) as class_total,
                COUNT(DISTINCT fp.student_id) as students_paid,
                COUNT(DISTINCT s.student_id) as total_students
            FROM students s
            LEFT JOIN fee_payments fp ON s.student_id = fp.student_id 
                AND fp.month_year = ?
            WHERE s.is_active = 1
            GROUP BY s.class_name
            ORDER BY s.class_name
        ''', (month_year,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def create_monthly_chart(self, parent_frame, year, month):
        """Create monthly collection chart"""
        # Clear previous chart
        for widget in parent_frame.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
        
        # Get data
        summary = self.db.get_monthly_summary(year, month)
        class_data = self.get_class_wise_collections(year, month)
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(f'گزارش ماه {month}/{year}', fontsize=16, fontweight='bold')
        
        # 1. Payment Status Pie Chart
        paid = summary['students_paid']
        unpaid = summary['students_unpaid']
        
        ax1.pie([paid, unpaid], labels=['پرداخت شده', 'پرداخت نشده'], 
                autopct='%1.1f%%', startangle=90, colors=['#2ecc71', '#e74c3c'])
        ax1.set_title('وضعیت پرداخت شاگردان')
        
        # 2. Class-wise Collections Bar Chart
        if class_data:
            classes = [row[0] for row in class_data]
            amounts = [row[1] if row[1] else 0 for row in class_data]
            
            ax2.bar(classes, amounts, color='#3498db')
            ax2.set_title('جمع آوری به تفکیک صنف')
            ax2.set_ylabel('مقدار (افغانی)')
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. Collection vs Expected
        total_students = summary['total_students']
        # Assume average fee (you might want to calculate this properly)
        expected_total = total_students * 1000  # placeholder
        actual_total = summary['total_collected']
        
        ax3.bar(['مورد انتظار', 'جمع آوری شده'], [expected_total, actual_total], 
                color=['#f39c12', '#27ae60'])
        ax3.set_title('مقایسه جمع آوری')
        ax3.set_ylabel('مقدار (افغانی)')
        
        # 4. Class-wise Payment Rate
        if class_data:
            payment_rates = [(row[2]/row[3])*100 if row[3] > 0 else 0 for row in class_data]
            ax4.bar(classes, payment_rates, color='#9b59b6')
            ax4.set_title('درصد پرداخت به تفکیک صنف')
            ax4.set_ylabel('درصد')
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Embed chart in tkinter
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        return canvas
    
    def create_yearly_chart(self, parent_frame, year):
        """Create yearly collection chart"""
        # Clear previous chart
        for widget in parent_frame.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
        
        # Get yearly data
        yearly_data = self.get_yearly_summary(year)
        
        if not yearly_data:
            # Show no data message
            ctk.CTkLabel(parent_frame, text="دیتا برای نمایش وجود ندارد", 
                        font=ctk.CTkFont(size=16)).pack(pady=50)
            return
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle(f'گزارش سالانه {year}', fontsize=16, fontweight='bold')
        
        # Monthly collections line chart
        months = [int(row[0]) for row in yearly_data]
        amounts = [row[1] for row in yearly_data]
        
        month_names = ['حمل', 'ثور', 'جوزا', 'سرطان', 'اسد', 'سنبله',
                      'میزان', 'عقرب', 'قوس', 'جدی', 'دلو', 'حوت']
        
        ax1.plot(months, amounts, marker='o', linewidth=2, markersize=6, color='#3498db')
        ax1.set_title('جمع آوری ماهانه')
        ax1.set_xlabel('ماه')
        ax1.set_ylabel('مقدار (افغانی)')
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(months)
        ax1.set_xticklabels([month_names[m-1] for m in months], rotation=45)
        
        # Monthly payment counts
        payment_counts = [row[2] for row in yearly_data]
        ax2.bar(months, payment_counts, color='#2ecc71')
        ax2.set_title('تعداد پرداخت‌های ماهانه')
        ax2.set_xlabel('ماه')
        ax2.set_ylabel('تعداد پرداخت')
        ax2.set_xticks(months)
        ax2.set_xticklabels([month_names[m-1] for m in months], rotation=45)
        
        plt.tight_layout()
        
        # Embed chart
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        return canvas
    
    def generate_printable_report(self, year, month):
        """Generate a printable report"""
        summary = self.db.get_monthly_summary(year, month)
        class_data = self.get_class_wise_collections(year, month)
        
        report_text = f"""
=== گزارش ماهانه لیسه عالی خصوصی الازهر ===
ماه: {month}/{year}
تاریخ تولید گزارش: {datetime.now().strftime('%Y-%m-%d %H:%M')}

=== خلاصه کلی ===
مجموع جمع آوری شده: {summary['total_collected']:,.0f} افغانی
تعداد شاگردان پرداخت کننده: {summary['students_paid']}
تعداد کل شاگردان: {summary['total_students']}
تعداد شاگردان بدهکار: {summary['students_unpaid']}
درصد پرداخت: {(summary['students_paid']/summary['total_students']*100):.1f}%

=== گزارش به تفکیک صنف ===
"""
        
        for class_info in class_data:
            class_name, total, paid_count, total_count = class_info
            payment_rate = (paid_count/total_count*100) if total_count > 0 else 0
            report_text += f"""
صنف {class_name}:
  - مجموع جمع آوری: {total if total else 0:,.0f} افغانی
  - شاگردان پرداخت کننده: {paid_count}/{total_count}
  - درصد پرداخت: {payment_rate:.1f}%
"""
        
        return report_text
