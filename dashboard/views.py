from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from documents.models import Document, LigneDocument

@login_required
def dashboard_index(request):
    user_docs = Document.objects.filter(user=request.user)
    
    # Prise en compte de 'bon_livraison' ou 'bl' selon ce qui est stocké
    nb_factures = user_docs.filter(type_document='facture').count()
    nb_devis = user_docs.filter(type_document='devis').count()
    nb_bl = user_docs.filter(type_document__in=['bon_livraison', 'bl', 'bon de livraison']).count()
    
    # Calcul du chiffre d'affaires cumulé sur les factures
    facture_ids = user_docs.filter(type_document='facture').values_list('id', flat=True)
    ca_total = LigneDocument.objects.filter(document_id__in=facture_ids).aggregate(Sum('prix_total'))['prix_total__sum'] or 0

    context = {
        'nb_factures': nb_factures,
        'nb_devis': nb_devis,
        'nb_bl': nb_bl,
        'ca_total': ca_total,
        'derniers_documents': user_docs.order_by('-date_creation')[:5]
    }
    return render(request, 'dashboard/index.html', context)