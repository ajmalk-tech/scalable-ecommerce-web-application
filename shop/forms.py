from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from product.models import Product

User = get_user_model()


class ShopRegistrationForm(forms.Form):
    shop_name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(
            attrs={"placeholder": "Enter Shop Name", "class": "form-control"}
        ),
        label="Enter Shop Name",
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

    def clean_shop_name(self):
        shop_name = self.cleaned_data.get("shop_name")

        if User.objects.filter(first_name=shop_name).exists():
            raise forms.ValidationError(
                "This shop name is already taken", code="duplicate_shop_name"
            )

        return shop_name

    def clean_email_id(self):
        email_id = self.cleaned_data.get("email_id")

        if User.objects.filter(email=email_id).exists():
            raise forms.ValidationError(
                "This email address is already registered", code="duplicate_email_id"
            )

        return email_id

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Password do not match", code="password_mismatch")

        return cleaned_data


class ShopLoginForm(forms.Form):
    shop_id = forms.CharField(
        max_length=4,
        widget=forms.TextInput(
            attrs={"placeholder": "Enter Shop ID", "class": "form-control"}
        ),
        label="Enter Shop ID",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Enter Password", "class": "form-control"}
        ),
        label="Enter Password",
    )


class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "description", "price", "stock", "image"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-input"}),
            "name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Product name"}
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }
