from django import forms
from .models import Device, Tag


class DeviceTagForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Device
        fields = ['tags']


class DeviceCredentialsForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = [
            "snmp_community",
            "ssh_username",
            "ssh_password",
            "roadblocks",
        ]
