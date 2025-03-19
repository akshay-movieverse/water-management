from django.db import models

from admin_dashboard.models import SoftDeleteModel, Subunit, Unit

# Create your models here.
class Worker(SoftDeleteModel):
    name = models.CharField(max_length=255)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class DailyReading(models.Model):
    date = models.DateField()
    subunit = models.ForeignKey(Subunit, on_delete=models.CASCADE)
    
    amount_opening_reading = models.IntegerField(default=0)
    amount_closing_reading = models.IntegerField(null=True, blank=True)
    
    dispenser_opening_reading = models.IntegerField(default=0)
    dispenser_closing_reading = models.IntegerField(null=True, blank=True)

    def amount_rs(self):
        if self.amount_closing_reading:
            return self.amount_closing_reading - self.amount_opening_reading
        return 0

    def water_supply(self):
        if self.dispenser_closing_reading:
            return self.dispenser_closing_reading - self.dispenser_opening_reading
        return 0

class Attendance(models.Model):
    date = models.DateField()
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=True)

class Expense(models.Model):
    date = models.DateField()
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    CATEGORY_CHOICES = [
        ('pickup_diesel', 'Pickup Diesel'),
        ('intra_v30_diesel', 'Intra V30 Diesel'),
        ('ace_new_diesel', 'ACE New Diesel'),
        ('diesel', 'Diesel'),
        ('salary', 'Salary'),
        ('electricity', 'Electricity'),
        ('plant_expense', 'Plant Expense'),
        ('petrol', 'Petrol'),
        ('nagar_palika', 'Nagar Palika'),
        ('others', 'Others'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
