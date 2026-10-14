"""
admin/ — Package quản trị License ExamAI (modular).
Tách từ admin_tool.py monolith → nhiều module nhỏ, dễ maintain.
"""


def launch():
    """Khởi chạy Admin App."""
    from admin.app import AdminApp
    app = AdminApp()
    app.mainloop()
