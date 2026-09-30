"""
Django Admin Site Registration for waste_management models.
Provides full administrative management via Django's default /admin/ interface.
"""

from django.contrib import admin
from .models import UserProfile, Complaint, ComplaintUpdate, PickupRequest


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'address', 'is_admin_staff', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'address')
    list_filter = ('is_admin_staff', 'created_at')


class ComplaintUpdateInline(admin.TabularInline):
    model = ComplaintUpdate
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_id', 'user', 'issue_type', 'location', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'issue_type', 'created_at')
    search_fields = ('complaint_id', 'location', 'description', 'user__username', 'user__email')
    readonly_fields = ('complaint_id', 'created_at', 'updated_at', 'resolved_at')
    inlines = [ComplaintUpdateInline]


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ('pickup_id', 'user', 'waste_category', 'quantity', 'preferred_date', 'status', 'created_at')
    list_filter = ('status', 'waste_category', 'preferred_date')
    search_fields = ('pickup_id', 'pickup_address', 'user__username', 'user__email')
    readonly_fields = ('pickup_id', 'created_at', 'updated_at')


@admin.register(ComplaintUpdate)
class ComplaintUpdateAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'status', 'updated_by', 'created_at')
    list_filter = ('status', 'created_at')
