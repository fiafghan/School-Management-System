from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Student, FeePayment


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'student_id', 'name', 'father_name', 'class_name', 
        'monthly_fee', 'phone', 'is_active', 'total_payments_display',
        'payments_count_display', 'registration_date'
    ]
    list_filter = ['class_name', 'is_active', 'registration_date']
    search_fields = ['student_id', 'name', 'father_name', 'phone']
    list_editable = ['is_active']
    readonly_fields = ['student_id', 'created_at', 'updated_at']
    fieldsets = (
        ('اطلاعات اساسی', {
            'fields': ('student_id', 'name', 'father_name', 'class_name')
        }),
        ('اطلاعات تماس و مالی', {
            'fields': ('phone', 'monthly_fee')
        }),
        ('وضعیت', {
            'fields': ('is_active', 'registration_date')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_payments_display(self, obj):
        total = obj.get_total_payments()
        return format_html(
            '<span style="color: green; font-weight: bold;">{} افغانی</span>',
            total
        )
    total_payments_display.short_description = 'مجموع پرداخت‌ها'
    
    def payments_count_display(self, obj):
        count = obj.get_payments_count()
        return format_html(
            '<span style="color: blue;">{} پرداخت</span>',
            count
        )
    payments_count_display.short_description = 'تعداد پرداخت‌ها'


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'amount', 'month_year', 'payment_method', 
        'payment_date', 'created_at'
    ]
    list_filter = [
        'payment_method', 'payment_date', 'month_year',
        'student__class_name'
    ]
    search_fields = [
        'student__name', 'student__student_id', 'notes'
    ]
    date_hierarchy = 'payment_date'
    readonly_fields = ['created_at']
    autocomplete_fields = ['student']
    
    fieldsets = (
        ('اطلاعات پرداخت', {
            'fields': ('student', 'amount', 'month_year', 'payment_method')
        }),
        ('جزئیات', {
            'fields': ('payment_date', 'notes')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student')


# Custom admin site configuration
admin.site.site_header = "سیستم مدیریت فیس - لیسه عالی خصوصی الازهر"
admin.site.site_title = "مدیریت فیس"
admin.site.index_title = "پنل مدیریت"
