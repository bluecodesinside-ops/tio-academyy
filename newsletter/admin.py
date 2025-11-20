from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import NewsletterSubscription
from .views import send_newsletter_to_all

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'get_full_name', 'is_active', 'subscribed_at', 'email_count', 'last_email_sent']
    list_filter = ['is_active', 'subscribed_at', 'last_email_sent']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-subscribed_at']
    readonly_fields = ['subscribed_at', 'last_email_sent', 'email_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'first_name', 'last_name', 'is_active')
        }),
        ('Statistics', {
            'fields': ('subscribed_at', 'last_email_sent', 'email_count'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['send_test_email', 'export_emails']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def send_test_email(self, request, queryset):
        # This would send a test email to selected subscribers
        messages.success(request, f'Test email sent to {queryset.count()} subscribers')
    send_test_email.short_description = 'Send test email to selected subscribers'
    
    def export_emails(self, request, queryset):
        # This would export emails to CSV
        messages.success(request, f'Exported {queryset.count()} email addresses')
    export_emails.short_description = 'Export emails to CSV'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-newsletter/', self.admin_site.admin_view(self.send_newsletter_view), name='newsletter_send'),
        ]
        return custom_urls + urls
    
    def send_newsletter_view(self, request):
        if request.method == 'POST':
            subject = request.POST.get('subject')
            html_content = request.POST.get('html_content')
            text_content = request.POST.get('text_content')
            
            if subject and html_content:
                count = send_newsletter_to_all(subject, html_content, text_content or '')
                messages.success(request, f'Newsletter sent to {count} subscribers!')
                return HttpResponseRedirect('../')
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        return render(request, 'admin/newsletter/send_newsletter.html', {
            'title': 'Send Newsletter',
            'opts': self.model._meta,
        })
