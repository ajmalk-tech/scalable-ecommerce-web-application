from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomerRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=70,
        widget=forms.TextInput(
            attrs={"placeholder": "Enter Username", "class": "form-control"}
        ),
        label="Enter Username",
    )
    email_id = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"placeholder": "Enter Email Address", "class": "form-control"}
        ),
        label="Enter Email Address",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Enter Password", "class": "form-control"}
        ),
        label="Enter Password",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Confirm Password", "class": "form-control"}
        ),
        label="Confirm Password",
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "this username is already taken", code="duplicate_username"
            )

        return username

    def clean_email_id(self):
        email_id = self.cleaned_data.get("email_id")

        if User.objects.filter(email=email_id).exists():
            raise forms.ValidationError("This email address is already registered")
        return email_id

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Password do not match", code="password_mismatch")

        return cleaned_data


class CustomerLoginForm(forms.Form):
    username = forms.CharField(
        max_length=70,
        widget=forms.TextInput(
            attrs={"placeholder": "Enter Username", "class": "form-control"}
        ),
        label="Enter Username",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Enter Password", "class": "form-control"}
        ),
        label="Enter Password",
    )
