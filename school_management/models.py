from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Student(models.Model):
    """Student model for managing student information"""
    student_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="شماره شاگرد",
        blank=True,
        null=True,
        editable=False,
    )
    name = models.CharField(
        max_length=255,
        verbose_name="نام شاگرد"
    )
    father_name = models.CharField(
        max_length=255,
        verbose_name="نام پدر"
    )
    class_name = models.CharField(
        max_length=100,
        verbose_name="صنف"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="تلفن"
    )
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="فیس ماهانه"
    )
    registration_date = models.DateField(
        default=timezone.now,
        verbose_name="تاریخ ثبت نام"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاریخ به روز رسانی"
    )

    class Meta:
        verbose_name = "شاگرد"
        verbose_name_plural = "شاگردان"
        ordering = ['name']

    def __str__(self):
        sid = self.student_id if self.student_id else "—"
        return f"{sid} - {self.name}"

    def get_total_payments(self):
        """Calculate total payments made by this student"""
        return self.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

    def get_payments_count(self):
        """Get number of payments made by this student"""
        return self.payments.count()

    def get_latest_payment(self):
        """Get the latest payment made by this student"""
        return self.payments.order_by('-payment_date').first()

    def save(self, *args, **kwargs):
        # On initial save, we need a primary key before generating student_id
        if not self.pk:
            super().save(*args, **kwargs)
            if not self.student_id:
                self.student_id = f"STD-{self.pk:06d}"
                super().save(update_fields=['student_id'])
        else:
            super().save(*args, **kwargs)


class FeePayment(models.Model):
    """Fee payment model for tracking student payments"""
    
    PAYMENT_METHODS = [
        ('نقدی', 'نقدی'),
        ('چک', 'چک'),
        ('انتقال بانکی', 'انتقال بانکی'),
    ]

    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='payments',
        verbose_name="شاگرد"
    )
    payment_date = models.DateField(
        default=timezone.now, 
        verbose_name="تاریخ پرداخت"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="مقدار"
    )
    month_year = models.CharField(
        max_length=7, 
        help_text="فرمت: YYYY-MM",
        verbose_name="ماه/سال"
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHODS, 
        default='نقدی',
        verbose_name="طریقه پرداخت"
    )
    notes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="یادداشت"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="تاریخ ایجاد"
    )

    class Meta:
        verbose_name = "پرداخت فیس"
        verbose_name_plural = "پرداخت‌های فیس"
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.student.name} - {self.amount} افغانی - {self.month_year}"

    @classmethod
    def get_monthly_summary(cls, year, month):
        """Get monthly payment summary"""
        month_year = f"{year}-{month:02d}"
        
        payments = cls.objects.filter(month_year=month_year)
        total_collected = payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        students_paid = payments.values('student').distinct().count()
        total_students = Student.objects.filter(is_active=True).count()
        students_unpaid = total_students - students_paid
        
        return {
            'total_collected': total_collected,
            'students_paid': students_paid,
            'total_students': total_students,
            'students_unpaid': students_unpaid,
            'month_year': month_year
        }

    @classmethod
    def get_class_wise_collections(cls, year, month):
        """Get class-wise collection data"""
        month_year = f"{year}-{month:02d}"
        
        from django.db.models import Sum, Count, Q
        
        class_data = Student.objects.filter(is_active=True).values('class_name').annotate(
            total_students=Count('id'),
            class_total=Sum(
                'payments__amount',
                filter=Q(payments__month_year=month_year)
            ),
            students_paid=Count(
                'payments__student',
                filter=Q(payments__month_year=month_year),
                distinct=True
            )
        ).order_by('class_name')
        
        # Convert None values to 0
        for item in class_data:
            item['class_total'] = item['class_total'] or Decimal('0.00')
            item['students_paid'] = item['students_paid'] or 0
            
        return class_data

    @classmethod
    def get_yearly_summary(cls, year):
        """Get Jalali yearly payment summary by month using month_year (YYYY-MM)."""
        from django.db.models import Sum, Count

        # Aggregate by month_year prefix matching the Jalali year
        records = cls.objects.filter(
            month_year__startswith=f"{year}-"
        ).values('month_year').annotate(
            monthly_total=Sum('amount'),
            payment_count=Count('id')
        )

        # Initialize all 12 months to zero to ensure chart completeness
        summary_map = {m: {'monthly_total': Decimal('0.00'), 'payment_count': 0} for m in range(1, 13)}

        for rec in records:
            try:
                month = int(rec['month_year'].split('-')[1])
                if 1 <= month <= 12:
                    summary_map[month] = {
                        'monthly_total': rec['monthly_total'] or Decimal('0.00'),
                        'payment_count': rec['payment_count'] or 0,
                    }
            except Exception:
                continue

        # Return as a list of dicts sorted by month
        return [
            {
                'month': f"{month:02d}",
                'monthly_total': summary_map[month]['monthly_total'],
                'payment_count': summary_map[month]['payment_count'],
            }
            for month in range(1, 13)
        ]
