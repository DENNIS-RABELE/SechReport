from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import rotate_token
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from StudentsDashboard.models import Report, Message
from .forms import AdminMessageForm, ReportUpdateForm


def _no_cache(response):
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@csrf_protect
@ensure_csrf_cookie
def admin_login(request):
    next_url = request.POST.get('next') or request.GET.get('next') or ''

    # Opening login directly should end any existing admin session.
    if request.method == 'GET' and request.user.is_authenticated and request.user.is_staff and not next_url:
        logout(request)
    if request.method == 'GET':
        # Always issue a fresh token for this login page render.
        rotate_token(request)

    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            # End session when browser/app is closed.
            request.session.set_expiry(0)
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)
            return redirect('dashboard')
        error_message = 'Invalid credentials or unauthorized account.'

    response = render(
        request,
        'adminpanel1/login.html',
        {'error_message': error_message, 'next_url': next_url},
    )
    return _no_cache(response)


def admin_logout(request):
    logout(request)
    return redirect('home')


@staff_member_required(login_url='/adminpanel/login/')
def dashboard(request):
    reports = Report.objects.all().order_by('-created_at')
    response = render(request, 'adminpanel1/dashboard.html', {'reports': reports})
    return _no_cache(response)


def report_login_gate(request, report_id):
    report_url = reverse('report_detail', kwargs={'report_id': report_id})
    logout(request)
    return redirect(f"{reverse('admin_login')}?next={report_url}")


@staff_member_required(login_url='/adminpanel/login/')
def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    messages = report.messages.all()

    if request.method == 'POST':
        if 'update_report' in request.POST:
            update_form = ReportUpdateForm(request.POST, instance=report)
            form = AdminMessageForm()
            if update_form.is_valid():
                update_form.save()
                return redirect('report_detail', report_id=report.id)
        else:
            form = AdminMessageForm(request.POST)
            update_form = ReportUpdateForm(instance=report)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.report = report
                msg.sender_type = 'admin'
                msg.save()
                return redirect('report_detail', report_id=report.id)
    else:
        form = AdminMessageForm()
        update_form = ReportUpdateForm(instance=report)

    response = render(request, 'adminpanel1/report_detail.html', {
        'report': report,
        'messages': messages,
        'form': form,
        'update_form': update_form,
    })
    return _no_cache(response)
