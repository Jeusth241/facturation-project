from django import forms
from django.forms import inlineformset_factory
from .models import Document, LigneDocument

class DocumentForm(forms.ModelForm):
    autre_option_label = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Remise / Pénalité'})
    )
    autre_option_montant = forms.FloatField(
        required=False, 
        initial=0.0, 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )

    class Meta:
        model = Document
        fields = ['type_document', 'numero', 'initiateur', 'client', 'objet', 'taux_prelevement', 'avance', 'regule']
        widgets = {
            'type_document': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'initiateur': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.TextInput(attrs={'class': 'form-control'}),
            'objet': forms.TextInput(attrs={'class': 'form-control'}),
            'taux_prelevement': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'avance': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'regule': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
        }

class LigneDocumentForm(forms.ModelForm):
    class Meta:
        model = LigneDocument
        fields = [
            'designation', 
            'periode', 
            'nombre_jours', 
            'taux_journalier', 
            'quantite', 
            'prix_unitaire', 
            'prix_total'
        ]
        widgets = {
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'periode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: 01 au 05 Janv'}),
            'nombre_jours': forms.NumberInput(attrs={'class': 'form-control input-nb-jours', 'placeholder': 'ex: 5', 'step': 'any'}),
            'taux_journalier': forms.NumberInput(attrs={'class': 'form-control input-taux', 'placeholder': '18000', 'step': 'any'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control input-qte', 'placeholder': '1', 'step': 'any'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control input-pu', 'placeholder': '15000', 'step': 'any'}),
            'prix_total': forms.NumberInput(attrs={'class': 'form-control input-total bg-light', 'readonly': 'readonly', 'step': 'any'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre tous les champs sauf 'designation' optionnels pour ne pas bloquer la validation
        self.fields['designation'].required = True
        self.fields['periode'].required = False
        self.fields['nombre_jours'].required = False
        self.fields['taux_journalier'].required = False
        self.fields['quantite'].required = False
        self.fields['prix_unitaire'].required = False
        self.fields['prix_total'].required = False


LigneDocumentFormSet = inlineformset_factory(
    Document,
    LigneDocument,
    form=LigneDocumentForm,
    extra=1,
    can_delete=True
)