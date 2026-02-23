import uuid
from django.db import models

class ReportCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Report(models.Model):
    STATUS_CHOICES = [
        ('Pending','Pending'),
        ('Under Review','Under Review'),
        ('Investigating','Investigating'),
        ('Resolved','Resolved'),
        ('Rejected','Rejected'),
    ]

    SEVERITY_CHOICES = [
        ('Low','Low'),
        ('Medium','Medium'),
        ('High','High'),
        ('Critical','Critical'),
    ]

    tracking_token = models.CharField(max_length=64, unique=True, editable=False)
    category = models.ForeignKey(ReportCategory, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    description = models.TextField()
    incident_date = models.DateField()
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_token:
            # Generate a short 8-character token and retry on collision.
            while True:
                token = uuid.uuid4().hex[:8].upper()
                if not Report.objects.filter(tracking_token=token).exists():
                    self.tracking_token = token
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Message(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=20)  # student/admin
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
