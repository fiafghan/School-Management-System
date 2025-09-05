from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Student, FeePayment
import re
import jdatetime
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget


class StudentForm(forms.ModelForm):
    """Form for adding/editing students"""
    
    class Meta:
        model = Student
        fields = [
            'name', 'father_name', 'class_name', 
            'phone', 'monthly_fee'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'نام شاگرد را وارد کنید'
            }),
            'father_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'نام پدر را وارد کنید'
            }),
            'class_name': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'شماره تلفن (اختیاری)'
            }),
            'monthly_fee': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'فیس ماهانه به افغانی',
                'step': '0.01'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define class choices
        self.fields['class_name'].widget.choices = [
            ('', 'صنف را انتخاب کنید'),
            ('اول', 'اول'),
            ('دوم', 'دوم'),
            ('سوم', 'سوم'),
            ('چهارم', 'چهارم'),
            ('پنجم', 'پنجم'),
            ('ششم', 'ششم'),
            ('هفتم', 'هفتم'),
            ('هشتم', 'هشتم'),
            ('نهم', 'نهم'),
            ('دهم', 'دهم'),
            ('یازدهم', 'یازدهم'),
            ('دوازدهم', 'دوازدهم'),
        ]

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone and not re.match(r'^[\d\s\-\+\(\)]+$', phone):
            raise ValidationError('شماره تلفن معتبر نیست.')
        return phone

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-set registration_date to today (Gregorian) based on Jalali today
        if not instance.registration_date:
            j_today = jdatetime.date.today()
            instance.registration_date = j_today.togregorian()
        if commit:
            instance.save()
        return instance


class FeePaymentForm(forms.ModelForm):
    """Form for recording fee payments with separate month and year selectors."""

    # Separate selectors to match the template
    MONTH_CHOICES = [
        (1, 'حمل'), (2, 'ثور'), (3, 'جوزا'), (4, 'سرطان'),
        (5, 'اسد'), (6, 'سنبله'), (7, 'میزان'), (8, 'عقرب'),
        (9, 'قوس'), (10, 'جدی'), (11, 'دلو'), (12, 'حوت')
    ]
    YEAR_CHOICES = [(y, str(y)) for y in range(1300, 1601)]

    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        label='ماه',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        label='سال',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )

    class Meta:
        model = FeePayment
        # Expose fields used by the template; month_year and payment_date are set in save()
        fields = ['student', 'amount', 'payment_method', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مقدار پرداخت به افغانی',
                'step': '0.01'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'یادداشت (اختیاری)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active students
        self.fields['student'].queryset = Student.objects.filter(is_active=True).order_by('name')

        # Initialize month/year from instance.month_year if available
        # Default to current Jalali month/year
        j_now = jdatetime.date.today()
        initial_month = j_now.month
        initial_year = j_now.year
        if self.instance and self.instance.pk and getattr(self.instance, 'month_year', None):
            try:
                y, m = self.instance.month_year.split('-')
                initial_year, initial_month = int(y), int(m)
            except Exception:
                pass

        # If form is unbound, set initial values
        if not self.is_bound:
            self.fields['month'].initial = initial_month
            self.fields['year'].initial = initial_year

    def clean(self):
        cleaned = super().clean()
        # Compose month_year from separate fields
        month = cleaned.get('month')
        year = cleaned.get('year')
        try:
            month_int = int(month)
            year_int = int(year)
        except (TypeError, ValueError):
            raise ValidationError('ماه و سال معتبر نیست.')

        if month_int < 1 or month_int > 12:
            raise ValidationError('ماه باید بین 1 تا 12 باشد.')

        if year_int < 1300 or year_int > 1600:
            raise ValidationError('سال باید بین 1300 تا 1600 باشد.')

        cleaned['month_year'] = f"{year_int}-{month_int:02d}"
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Ensure month_year is set from cleaned data
        month_year = self.cleaned_data.get('month_year')
        if month_year:
            instance.month_year = month_year
        # Auto-set payment_date to today (Gregorian) based on Jalali today
        if not instance.payment_date:
            j_today = jdatetime.date.today()
            instance.payment_date = j_today.togregorian()
        if commit:
            instance.save()
        return instance


class ReportFilterForm(forms.Form):
    """Form for filtering reports"""
    
    YEAR_CHOICES = [(year, str(year)) for year in range(1300, 1601)]
    MONTH_CHOICES = [
        (1, 'حمل'), (2, 'ثور'), (3, 'جوزا'), (4, 'سرطان'),
        (5, 'اسد'), (6, 'سنبله'), (7, 'میزان'), (8, 'عقرب'),
        (9, 'قوس'), (10, 'جدی'), (11, 'دلو'), (12, 'حوت')
    ]
    
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        initial=jdatetime.date.today().year,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='سال'
    )
    
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        initial=jdatetime.date.today().month,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline:none focus:ring-2 focus:ring-blue-500'
        }),
        label='ماه'
    )


class StudentSearchForm(forms.Form):
    """Form for searching students"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'جستجو بر اساس نام، شماره شاگرد یا نام پدر...'
        }),
        label='جستجو'
    )
    
    class_filter = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline:none focus:ring-2 focus:ring-blue-500'
        }),
        label='فیلتر بر اساس صنف'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get unique class names from database
        classes = Student.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
        class_choices = [('', 'همه صنف‌ها')] + [(cls, cls) for cls in classes if cls]
        self.fields['class_filter'].choices = class_choices
