from django.shortcuts import render, redirect, get_object_or_404
from .models import Report, ReportCategory
from .forms import ReportForm, TrackForm, MessageForm


def home(request):
    return render(request, 'home.html')


def submit_report(request):
    success = False
    tracking_token = None
    error_message = "Please correct the highlighted fields and submit again."

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            if not report.category_id:
                default_category, _ = ReportCategory.objects.get_or_create(
                    name='General',
                    defaults={'description': 'Default category for uncategorized reports.'}
                )
                report.category = default_category

            report.save()
            form = ReportForm()
            success = True
            tracking_token = report.tracking_token
        elif 'incident_date' in form.errors:
            error_message = (
                "Please correct the highlighted fields and submit again. "
                "date format is 01 January 1996."
            )
    else:
        form = ReportForm()

    return render(request, 'students/report_form.html', {
        'form': form,
        'success': success,
        'tracking_token': tracking_token,
        'error_message': error_message,
    })


def track_report(request):
    if request.method == 'POST':
        form = TrackForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['tracking_token'].strip()
            report = Report.objects.filter(tracking_token__iexact=token).first()
            if report:
                return redirect('conversation', token=report.tracking_token)
            form.add_error('tracking_token', 'Invalid tracking token. Please check and try again.')
    else:
        form = TrackForm()
    return render(request, 'students/track_report.html', {'form': form})


def conversation(request, token):
    report = get_object_or_404(Report, tracking_token__iexact=token)
    messages = report.messages.all().order_by('created_at')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.report = report
            msg.sender_type = 'student'
            msg.save()
            return redirect('conversation', token=token)
    else:
        form = MessageForm()

    return render(request, 'students/conversation.html', {
        'report': report,
        'messages': messages,
        'form': form
    })
