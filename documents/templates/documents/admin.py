from django.contrib import admin
from models import Document, LigneDocument  # Ajoutez vos autres modèles si nécessaire

admin.site.register(Document)
admin.site.register(LigneDocument)