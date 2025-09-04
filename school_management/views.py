from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
import jdatetime
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
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
    """View for listing payments"""
    payments = FeePayment.objects.select_related('student').order_by('-payment_date')
    
    # Filter by month/year if provided
    month_year = request.GET.get('month_year')
    if month_year:
        payments = payments.filter(month_year=month_year)
    
    # Filter by student if provided
    student_id = request.GET.get('student')
    if student_id:
        payments = payments.filter(student_id=student_id)
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique month/years for filter
    month_years = FeePayment.objects.values_list('month_year', flat=True).distinct().order_by('-month_year')
    
    context = {
        'page_obj': page_obj,
        'payments': page_obj,
        'month_years': month_years,
        'selected_month_year': month_year,
        'students': Student.objects.filter(is_active=True).order_by('name'),
        'selected_student': student_id,
    }
    
    return render(request, 'school_management/payment_list.html', context)


def reports(request):
    """View for generating reports"""
    form = ReportFilterForm(request.GET or None)
    # Always provide Afghan year list and sensible defaults
    available_years = list(range(1300, 1601))
    context = {
        'form': form,
        'available_years': available_years,
        'selected_year': 1400,
        'selected_month': 1,
    }
    
    if form and form.is_valid():
        year = int(form.cleaned_data['year'])
        month = int(form.cleaned_data['month'])
        
        # Get monthly summary
        monthly_summary = FeePayment.get_monthly_summary(year, month)
        
        # Get class-wise collections
        class_data = FeePayment.get_class_wise_collections(year, month)
        
        # Get yearly data for charts
        yearly_data = FeePayment.get_yearly_summary(year)
        
        context.update({
            'monthly_summary': monthly_summary,
            'class_data': class_data,
            'yearly_data': yearly_data,
            'selected_year': year,
            'selected_month': month,
            'selected_month_name': get_afghan_month_name(month),
            'available_years': available_years,
        })
    
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
