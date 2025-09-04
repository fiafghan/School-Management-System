import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from database import DatabaseManager
import sys
import traceback

# Configure matplotlib for better font handling
plt.rcParams['font.family'] = ['Arial Unicode MS', 'Tahoma', 'DejaVu Sans']

# Configure appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class AlAzharSchoolApp:
    def __init__(self):
        try:
            self.root = ctk.CTk()
            self.root.title("سیستم مدیریت فیس - لیسه عالی خصوصی ازهر")
            self.root.geometry("1400x900")
            
            # Initialize database
            self.db = DatabaseManager()
            
            # Afghan/Persian month names
            self.month_names = ['حمل', 'ثور', 'جوزا', 'سرطان', 'اسد', 'سنبله',
                               'میزان', 'عقرب', 'قوس', 'جدی', 'دلو', 'حوت']
            
            # Create main interface
            self.setup_main_interface()
            
        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا در راه‌اندازی", f"خطا در راه‌اندازی برنامه: {str(e)}")
            sys.exit(1)
        
    def setup_main_interface(self):
        """Setup the main application interface"""
        try:
            # Main title
            title_label = ctk.CTkLabel(
                self.root,
                text="سیستم مدیریت فیس - لیسه عالی خصوصی ازهر",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=20)
            
            # Create tabview
            self.tabview = ctk.CTkTabview(self.root, width=1150, height=700)
            self.tabview.pack(pady=20, padx=20, fill="both", expand=True)
            
            # Add tabs
            self.tabview.add("شاگردان")
            self.tabview.add("پرداخت فیس")
            self.tabview.add("گزارشات")
            self.tabview.add("تاریخچه پرداخت")
            
            # Setup each tab
            self.setup_students_tab()
            self.setup_payments_tab()
            self.setup_reports_tab()
            self.setup_history_tab()
            
        except Exception as e:
            print(f"Error setting up main interface: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در ایجاد رابط کاربری: {str(e)}")

    def setup_students_tab(self):
        """Setup students management tab"""
        try:
            students_frame = self.tabview.tab("شاگردان")
            
            # Add student form
            form_frame = ctk.CTkFrame(students_frame)
            form_frame.pack(pady=10, padx=10, fill="x")
            
            ctk.CTkLabel(form_frame, text="اضافه کردن شاگرد جدید", 
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            
            # Form fields
            fields_frame = ctk.CTkFrame(form_frame)
            fields_frame.pack(pady=10, padx=20, fill="x")
            
            # Student ID
            ctk.CTkLabel(fields_frame, text="شماره شاگرد:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
            self.student_id_entry = ctk.CTkEntry(fields_frame, width=200)
            self.student_id_entry.grid(row=0, column=1, padx=10, pady=5)
            
            # Name
            ctk.CTkLabel(fields_frame, text="نام شاگرد:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
            self.student_name_entry = ctk.CTkEntry(fields_frame, width=200)
            self.student_name_entry.grid(row=0, column=3, padx=10, pady=5)
            
            # Father name
            ctk.CTkLabel(fields_frame, text="نام پدر:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
            self.father_name_entry = ctk.CTkEntry(fields_frame, width=200)
            self.father_name_entry.grid(row=1, column=1, padx=10, pady=5)
            
            # Class
            ctk.CTkLabel(fields_frame, text="صنف:").grid(row=1, column=2, padx=10, pady=5, sticky="e")
            self.class_entry = ctk.CTkEntry(fields_frame, width=200)
            self.class_entry.grid(row=1, column=3, padx=10, pady=5)
            
            # Phone
            ctk.CTkLabel(fields_frame, text="تلفن:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
            self.phone_entry = ctk.CTkEntry(fields_frame, width=200)
            self.phone_entry.grid(row=2, column=1, padx=10, pady=5)
            
            # Monthly fee
            ctk.CTkLabel(fields_frame, text="فیس ماهانه:").grid(row=2, column=2, padx=10, pady=5, sticky="e")
            self.fee_entry = ctk.CTkEntry(fields_frame, width=200)
            self.fee_entry.grid(row=2, column=3, padx=10, pady=5)
            
            # Add button
            add_btn = ctk.CTkButton(form_frame, text="اضافه کردن شاگرد", 
                                   command=self.add_student)
            add_btn.pack(pady=10)
            
            # Students list
            list_frame = ctk.CTkFrame(students_frame)
            list_frame.pack(pady=10, padx=10, fill="both", expand=True)
            
            ctk.CTkLabel(list_frame, text="لیست شاگردان", 
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            
            # Create treeview for students list
            self.students_tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Father", "Class", "Phone", "Fee"), 
                                             show="headings", height=15)
            
            # Configure columns
            self.students_tree.heading("ID", text="شماره")
            self.students_tree.heading("Name", text="نام")
            self.students_tree.heading("Father", text="نام پدر")
            self.students_tree.heading("Class", text="صنف")
            self.students_tree.heading("Phone", text="تلفن")
            self.students_tree.heading("Fee", text="فیس ماهانه")
            
            self.students_tree.column("ID", width=100)
            self.students_tree.column("Name", width=150)
            self.students_tree.column("Father", width=150)
            self.students_tree.column("Class", width=100)
            self.students_tree.column("Phone", width=120)
            self.students_tree.column("Fee", width=100)
            
            self.students_tree.pack(pady=10, padx=10, fill="both", expand=True)
            
            # Refresh students list
            self.refresh_students_list()
            
        except Exception as e:
            print(f"Error setting up students tab: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در ایجاد لیست شاگردان: {str(e)}")

    def setup_payments_tab(self):
        """Setup payments tab"""
        try:
            payments_frame = self.tabview.tab("پرداخت فیس")
            
            # Payment form
            form_frame = ctk.CTkFrame(payments_frame)
            form_frame.pack(pady=10, padx=10, fill="x")
            
            ctk.CTkLabel(form_frame, text="ثبت پرداخت فیس", 
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            
            fields_frame = ctk.CTkFrame(form_frame)
            fields_frame.pack(pady=10, padx=20, fill="x")
            
            # Student selection
            ctk.CTkLabel(fields_frame, text="شاگرد:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
            self.student_combo = ctk.CTkComboBox(fields_frame, width=200, values=[])
            self.student_combo.grid(row=0, column=1, padx=10, pady=5)
            
            # Amount
            ctk.CTkLabel(fields_frame, text="مقدار:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
            self.amount_entry = ctk.CTkEntry(fields_frame, width=200)
            self.amount_entry.grid(row=0, column=3, padx=10, pady=5)
            
            # Month/Year
            ctk.CTkLabel(fields_frame, text="ماه/سال:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
            self.month_year_entry = ctk.CTkEntry(fields_frame, width=200, 
                                               placeholder_text="مثال: 1404-02")
            self.month_year_entry.grid(row=1, column=1, padx=10, pady=5)
            
            # Payment method
            ctk.CTkLabel(fields_frame, text="طریقه پرداخت:").grid(row=1, column=2, padx=10, pady=5, sticky="e")
            self.payment_method_combo = ctk.CTkComboBox(fields_frame, width=200, 
                                                      values=["نقدی", "چک", "انتقال بانکی"])
            self.payment_method_combo.grid(row=1, column=3, padx=10, pady=5)
            
            # Add payment button
            payment_btn = ctk.CTkButton(form_frame, text="ثبت پرداخت", 
                                       command=self.add_payment)
            payment_btn.pack(pady=10)
            
            # Refresh student combo
            self.refresh_student_combo()
            
        except Exception as e:
            print(f"Error setting up payments tab: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در ایجاد فرم پرداخت: {str(e)}")

    def setup_reports_tab(self):
        """Setup reports tab"""
        try:
            reports_frame = self.tabview.tab("گزارشات")
            
            # Report controls
            controls_frame = ctk.CTkFrame(reports_frame)
            controls_frame.pack(pady=10, padx=10, fill="x")
            
            ctk.CTkLabel(controls_frame, text="گزارشات مالی", 
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            
            # Month/Year selection
            selection_frame = ctk.CTkFrame(controls_frame)
            selection_frame.pack(pady=10)
            
            ctk.CTkLabel(selection_frame, text="سال:").grid(row=0, column=0, padx=10, pady=5)
            self.year_combo = ctk.CTkComboBox(selection_frame, width=100, 
                                            values=[str(y) for y in range(2020, 2030)])
            self.year_combo.set(str(datetime.now().year))
            self.year_combo.grid(row=0, column=1, padx=10, pady=5)
            
            ctk.CTkLabel(selection_frame, text="ماه:").grid(row=0, column=2, padx=10, pady=5)
            self.month_combo = ctk.CTkComboBox(selection_frame, width=100, 
                                              values=self.month_names)
            self.month_combo.set(self.month_names[datetime.now().month - 1])
            self.month_combo.grid(row=0, column=3, padx=10, pady=5)
            
            # Generate report button
            report_btn = ctk.CTkButton(controls_frame, text="تولید گزارش", 
                                      command=self.generate_report)
            report_btn.pack(pady=10)
            
            # Report display area
            self.report_frame = ctk.CTkFrame(reports_frame)
            self.report_frame.pack(pady=10, padx=10, fill="both", expand=True)
            
        except Exception as e:
            print(f"Error setting up reports tab: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در ایجاد گزارشات: {str(e)}")

    def setup_history_tab(self):
        """Setup payment history tab"""
        try:
            history_frame = self.tabview.tab("تاریخچه پرداخت")
            
            # Student selection for history
            selection_frame = ctk.CTkFrame(history_frame)
            selection_frame.pack(pady=10, padx=10, fill="x")
            
            ctk.CTkLabel(selection_frame, text="انتخاب شاگرد برای مشاهده تاریخچه:", 
                        font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
            
            self.history_student_combo = ctk.CTkComboBox(selection_frame, width=300, values=[])
            self.history_student_combo.pack(pady=10)
            
            view_history_btn = ctk.CTkButton(selection_frame, text="مشاهده تاریخچه", 
                                           command=self.view_student_history)
            view_history_btn.pack(pady=10)
            
            # History display
            self.history_display_frame = ctk.CTkFrame(history_frame)
            self.history_display_frame.pack(pady=10, padx=10, fill="both", expand=True)
            
            # Refresh combo
            self.refresh_history_combo()
            
        except Exception as e:
            print(f"Error setting up history tab: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در ایجاد تاریخچه پرداخت: {str(e)}")

    def add_student(self):
        """Add a new student"""
        try:
            student_data = {
                'student_id': self.student_id_entry.get(),
                'name': self.student_name_entry.get(),
                'father_name': self.father_name_entry.get(),
                'class_name': self.class_entry.get(),
                'phone': self.phone_entry.get(),
                'monthly_fee': float(self.fee_entry.get())
            }
            
            if self.db.add_student(student_data):
                messagebox.showinfo("موفقیت", "شاگرد با موفقیت اضافه شد")
                self.clear_student_form()
                self.refresh_students_list()
                self.refresh_student_combo()
                self.refresh_history_combo()
            else:
                messagebox.showerror("خطا", "خطا در اضافه کردن شاگرد")
        except ValueError:
            messagebox.showerror("خطا", "لطفاً مقدار فیس را به درستی وارد کنید")
        except Exception as e:
            print(f"Error adding student: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در اضافه کردن شاگرد: {str(e)}")

    def clear_student_form(self):
        """Clear student form fields"""
        self.student_id_entry.delete(0, 'end')
        self.student_name_entry.delete(0, 'end')
        self.father_name_entry.delete(0, 'end')
        self.class_entry.delete(0, 'end')
        self.phone_entry.delete(0, 'end')
        self.fee_entry.delete(0, 'end')

    def refresh_students_list(self):
        """Refresh the students list"""
        try:
            # Clear existing items
            for item in self.students_tree.get_children():
                self.students_tree.delete(item)
            
            # Add students
            students = self.db.get_all_students()
            for student in students:
                self.students_tree.insert("", "end", values=(
                    student['student_id'],
                    student['name'],
                    student['father_name'],
                    student['class_name'],
                    student['phone'],
                    f"{student['monthly_fee']} افغانی"
                ))
        except Exception as e:
            print(f"Error refreshing students list: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در به روز رسانی لیست شاگردان: {str(e)}")

    def refresh_student_combo(self):
        """Refresh student combo boxes"""
        try:
            students = self.db.get_all_students()
            student_list = [f"{s['student_id']} - {s['name']}" for s in students]
            self.student_combo.configure(values=student_list)
        except Exception as e:
            print(f"Error refreshing student combo: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در به روز رسانی لیست شاگردان: {str(e)}")

    def refresh_history_combo(self):
        """Refresh history combo box"""
        try:
            students = self.db.get_all_students()
            student_list = [f"{s['student_id']} - {s['name']}" for s in students]
            self.history_student_combo.configure(values=student_list)
        except Exception as e:
            print(f"Error refreshing history combo: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در به روز رسانی تاریخچه پرداخت: {str(e)}")

    def add_payment(self):
        """Add a payment"""
        try:
            student_selection = self.student_combo.get()
            if not student_selection:
                messagebox.showerror("خطا", "لطفاً شاگرد را انتخاب کنید")
                return
            
            student_id = student_selection.split(" - ")[0]
            
            payment_data = {
                'student_id': student_id,
                'payment_date': date.today().isoformat(),
                'amount': float(self.amount_entry.get()),
                'month_year': self.month_year_entry.get(),
                'payment_method': self.payment_method_combo.get()
            }
            
            if self.db.add_payment(payment_data):
                messagebox.showinfo("موفقیت", "پرداخت با موفقیت ثبت شد")
                self.amount_entry.delete(0, 'end')
                self.month_year_entry.delete(0, 'end')
            else:
                messagebox.showerror("خطا", "خطا در ثبت پرداخت")
        except ValueError:
            messagebox.showerror("خطا", "لطفاً مقدار را به درستی وارد کنید")
        except Exception as e:
            print(f"Error adding payment: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در ثبت پرداخت: {str(e)}")

    def generate_report(self):
        """Generate monthly report"""
        try:
            year_str = self.year_combo.get()
            month_str = self.month_combo.get()
            
            if not year_str or not month_str:
                messagebox.showerror("خطا", "لطفاً سال و ماه را انتخاب کنید")
                return
                
            year = int(year_str)
            
            # Find month index safely
            if month_str in self.month_names:
                month = self.month_names.index(month_str) + 1
            else:
                messagebox.showerror("خطا", "ماه انتخاب شده معتبر نیست")
                return
            
            summary = self.db.get_monthly_summary(year, month)
            
            # Clear previous report
            for widget in self.report_frame.winfo_children():
                widget.destroy()
            
            # Display summary
            ctk.CTkLabel(self.report_frame, 
                        text=f"گزارش ماه {month_str}/{year}", 
                        font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
            
            summary_text = f"""
            مجموع جمع آوری شده: {summary['total_collected']:,.0f} افغانی
            تعداد شاگردان پرداخت کننده: {summary['students_paid']}
            تعداد کل شاگردان: {summary['total_students']}
            تعداد شاگردان بدهکار: {summary['students_unpaid']}
            """
            
            ctk.CTkLabel(self.report_frame, text=summary_text, 
                        font=ctk.CTkFont(size=14)).pack(pady=10)
            
        except ValueError as e:
            messagebox.showerror("خطا", "لطفاً سال را به درستی وارد کنید")
        except Exception as e:
            print(f"Error generating report: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در تولید گزارش: {str(e)}")

    def view_student_history(self):
        """View payment history for selected student"""
        try:
            student_selection = self.history_student_combo.get()
            if not student_selection:
                messagebox.showerror("خطا", "لطفاً شاگرد را انتخاب کنید")
                return
            
            student_id = student_selection.split(" - ")[0]
            payments = self.db.get_student_payments(student_id)
            
            # Clear previous history
            for widget in self.history_display_frame.winfo_children():
                widget.destroy()
            
            ctk.CTkLabel(self.history_display_frame, 
                        text=f"تاریخچه پرداخت: {student_selection}", 
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            
            if payments:
                # Create treeview for payment history
                history_tree = ttk.Treeview(self.history_display_frame, 
                                          columns=("Date", "Amount", "Month", "Method"), 
                                          show="headings", height=10)
                
                history_tree.heading("Date", text="تاریخ پرداخت")
                history_tree.heading("Amount", text="مقدار")
                history_tree.heading("Month", text="ماه/سال")
                history_tree.heading("Method", text="طریقه پرداخت")
                
                for payment in payments:
                    history_tree.insert("", "end", values=(
                        payment['payment_date'],
                        f"{payment['amount']:,.0f} افغانی",
                        payment['month_year'],
                        payment['payment_method']
                    ))
                
                history_tree.pack(pady=10, padx=10, fill="both", expand=True)
            else:
                ctk.CTkLabel(self.history_display_frame, 
                            text="هیچ پرداختی ثبت نشده است", 
                            font=ctk.CTkFont(size=14)).pack(pady=20)
                
        except Exception as e:
            print(f"Error viewing student history: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در نمایش تاریخچه پرداخت: {str(e)}")

    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error during application run: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("خطا", f"خطا در اجرای برنامه: {str(e)}")

if __name__ == "__main__":
    try:
        app = AlAzharSchoolApp()
        app.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        print(traceback.format_exc())
        messagebox.showerror("خطای جدی", f"خطای جدی در برنامه: {str(e)}")
        sys.exit(1)
