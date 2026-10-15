from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    TYPE_CHOICES = [
        ('facture', 'Facture'),
        ('devis', 'Devis'),
        ('bon_livraison', 'Bon de livraison'),
    ]
    
    MODELE_CHOICES = [
        ('service', 'Prestation (Jours / Taux)'),
        ('produit', 'Vente / Produit (Quantité / Prix Unitaire)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES, default='facture')
    modele_facture = models.CharField(max_length=20, choices=MODELE_CHOICES, default='service')
    numero = models.CharField(max_length=50)
    initiateur = models.CharField(max_length=100, blank=True)
    client = models.CharField(max_length=100)
    objet = models.CharField(max_length=255, blank=True)
    
    taux_prelevement = models.FloatField(default=0.0)
    avance = models.FloatField(default=0.0)
    regule = models.FloatField(default=0.0)
    
    autre_option_label = models.CharField(max_length=100, blank=True)
    autre_option_montant = models.FloatField(default=0.0)
    
    date_creation = models.DateTimeField(auto_now_add=True)

from django.db import models

class LigneDocument(models.Model):
    document = models.ForeignKey('Document', related_name='lignes', on_delete=models.CASCADE)
    designation = models.CharField(max_length=255)
    
    # Pour le modèle Prestation
    periode = models.CharField(max_length=100, blank=True, null=True)
    nombre_jours = models.FloatField(blank=True, null=True, default=0)
    taux_journalier = models.FloatField(blank=True, null=True, default=0)
    
    # Pour le modèle Vente / Produit
    quantite = models.FloatField(blank=True, null=True, default=0)
    prix_unitaire = models.FloatField(blank=True, null=True, default=0)
    
    # Résultat calculé
    prix_total = models.FloatField(blank=True, null=True, default=0)

    def __str__(self):
        return f"{self.designation} - {self.prix_total}"