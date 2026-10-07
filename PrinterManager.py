import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import win32print
import subprocess
import json
import os
import threading
from plyer import notification

class ModernPrinterManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("مدير الطابعات الاحترافي - Pro Printer Manager")
        self.root.geometry("1150x750")
        self.root.minsize(950, 600)

        # محاذاة النافذة في منتصف الشاشة
        self.root.eval('tk::PlaceWindow . center')

        # أسماء ملفات البيانات
        self.data_file = "printer_users.json"
        self.ink_file = "ink_stock.json"
        
        # إنشاء واسترجاع البيانات المستخرجة تلقائياً
        self.users_data = self.load_json_data(self.data_file, self.get_default_users())
        self.ink_data = self.load_json_data(self.ink_file, self.get_default_inks())

        # تهيئة الألوان والتنسيقات البصرية
        self.setup_styles()

        # بناء الواجهة
        self.build_ui()

        # جلب البيانات لأول مرة
        self.refresh_printers_async()

    def get_default_users(self):
        """البيانات المستخرجة من الصور السابقة"""
        return {
            "HP Color LaserJet Pro M479 [6B1A90]": "IT Department",
            "\\\\192.168.1.119\\ricoh mp c2004 pcl 6": "Finance Department",
            "\\\\192.168.1.133\\HP LaserJet M109-M112": "Abdullah - Gamil with Abdurahm",
            "\\\\192.168.1.135\\HP LaserJet Professional P1102": "Seif",
            "\\\\192.168.1.144\\HP Laser MFP 131 133 135-138": "salem",
            "\\\\192.168.1.154\\HP Color LaserJet Pro M479 PCL-6 (V4) (Network)": "Safety",
            "\\\\192.168.1.174\\ricoh m c2000 pcl 6": "logistaic Department",
            "\\\\192.168.1.183\\HP Laser 103 107 108 (Copy 1)": "HR-Moaz",
            "\\\\192.168.1.183\\HP ColorLaserJet MFP M278-M281 PCL-6 (V4) (Network)": "HR Department",
            "\\\\LOG-02\\HP Color LaserJet Pro MFP M277 PCL 6 (Copy 1)": "store-john",
            "\\\\Log-02\\ricoh m c2000 pcl 6": "john"
        }

    def get_default_inks(self):
        """بيانات الأحبار المحددة مسبقاً"""
        return {
            "HP Color LaserJet Pro M479 [6B1A90]": {"name": "415A", "qty": "0"},
            "\\\\192.168.1.119\\ricoh mp c2004 pcl 6": {"name": "C2000H", "qty": "4"}
        }

    def load_json_data(self, filepath, default_data):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # في حال عدم وجود الملف يتم إنشاؤه وتخزين البيانات الافتراضية به
        self.save_json_data(filepath, default_data)
        return default_data

    def save_json_data(self, filepath, data):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def setup_styles(self):
        """إعداد المظهر والألوان الحديثة للبرنامج"""
        self.bg_color = "#F8F9FA"
        self.card_bg = "#FFFFFF"
        self.primary_color = "#0D6EFD"
        self.text_color = "#212529"
        
        self.root.configure(bg=self.bg_color)

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure("Treeview", 
                             background=self.card_bg,
                             foreground=self.text_color,
                             rowheight=32,
                             fieldbackground=self.card_bg,
                             font=('Segoe UI', 10))
        
        self.style.configure("Treeview.Heading", 
                             background="#E9ECEF",
                             foreground=self.text_color,
                             font=('Segoe UI', 10, 'bold'),
                             padding=5)
        
        self.style.map("Treeview", background=[('selected', '#E2E6EA')], foreground=[('selected', '#000000')])

        self.style.configure("TButton", 
                             font=('Segoe UI', 9, 'bold'),
                             padding=6,
                             background="#E9ECEF",
                             foreground="#495057")
        self.style.map("TButton", background=[('active', '#DEE2E6')])

        self.style.configure("Primary.TButton", 
                             font=('Segoe UI', 9, 'bold'),
                             padding=6,
                             background=self.primary_color,
                             foreground="white")
        self.style.map("Primary.TButton", background=[('active', '#0B5ED7')])

    def build_ui(self):
        header_frame = tk.Frame(self.root, bg=self.bg_color)
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        title_label = tk.Label(header_frame, text="🖨️ لوحة تحكم وإدارة الطابعات", font=("Segoe UI", 16, "bold"), bg=self.bg_color, fg=self.text_color)
        title_label.pack(side="left")

        self.stats_frame = tk.Frame(header_frame, bg=self.bg_color)
        self.stats_frame.pack(side="right")

        self.lbl_total = self.create_stat_card(self.stats_frame, "الإجمالي", "0", "#6C757D")
        self.lbl_ready = self.create_stat_card(self.stats_frame, "جاهزة", "0", "#198754")
        self.lbl_issues = self.create_stat_card(self.stats_frame, "تنبيهات/أخطاء", "0", "#DC3545")

        search_frame = tk.Frame(self.root, bg=self.bg_color)
        search_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(search_frame, text="🔍 بحث سريع:", font=("Segoe UI", 10, "bold"), bg=self.bg_color).pack(side="left", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_tree())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10), width=30)
        search_entry.pack(side="left", padx=5)

        btn_refresh = ttk.Button(search_frame, text="🔄 تحديث القائمة", command=self.refresh_printers_async)
        btn_refresh.pack(side="right")

        table_frame = tk.Frame(self.root, bg=self.card_bg, bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        tree_scroll = ttk.Scrollbar(table_frame)
        tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(table_frame, 
                                 columns=("printer", "user", "ink_name", "ink_qty", "status", "is_default"), 
                                 show="headings", 
                                 yscrollcommand=tree_scroll.set)
        
        self.tree.heading("printer", text="اسم الطابعة الموصلة")
        self.tree.heading("user", text="اسم المستخدم / ملاحظة")
        self.tree.heading("ink_name", text="موديل/اسم الحبر")
        self.tree.heading("ink_qty", text="الكمية بالخزينة")
        self.tree.heading("status", text="حالة الطابعة")
        self.tree.heading("is_default", text="الافتراضية")

        self.tree.column("printer", width=240, anchor="w")
        self.tree.column("user", width=150, anchor="center")
        self.tree.column("ink_name", width=130, anchor="center")
        self.tree.column("ink_qty", width=100, anchor="center")
        self.tree.column("status", width=220, anchor="center")
        self.tree.column("is_default", width=90, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.tree.tag_configure("ready", foreground="#198754")
        self.tree.tag_configure("error", foreground="#DC3545")
        self.tree.tag_configure("warning", foreground="#FD7E14")
        self.tree.tag_configure("offline", foreground="#6C757D")
        self.tree.tag_configure("printing", foreground="#0D6EFD")

        self.tree.bind("<<TreeviewSelect>>", self.on_printer_select)

        control_card = tk.LabelFrame(self.root, text=" أدوات التحكم وإدارة الطابعة المحددة ", font=("Segoe UI", 10, "bold"), bg=self.bg_color, fg=self.text_color, padx=15, pady=10)
        control_card.pack(fill="x", padx=20, pady=(0, 15))

        edit_frame = tk.Frame(control_card, bg=self.bg_color)
        edit_frame.pack(fill="x", pady=(0, 5))

        self.btn_edit_user = ttk.Button(edit_frame, text="✏️ تعديل المستخدم", command=self.edit_user, state="disabled")
        self.btn_edit_user.pack(side="left", padx=5)

        self.btn_edit_ink = ttk.Button(edit_frame, text="📦 تعديل مخزون الحبر", command=self.edit_ink, state="disabled")
        self.btn_edit_ink.pack(side="left", padx=5)

        ttk.Separator(control_card, orient='horizontal').pack(fill='x', pady=8)

        actions_frame = tk.Frame(control_card, bg=self.bg_color)
        actions_frame.pack(fill="x")

        self.action_buttons = []

        btn_default = ttk.Button(actions_frame, text="★ تعيين كافتراضية", style="Primary.TButton", command=self.set_default)
        btn_default.pack(side="left", padx=4)
        self.action_buttons.append(btn_default)

        btn_queue = ttk.Button(actions_frame, text="📋 طابور الطباعة", command=self.open_queue)
        btn_queue.pack(side="left", padx=4)
        self.action_buttons.append(btn_queue)

        btn_pause = ttk.Button(actions_frame, text="⏸️ إيقاف مؤقت", command=lambda: self.control_printer(win32print.PRINTER_CONTROL_PAUSE, "تم إيقاف الطابعة."))
        btn_pause.pack(side="left", padx=4)
        self.action_buttons.append(btn_pause)

        btn_resume = ttk.Button(actions_frame, text="▶️ استئناف", command=lambda: self.control_printer(win32print.PRINTER_CONTROL_RESUME, "تم استئناف الطابعة."))
        btn_resume.pack(side="left", padx=4)
        self.action_buttons.append(btn_resume)

        btn_purge = ttk.Button(actions_frame, text="🗑️ تنظيف المهام", command=lambda: self.control_printer(win32print.PRINTER_CONTROL_PURGE, "تم مسح جميع مهام الطباعة."))
        btn_purge.pack(side="left", padx=4)
        self.action_buttons.append(btn_purge)

        btn_prefs = ttk.Button(actions_frame, text="⚙️ التفضيلات", command=self.open_preferences)
        btn_prefs.pack(side="left", padx=4)
        self.action_buttons.append(btn_prefs)

        btn_repair = ttk.Button(actions_frame, text="🛠️ إصلاح أعطال", command=self.repair_printer)
        btn_repair.pack(side="right", padx=4)
        self.action_buttons.append(btn_repair)

        self.disable_controls()

    def create_stat_card(self, parent, title, value, color):
        frame = tk.Frame(parent, bg="#FFFFFF", bd=1, relief="solid", padx=10, pady=3)
        frame.pack(side="left", padx=4)
        
        lbl_title = tk.Label(frame, text=title, font=("Segoe UI", 8), bg="#FFFFFF", fg="#6C757D")
        lbl_title.pack()
        
        lbl_val = tk.Label(frame, text=value, font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg=color)
        lbl_val.pack()
        return lbl_val

    def refresh_printers_async(self):
        threading.Thread(target=self._fetch_printers_data, daemon=True).start()

    def _fetch_printers_data(self):
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        
        try:
            default_printer = win32print.GetDefaultPrinter()
        except Exception:
            default_printer = ""

        printers_list = []
        ready_cnt = 0
        issue_cnt = 0

        for printer in printers:
            p_name = printer[2]
            user_name = self.users_data.get(p_name, "---")
            
            ink_info = self.ink_data.get(p_name, {"name": "غير محدد", "qty": "0"})
            ink_name = ink_info.get("name", "غير محدد")
            ink_qty = ink_info.get("qty", "0")

            is_def = "★ نعم" if p_name == default_printer else ""
            
            try:
                hprinter = win32print.OpenPrinter(p_name)
                p_info = win32print.GetPrinter(hprinter, 2) 
                status_code = p_info.get('Status', 0)
                status_text, row_tag, ink_low = self.get_printer_status_info(status_code)
                win32print.ClosePrinter(hprinter)
            except Exception:
                status_text = "⚪ تعذر قراءة الحالة"
                row_tag = "offline"
                ink_low = False

            if row_tag == "ready":
                ready_cnt += 1
            else:
                issue_cnt += 1

            printers_list.append((p_name, user_name, ink_name, ink_qty, status_text, is_def, row_tag, ink_low))

        self.root.after(0, self._update_ui_tree, printers_list, ready_cnt, issue_cnt)

    def _update_ui_tree(self, printers_list, ready_cnt, issue_cnt):
        self.all_printers_cache = printers_list
        
        self.lbl_total.config(text=str(len(printers_list)))
        self.lbl_ready.config(text=str(ready_cnt))
        self.lbl_issues.config(text=str(issue_cnt))

        self.filter_tree()

    def filter_tree(self):
        search_query = self.search_var.get().strip().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.disable_controls()

        if not hasattr(self, 'all_printers_cache'):
            return

        for p in self.all_printers_cache:
            p_name, user_name, ink_name, ink_qty, status_text, is_def, row_tag, ink_low = p
            
            if search_query in p_name.lower() or search_query in user_name.lower() or search_query in ink_name.lower():
                self.tree.insert("", "end", values=(p_name, user_name, ink_name, ink_qty, status_text, is_def), tags=(row_tag,))

            if ink_low:
                self.send_desktop_notification(p_name, ink_name, ink_qty)

    def get_printer_status_info(self, status_code):
        if status_code == 0:
            return "🟢 جاهزة للاستخدام", "ready", False
        
        statuses = []
        tag = "ready"
        ink_low = False
        
        if status_code & 0x00000080: 
            statuses.append("⚪ غير متصلة (Offline)")
            tag = "offline"
        if status_code & 0x00000002: 
            statuses.append("🔴 يوجد خطأ")
            tag = "error"
        if status_code & 0x00020000: 
            statuses.append("🔴 الحبر منخفض جداً")
            tag = "error"
            ink_low = True
        if status_code & 0x00000010: 
            statuses.append("🟠 لا يوجد ورق")
            if tag != "error": tag = "warning"
        if status_code & 0x00000400: 
            statuses.append("🔵 تطبع الآن...")
            if tag == "ready": tag = "printing"
            
        if not statuses:
            return f"⚪ حالة غير معروفة ({status_code})", "offline", False
            
        return " | ".join(statuses), tag, ink_low

    def send_desktop_notification(self, printer_name, ink_name, qty):
        try:
            notification.notify(
                title="⚠️ تنبيه: نفاد الحبر!",
                message=f"الطابعة: {printer_name}\nنوع الحبر: {ink_name}\nالكمية بالخزينة: {qty}",
                app_name="مدير الطابعات",
                timeout=5
            )
        except Exception as e:
            print(f"خطأ الإشعار: {e}")

    def disable_controls(self):
        self.btn_edit_user.config(state="disabled")
        self.btn_edit_ink.config(state="disabled")
        for btn in self.action_buttons:
            btn.config(state="disabled")

    def enable_controls(self):
        self.btn_edit_user.config(state="normal")
        self.btn_edit_ink.config(state="normal")
        for btn in self.action_buttons:
            btn.config(state="normal")

    def on_printer_select(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            self.enable_controls()
        else:
            self.disable_controls()

    def get_selected_printer_name(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return None
        return self.tree.item(selected_item[0])['values'][0]

    def edit_user(self):
        p_name = self.get_selected_printer_name()
        if not p_name: return

        current_user = self.users_data.get(p_name, "")
        new_user = simpledialog.askstring("اسم المستخدم", f"أدخل اسم المستخدم أو الملاحظة للطابعة:\n{p_name}", initialvalue=current_user, parent=self.root)
        
        if new_user is not None:
            self.users_data[p_name] = new_user
            self.save_json_data(self.data_file, self.users_data)
            self.refresh_printers_async()

    def edit_ink(self):
        p_name = self.get_selected_printer_name()
        if not p_name: return

        current_ink = self.ink_data.get(p_name, {"name": "", "qty": "0"})
        
        new_ink_name = simpledialog.askstring("اسم الحبر", f"أدخل موديل الحبر الخاص بـ:\n{p_name}", initialvalue=current_ink.get("name", ""), parent=self.root)
        if new_ink_name is None: return

        new_ink_qty = simpledialog.askstring("الكمية المتاحة", f"أدخل الكمية المتوفرة بالخزينة:", initialvalue=current_ink.get("qty", "0"), parent=self.root)
        if new_ink_qty is None: return

        self.ink_data[p_name] = {"name": new_ink_name, "qty": new_ink_qty}
        self.save_json_data(self.ink_file, self.ink_data)
        self.refresh_printers_async()

    def set_default(self):
        p_name = self.get_selected_printer_name()
        if p_name:
            try:
                win32print.SetDefaultPrinter(p_name)
                self.refresh_printers_async() 
                messagebox.showinfo("نجاح", f"تم تعيين '{p_name}' كطابعة افتراضية.")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء التعيين: {e}")

    def control_printer(self, command_code, success_msg):
        p_name = self.get_selected_printer_name()
        if p_name:
            try:
                PRINTER_ALL_ACCESS = {"DesiredAccess": win32print.PRINTER_ALL_ACCESS}
                hprinter = win32print.OpenPrinter(p_name, PRINTER_ALL_ACCESS)
                win32print.SetPrinter(hprinter, 0, None, command_code)
                win32print.ClosePrinter(hprinter)
                messagebox.showinfo("نجاح", success_msg)
            except Exception as e:
                messagebox.showerror("صلاحيات مفقودة", f"تأكد من تشغيل البرنامج كمسؤول.\n{e}")

    def open_preferences(self):
        p_name = self.get_selected_printer_name()
        if p_name:
            subprocess.Popen(f'rundll32 printui.dll,PrintUIEntry /e /n "{p_name}"', shell=True)

    def open_queue(self):
        p_name = self.get_selected_printer_name()
        if p_name:
            subprocess.Popen(f'rundll32 printui.dll,PrintUIEntry /o /n "{p_name}"', shell=True)

    def repair_printer(self):
        p_name = self.get_selected_printer_name()
        if p_name:
            msg = messagebox.askyesno("إصلاح مشاكل الطابعة", f"سيتم محاولة إصلاح الطابعة '{p_name}' عن طريق:\n1- أداة تشخيص الأخطاء.\n2- إعادة تشغيل خدمة Spooler.\n\nهل تريد المتابعة؟")
            if msg:
                try:
                    subprocess.Popen("msdt.exe /id PrinterDiagnostic", shell=True)
                    subprocess.Popen("net stop spooler & net start spooler", shell=True)
                except Exception as e:
                    messagebox.showerror("خطأ", f"تعذر التنفيذ: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernPrinterManagerApp(root)
    root.mainloop()