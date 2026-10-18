from django import forms
from django.contrib.auth.models import User

from catalog.models import (
    ACCESS_LENGTH_CHOICES,
    CourseProduct,
    MediaAsset,
    Package,
    PricingTier,
    ProductKind,
    UserAccessEntitlement,
)
from catalog.schemas import parse_bundle_config_payload, parse_pricing_tier_payload


class CourseProductForm(forms.ModelForm):
    bundle_access_duration_months = forms.IntegerField(
        required=False,
        min_value=0,
        help_text='Optional. Saved as days (months × 30) when days is left blank.',
    )

    class Meta:
        model = CourseProduct
        fields = (
            'kind',
            'title',
            'slug',
            'description',
            'is_active',
            'currency',
            'linked_course',
            'bundle_enabled',
            'bundle_title',
            'bundle_price',
            'bundle_access_duration_days',
            'expected_package_count',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['bundle_access_duration_months'].initial = self.instance.bundle_access_duration_months

    def clean(self):
        cleaned = super().clean()
        days = cleaned.get('bundle_access_duration_days')
        months = cleaned.get('bundle_access_duration_months')
        if not days and months:
            cleaned['bundle_access_duration_days'] = months * 30
        kind = cleaned.get('kind')
        if kind == ProductKind.PHYSIO_PACKAGES:
            parse_bundle_config_payload({
                'bundle_enabled': cleaned.get('bundle_enabled'),
                'bundle_title': cleaned.get('bundle_title') or 'All 15 Packages',
                'bundle_price': cleaned.get('bundle_price') or 0,
                'access_duration_days': cleaned.get('bundle_access_duration_days') or 0,
                'expected_package_count': cleaned.get('expected_package_count') or 15,
            })
        return cleaned


class PricingTierForm(forms.ModelForm):
    access_duration_months = forms.IntegerField(
        required=False,
        min_value=0,
        help_text='Optional shortcut. 1 month = 30 days.',
    )

    class Meta:
        model = PricingTier
        fields = (
            'name',
            'video_count',
            'price',
            'access_duration_days',
            'discount_percent',
            'is_active',
            'display_order',
            'stripe_price_id',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['access_duration_months'].initial = self.instance.access_duration_months

    def clean(self):
        cleaned = super().clean()
        payload = {
            'name': cleaned.get('name') or '',
            'video_count': cleaned.get('video_count') or 1,
            'price': cleaned.get('price') or 0,
            'access_duration_days': cleaned.get('access_duration_days'),
            'access_duration_months': cleaned.get('access_duration_months'),
            'discount_percent': cleaned.get('discount_percent') or 0,
            'is_active': cleaned.get('is_active', True),
            'display_order': cleaned.get('display_order') or 0,
            'stripe_price_id': cleaned.get('stripe_price_id') or '',
        }
        parsed = parse_pricing_tier_payload(payload)
        cleaned['access_duration_days'] = parsed.access_duration_days
        cleaned['discount_percent'] = parsed.discount_percent
        cleaned['price'] = parsed.price
        return cleaned


class PackageForm(forms.ModelForm):
    access_duration_months = forms.IntegerField(required=False, min_value=0)

    class Meta:
        model = Package
        fields = (
            'product',
            'title',
            'slug',
            'description',
            'chapter_number',
            'individual_price',
            'cover',
            'access_duration_days',
            'is_active',
            'display_order',
        )

    def clean(self):
        cleaned = super().clean()
        days = cleaned.get('access_duration_days')
        months = cleaned.get('access_duration_months')
        if not days and months:
            cleaned['access_duration_days'] = months * 30
        return cleaned


class MediaAssetForm(forms.ModelForm):
    class Meta:
        model = MediaAsset
        fields = (
            'product',
            'package',
            'session',
            'title',
            'description',
            'video_url',
            'video_file',
            'cover',
            'duration_seconds',
            'order',
            'is_active',
            'allowed_tiers',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product = None
        if self.instance and self.instance.product_id:
            product = self.instance.product
        elif self.data.get('product'):
            product = CourseProduct.objects.filter(pk=self.data.get('product')).first()
        if product:
            self.fields['package'].queryset = product.packages.all()
            self.fields['allowed_tiers'].queryset = product.pricing_tiers.all()
            if product.linked_course_id:
                self.fields['session'].queryset = product.linked_course.sessions.all()


class EntitlementGrantForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.order_by('email', 'username'))
    access_length = forms.TypedChoiceField(
        choices=[('', 'Keep current expiry')] + [(str(days), label) for days, label in ACCESS_LENGTH_CHOICES],
        required=False,
        coerce=lambda value: '' if value in (None, '') else int(value),
        empty_value='',
        help_text='Set how long this purchase stays open: 1, 3, or 6 months, or lifetime.',
    )

    class Meta:
        model = UserAccessEntitlement
        fields = (
            'user',
            'product',
            'pricing_tier',
            'package',
            'scope',
            'media_assets',
            'started_at',
            'expires_at',
            'is_active',
            'notes',
        )

    def save(self, commit=True):
        obj = super().save(commit=False)
        length = self.cleaned_data.get('access_length')
        if length != '' and length is not None:
            from django.utils import timezone
            started = obj.started_at or timezone.now()
            obj.started_at = started
            obj.expires_at = UserAccessEntitlement.compute_expiry(started, int(length))
        if commit:
            obj.save()
            self.save_m2m()
        return obj
