from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
import jdatetime
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import csv
from decimal import Decimal

from .models import Student, FeePayment
from .forms import StudentForm, FeePaymentForm, ReportFilterForm, StudentSearchForm


def dashboard(request):
    """Main dashboard view with summary statistics"""
    # Use Jalali (Afghan) calendar for dashboard context
    j_now = jdatetime.date.today()
    current_year = j_now.year
    current_month = j_now.month
    
    # Get monthly summary
    monthly_summary = FeePayment.get_monthly_summary(current_year, current_month)
    
    # Get recent payments
    recent_payments = FeePayment.objects.select_related('student').order_by('-created_at')[:10]
    
    # Get total statistics
    total_students = Student.objects.filter(is_active=True).count()
    total_collected_all_time = FeePayment.objects.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Get class-wise data for current month
    class_data = FeePayment.get_class_wise_collections(current_year, current_month)
    
    context = {
        'monthly_summary': monthly_summary,
        'recent_payments': recent_payments,
        'total_students': total_students,
        'total_collected_all_time': total_collected_all_time,
        'class_data': class_data,
        'current_month_name': get_afghan_month_name(current_month),
        'current_year': current_year,
    }
    
    return render(request, 'school_management/dashboard.html', context)


def student_list(request):
    """View for listing and searching students"""
    form = StudentSearchForm(request.GET)
    students = Student.objects.all().order_by('name')
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        class_filter = form.cleaned_data.get('class_filter')
        
        if search:
            students = students.filter(
                Q(name__icontains=search) |
                Q(student_id__icontains=search) |
                Q(father_name__icontains=search)
            )
        
        if class_filter:
            students = students.filter(class_name=class_filter)
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'students': page_obj,
    }
    
    return render(request, 'school_management/student_list.html', context)


def student_add(request):
    """View for adding new students"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'شاگرد {student.name} با موفقیت اضافه شد.')
            return redirect('student_list')
    else:
        form = StudentForm()
    
    context = {'form': form, 'title': 'اضافه کردن شاگرد جدید'}
    return render(request, 'school_management/student_form.html', context)


def student_edit(request, pk):
    """View for editing existing students"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'اطلاعات شاگرد {student.name} به روز رسانی شد.')
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    
    context = {
        'form': form, 
        'student': student, 
        'title': f'ویرایش اطلاعات {student.name}'
    }
    return render(request, 'school_management/student_form.html', context)


def student_detail(request, pk):
    """View for student details and payment history"""
    student = get_object_or_404(Student, pk=pk)
    payments = student.payments.all().order_by('-payment_date')
    
    # Pagination for payments
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_payments = student.get_total_payments()
    payments_count = student.get_payments_count()
    latest_payment = student.get_latest_payment()
    
    context = {
        'student': student,
        'page_obj': page_obj,
        'payments': page_obj,
        'total_payments': total_payments,
        'payments_count': payments_count,
        'latest_payment': latest_payment,
    }
    
    return render(request, 'school_management/student_detail.html', context)


def payment_add(request):
    """View for adding new payments"""
    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(
                request, 
                f'پرداخت {payment.amount} افغانی برای {payment.student.name} ثبت شد.'
            )
            return redirect('payment_list')
    else:
        form = FeePaymentForm()
    
    context = {'form': form, 'title': 'ثبت پرداخت فیس'}
    return render(request, 'school_management/payment_form.html', context)


def payment_list(request):
    """View for listing payments with filtering, sorting, stats, and CSV export."""
    qs = FeePayment.objects.select_related('student')

    # Filters from GET
    search = request.GET.get('search', '').strip()
    class_filter = request.GET.get('class', '').strip()
    month = request.GET.get('month', '').strip()
    year = request.GET.get('year', '').strip()
    student_id = request.GET.get('student', '').strip()

    if search:
        qs = qs.filter(
            Q(student__name__icontains=search) |
            Q(student__student_id__icontains=search) |
            Q(student__father_name__icontains=search)
        )

    if class_filter:
        qs = qs.filter(student__class_name=class_filter)

    # Month/Year filter logic using month_year stored as YYYY-MM
    try:
        month_int = int(month) if month else None
    except ValueError:
        month_int = None
    try:
        year_int = int(year) if year else None
    except ValueError:
        year_int = None

    if year_int and month_int:
        qs = qs.filter(month_year=f"{year_int}-{month_int:02d}")
    elif year_int:
        qs = qs.filter(month_year__startswith=f"{year_int}-")
    elif month_int:
        qs = qs.filter(month_year__endswith=f"-{month_int:02d}")

    if student_id:
        qs = qs.filter(student_id=student_id)

    # Sorting
    sort = request.GET.get('sort', 'payment_date')
    sort_dir = request.GET.get('dir', 'desc')
    sort_map = {
        'payment_date': 'payment_date',
        'amount': 'amount',
    }
    sort_field = sort_map.get(sort, 'payment_date')
    if sort_dir == 'asc':
        qs = qs.order_by(sort_field, '-id')
    else:
        qs = qs.order_by(f'-{sort_field}', '-id')

    # Export CSV (Excel-friendly)
    if request.GET.get('export') == 'excel':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="payments.csv"'
        writer = csv.writer(response)
        writer.writerow(['تاریخ پرداخت', 'شاگرد', 'شماره شاگرد', 'صنف', 'مقدار', 'ماه/سال', 'روش پرداخت', 'یادداشت'])
        for p in qs:
            writer.writerow([
                p.payment_date.strftime('%Y/%m/%d'),
                p.student.name,
                p.student.student_id or '',
                p.student.class_name,
                str(p.amount),
                p.month_year,
                p.payment_method,
                (p.notes or '').replace('\n', ' ').strip(),
            ])
        return response

    # Statistics for current filtered queryset (before pagination)
    aggregate = qs.aggregate(
        total_amount=Sum('amount'),
        payments_count=Count('id'),
        unique_students=Count('student', distinct=True),
    )
    total_amount = aggregate['total_amount'] or Decimal('0.00')
    payments_count = aggregate['payments_count'] or 0
    unique_students = aggregate['unique_students'] or 0

    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter choice lists
    class_choices = list(
        Student.objects.values_list('class_name', 'class_name').distinct().order_by('class_name')
    )
    month_choices = [
        (1, 'حمل'), (2, 'ثور'), (3, 'جوزا'), (4, 'سرطان'),
        (5, 'اسد'), (6, 'سنبله'), (7, 'میزان'), (8, 'عقرب'),
        (9, 'قوس'), (10, 'جدی'), (11, 'دلو'), (12, 'حوت')
    ]
    available_years = list(range(1300, 1601))

    context = {
        'page_obj': page_obj,
        'payments': page_obj,
        # Stats
        'total_amount': total_amount,
        'payments_count': payments_count,
        'unique_students': unique_students,
        # Filters and choices
        'class_choices': class_choices,
        'month_choices': month_choices,
        'available_years': available_years,
        'students': Student.objects.filter(is_active=True).order_by('name'),
        'selected_student': student_id,
    }

    return render(request, 'school_management/payment_list.html', context)


def reports(request):
    """Comprehensive Reports view with filters, summaries, charts, and CSV export."""
    # Defaults based on current Jalali date
    j_now = jdatetime.date.today()
    default_year = j_now.year
    available_years = list(range(1300, 1601))

    # GET filters
    year = request.GET.get('year')
    month = request.GET.get('month')  # optional
    selected_class = request.GET.get('class')  # optional; template uses numbers 1..12

    # Validate year/month
    try:
        year = int(year) if year else default_year
    except ValueError:
        year = default_year
    try:
        month_int = int(month) if month else None
        if month_int is not None and (month_int < 1 or month_int > 12):
            month_int = None
    except ValueError:
        month_int = None

    # Map selected_class ("1".."12") to stored class_name strings
    class_map = {
        "1": "اول", "2": "دوم", "3": "سوم", "4": "چهارم",
        "5": "پنجم", "6": "ششم", "7": "هفتم", "8": "هشتم",
        "9": "نهم", "10": "دهم", "11": "یازدهم", "12": "دوازدهم",
    }
    class_name_filter = class_map.get(selected_class) if selected_class else None

    # Base queryset filtered by year/month and optional class
    qs = FeePayment.objects.select_related('student').filter(month_year__startswith=f"{year}-")
    if month_int:
        qs = qs.filter(month_year=f"{year}-{month_int:02d}")
    if class_name_filter:
        qs = qs.filter(student__class_name=class_name_filter)

    # Export CSV of detailed payments (filtered)
    if request.GET.get('export') == 'excel':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"report_{year}{'-'+str(month_int).zfill(2) if month_int else ''}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['سال', 'ماه', 'تاریخ پرداخت', 'شاگرد', 'شماره شاگرد', 'صنف', 'مقدار', 'ماه/سال', 'روش پرداخت', 'یادداشت'])
        for p in qs.order_by('-payment_date', '-id'):
            month_num = int(p.month_year.split('-')[1]) if p.month_year else 0
            writer.writerow([
                year,
                get_afghan_month_name(month_num),
                p.payment_date.strftime('%Y/%m/%d'),
                p.student.name,
                p.student.student_id or '',
                p.student.class_name,
                str(p.amount),
                p.month_year,
                p.payment_method,
                (p.notes or '').replace('\n', ' ').strip(),
            ])
        return response

    # Top-level totals for the filtered period
    totals = qs.aggregate(
        total_revenue=Sum('amount'),
        total_payments=Count('id'),
        paying_students=Count('student', distinct=True),
    )
    total_revenue = totals['total_revenue'] or Decimal('0.00')
    total_payments = totals['total_payments'] or 0
    paying_students = totals['paying_students'] or 0
    average_payment = (total_revenue / total_payments) if total_payments else Decimal('0.00')

    # Monthly summary across 12 months for selected year (respect class filter only)
    monthly_summary = []
    monthly_labels = []
    monthly_data = []
    for m in range(1, 13):
        month_qs = FeePayment.objects.select_related('student').filter(month_year=f"{year}-{m:02d}")
        if class_name_filter:
            month_qs = month_qs.filter(student__class_name=class_name_filter)
        agg = month_qs.aggregate(
            total_amount=Sum('amount'),
            payment_count=Count('id'),
            unique_students=Count('student', distinct=True),
        )
        total_amount = agg['total_amount'] or Decimal('0.00')
        payment_count = agg['payment_count'] or 0
        unique_stu = agg['unique_students'] or 0
        average_amount = (total_amount / payment_count) if payment_count else Decimal('0.00')
        monthly_summary.append({
            'month': m,
            'month_name': get_afghan_month_name(m),
            'total_amount': total_amount,
            'payment_count': payment_count,
            'unique_students': unique_stu,
            'average_amount': average_amount,
        })
        monthly_labels.append(get_afghan_month_name(m))
        monthly_data.append(float(total_amount))

    # Class-wise summary within the filtered period (year and optional month)
    classes = list(
        Student.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
    )
    class_summary = []
    class_labels = []
    class_data_series = []
    for cls in classes:
        if class_name_filter and cls != class_name_filter:
            continue
        class_qs = qs.filter(student__class_name=cls)
        agg = class_qs.aggregate(
            total_amount=Sum('amount'),
            payment_count=Count('id'),
        )
        total_amount = agg['total_amount'] or Decimal('0.00')
        payment_count = agg['payment_count'] or 0
        average_amount = (total_amount / payment_count) if payment_count else Decimal('0.00')
        student_count = Student.objects.filter(is_active=True, class_name=cls).count()
        class_summary.append({
            'class_name': cls,
            'student_count': student_count,
            'payment_count': payment_count,
            'total_amount': total_amount,
            'average_amount': average_amount,
        })
        class_labels.append(cls)
        class_data_series.append(float(total_amount))

    # Payment methods summary
    payment_methods_summary = []
    methods = (qs.values('payment_method')
                 .annotate(count=Count('id'), total=Sum('amount'))
                 .order_by('payment_method'))
    for row in methods:
        payment_methods_summary.append({
            'method': row['payment_method'],
            'count': row['count'] or 0,
            'total': row['total'] or Decimal('0.00'),
        })

    context = {
        'available_years': available_years,
        'selected_year': year,
        'selected_month': month_int or None,
        'selected_class': selected_class,

        # Top stats
        'total_revenue': total_revenue,
        'total_payments': total_payments,
        'paying_students': paying_students,
        'average_payment': average_payment,

        # Monthly and class summaries
        'monthly_summary': monthly_summary,
        'class_summary': class_summary,
        'payment_methods_summary': payment_methods_summary,

        # Charts
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'class_labels': class_labels,
        'class_data': class_data_series,
    }

    return render(request, 'school_management/reports.html', context)


@require_http_methods(["GET"])
def api_student_payments(request, student_id):
    """API endpoint for getting student payment history"""
    try:
        student = get_object_or_404(Student, pk=student_id)
        payments = student.payments.all().order_by('-payment_date')
        
        payments_data = []
        for payment in payments:
            payments_data.append({
                'id': payment.id,
                'amount': str(payment.amount),
                'month_year': payment.month_year,
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
                'notes': payment.notes or '',
            })
        
        return JsonResponse({
            'student_name': student.name,
            'student_id': student.student_id,
            'payments': payments_data,
            'total_payments': str(student.get_total_payments()),
            'payments_count': student.get_payments_count(),
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_report_data(request):
    """API endpoint for getting report data"""
    try:
        # Use local calendar defaults and validation
        year = int(request.GET.get('year', 1400))
        month = int(request.GET.get('month', 1))

        if year < 1300 or year > 1600:
            year = 1400
        if month < 1 or month > 12:
            month = 1
        
        monthly_summary = FeePayment.get_monthly_summary(year, month)
        class_data = list(FeePayment.get_class_wise_collections(year, month))
        yearly_data = list(FeePayment.get_yearly_summary(year))
        
        # Convert Decimal to string for JSON serialization
        monthly_summary['total_collected'] = str(monthly_summary['total_collected'])
        
        for item in class_data:
            item['class_total'] = str(item['class_total'])
        
        for item in yearly_data:
            item['monthly_total'] = str(item['monthly_total'])
        
        return JsonResponse({
            'monthly_summary': monthly_summary,
            'class_data': class_data,
            'yearly_data': yearly_data,
            'month_name': get_afghan_month_name(month),
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_afghan_month_name(month_number):
    """Convert month number to Afghan month name"""
    afghan_months = [
        'حمل', 'ثور', 'جوزا', 'سرطان', 'اسد', 'سنبله',
        'میزان', 'عقرب', 'قوس', 'جدی', 'دلو', 'حوت'
    ]
    
    if 1 <= month_number <= 12:
        return afghan_months[month_number - 1]
    return str(month_number)
