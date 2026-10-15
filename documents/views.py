import os
import pythoncom  # Nécessaire pour éviter l'erreur CoInitialize sous Windows
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import Document
from .forms import DocumentForm, LigneDocumentFormSet
from .utils import generer_pdf_document

@login_required
def liste_documents(request):
    documents = Document.objects.filter(user=request.user)

    search_query = request.GET.get('q', '').strip()
    type_doc = request.GET.get('type', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    if search_query:
        query_type = Q()
        search_lower = search_query.lower()
        if "facture" in search_lower:
            query_type |= Q(type_document='facture')
        if "devis" in search_lower:
            query_type |= Q(type_document='devis')
        if "bon" in search_lower or "livraison" in search_lower:
            query_type |= Q(type_document='bon_livraison')

        documents = documents.filter(
            Q(numero__icontains=search_query) |
            Q(client__icontains=search_query) |
            Q(objet__icontains=search_query) |
            query_type
        )

    if type_doc:
        documents = documents.filter(type_document=type_doc)

    if date_debut:
        documents = documents.filter(date_creation__gte=date_debut)
    if date_fin:
        documents = documents.filter(date_creation__lte=date_fin)

    documents = documents.order_by('-date_creation')

    return render(request, 'documents/liste_documents.html', {
        'documents': documents,
        'search_query': search_query,
        'type_doc': type_doc,
        'date_debut': date_debut,
        'date_fin': date_fin,
    })


@login_required
def creer_document(request):
    nom_initiateur = request.user.get_full_name() or request.user.username

    if request.method == 'POST':
        form = DocumentForm(request.POST)
        formset = LigneDocumentFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.initiateur = nom_initiateur
            
            # Récupération sécurisée du modèle de facture (service ou produit)
            document.modele_facture = request.POST.get('modele_facture', 'service')
            document.save()
            
            instances = formset.save(commit=False)
            for instance in instances:
                instance.document = document
                
                # Calcul de sécurité du prix_total selon le mode choisi
                if document.modele_facture == 'produit':
                    qte = instance.quantite or 0
                    pu = instance.prix_unitaire or 0
                    instance.prix_total = qte * pu
                else:
                    nb_j = instance.nombre_jours or 0
                    taux = instance.taux_journalier or 0
                    instance.prix_total = nb_j * taux

                instance.save()
            
            formset.save_m2m()

            # Génération directe du fichier PDF
            generer_pdf_document(document.id)

            return redirect('dashboard_index')
        else:
            # Traçabilité des erreurs dans la console terminal si la validation échoue
            print("--- ERREURS DU FORMULAIRE PRINCIPAL ---", form.errors)
            print("--- ERREURS DU FORMSET (LIGNES) ---", formset.errors)
    else:
        form = DocumentForm(initial={'initiateur': nom_initiateur})
        formset = LigneDocumentFormSet()
    
    return render(request, 'documents/creer_document.html', {
        'form': form, 
        'formset': formset,
        'nom_initiateur': nom_initiateur
    })


@login_required
def apercu_pdf(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    pdf_path = generer_pdf_document(document.id)
    
    if os.path.exists(pdf_path):
        return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', filename=f"document_{document.numero}.pdf")
    else:
        raise Http404("Le fichier PDF n'a pas pu être généré.")