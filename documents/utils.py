import os
from django.conf import settings
from num2words import num2words
from pypdf import PdfReader, PdfWriter
import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}

def generer_pdf_document(document_id):
    from .models import Document
    doc_obj = Document.objects.get(id=document_id)

    temp_pdf = os.path.join(settings.MEDIA_ROOT, f"temp_{doc_obj.id}.pdf")
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    # Configuration du document ReportLab (Marges réduites pour tout remonter)
    doc = SimpleDocTemplate(
        temp_pdf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=30,
        bottomMargin=50
    )

    story = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    style_titre = ParagraphStyle(
        'TitreDoc',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#1F4E79'),
        alignment=1, # Centré
        spaceAfter=15
    )
    
    style_texte = ParagraphStyle(
        'TexteNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14
    )
    
    style_bold = ParagraphStyle(
        'TexteBold',
        parent=style_texte,
        fontName='Helvetica-Bold'
    )

    # 1. En-tête : Logo à gauche, Date à droite
    logo_path = os.path.join(settings.BASE_DIR, "templates", "docx", "logo_perso.png")
    date_doc = getattr(doc_obj, "date_creation", None)
    if date_doc:
        mois_nom = MOIS_FR.get(date_doc.month, "")
        date_formatted = f"{date_doc.day:02d} {mois_nom} {date_doc.year}"
    else:
        date_formatted = ""

    header_data = [
        [
            Paragraph(f'<img src="{logo_path}" width="120" height="50"/>' if os.path.exists(logo_path) else "<b>ATELIER MOBILE</b>", style_texte),
            Paragraph(f"<b>Date :</b> {date_formatted}", ParagraphStyle('RightDate', parent=style_texte, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[250, 285])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. Titre Principal Dynamique
    if hasattr(doc_obj, "get_type_document_display"):
        type_doc_str = doc_obj.get_type_document_display().upper()
    else:
        type_doc_str = str(getattr(doc_obj, "type_document", "FACTURE")).upper()

    if "DEVIS" in type_doc_str:
        titre_principal = f"DEVIS N° : {doc_obj.numero}"
    elif "LIVRAISON" in type_doc_str or "BON" in type_doc_str:
        titre_principal = f"BON DE LIVRAISON N° : {doc_obj.numero}"
    else:
        titre_principal = f"FACTURE N° : {doc_obj.numero}"

    story.append(Paragraph(titre_principal, style_titre))

    # 3. Informations Client Statiques & Objet
    client_obj = getattr(doc_obj, "client", None)
    client_nom = str(client_obj) if client_obj else ""
    client_nif = "315548R"
    client_bp = "129"
    client_ville = "Port-Gentil"

    client_text = (
        f"<b>Client :</b> {client_nom}<br/>"
        f"<b>NIF :</b> {client_nif}<br/>"
        f"<b>BP :</b> {client_bp}<br/>"
        f"<b>Ville :</b> {client_ville}<br/><br/>"
        f"<b>Objet :</b> {doc_obj.objet or ''}"
    )
    story.append(Paragraph(client_text, style_texte))
    story.append(Spacer(1, 15))

    # 4. Tableau des prestations / produits
    table_data = [["Désignation", "Quantité / Période", "Prix Unitaire / Taux", "Prix total"]]
    
    total_brut = 0
    modele_val = getattr(doc_obj, "modele_facture", "service")

    for ligne in doc_obj.lignes.all():
        qte = ligne.quantite or 0
        pu = ligne.prix_unitaire or 0
        total_ligne = ligne.prix_total or (qte * pu)
        total_brut += total_ligne
        
        qte_str = f"{qte:g}" if qte else (ligne.periode or "")
        pu_str = f"{pu:,.0f}".replace(",", " ") if pu else ""
        tot_str = f"{total_ligne:,.0f} FCFA".replace(",", " ")

        table_data.append([
            ligne.designation or "",
            qte_str,
            pu_str,
            tot_str
        ])

    # Ligne Montant TTC
    table_data.append(["MONTANT TTC", "", "", f"{total_brut:,.0f} FCFA".replace(",", " ")])

    # Options supplémentaires (avances, prélèvements, etc.)
    taux_p = doc_obj.taux_prelevement or 0
    if taux_p > 0:
        montant_p = (total_brut * taux_p) / 100
        table_data.append([f"Prélèvement ({taux_p}%)", "", "", f"-{montant_p:,.0f} FCFA".replace(",", " ")])
        total_brut -= montant_p

    val_avance = doc_obj.avance or 0
    if val_avance > 0:
        table_data.append(["Avance", "", "", f"-{val_avance:,.0f} FCFA".replace(",", " ")])
        total_brut -= val_avance

    val_regule = doc_obj.regule or 0
    if val_regule > 0:
        table_data.append(["Régule", "", "", f"-{val_regule:,.0f} FCFA".replace(",", " ")])
        total_brut -= val_regule

    net_a_payer = total_brut
    table_data.append(["NET À PAYER", "", "", f"{net_a_payer:,.0f} FCFA".replace(",", " ")])

    t = Table(table_data, colWidths=[180, 110, 110, 135])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F2F2F2')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # 5. Arrêté en lettres et Signature
    net_en_lettres = num2words(net_a_payer, lang="fr").capitalize() + " francs FCFA"
    story.append(Paragraph(f"<b>Arrêté la présente facture à la somme de :</b> {net_en_lettres}", style_texte))
    story.append(Spacer(1, 25))

    signature_data = [
        ["", Paragraph("<b>Le Responsable</b>", ParagraphStyle('Resp', parent=style_texte, alignment=2))]
    ]
    sig_table = Table(signature_data, colWidths=[300, 235])
    sig_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(sig_table)

    # Fonction pour dessiner le pied de page institutionnel sur chaque page
    def ajouter_pied_de_page(canvas_obj, doc_instance):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#505050"))
        
        footer_text = (
            "Atelier Mobile Mécanique Générale — Adresse : Zone du PK9 derrière le lycée Classique, BP 129\n"
            "Tél. : (+241) 62.70.55.62 / 77.93.98.66 — N° RCCM : GA-LBV-01-2020-A10-02435 — N° NIF : 315548 R\n"
            "UBA N° : 80901600302 — Capital : 2.000.000 F CFA — Site Internet : mobileateliermou.wixsite.com/website"
        )
        
        # Centrage du texte du pied de page en bas de page
        text_object = canvas_obj.beginText(40, 25)
        text_object.setFont("Helvetica", 7.5)
        for line in footer_text.split('\n'):
            text_object.textLine(line)
        canvas_obj.drawText(text_object)
        canvas_obj.restoreState()

    # Construction du PDF via ReportLab
    doc.build(story, onFirstPage=ajouter_pied_de_page, onLaterPages=ajouter_pied_de_page)

    # 6. Application du filigrane en arrière-plan derrière le tableau
    watermark_file = os.path.join(settings.BASE_DIR, "static", "watermark.png")
    if os.path.exists(watermark_file):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        img_width = 420
        img_height = 250
        x = (595.27 - img_width) / 2
        y = 280  # Positionné pile derrière le tableau
        can.drawImage(watermark_file, x, y, width=img_width, height=img_height, mask="auto", preserveAspectRatio=True)
        can.save()
        packet.seek(0)

        watermark_pdf = PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]

        original_pdf = PdfReader(temp_pdf)
        writer = PdfWriter()

        for page in original_pdf.pages:
            background = PdfReader(io.BytesIO(packet.getvalue())).pages[0]
            background.merge_page(page)
            writer.add_page(background)

        with open(temp_pdf, "wb") as f:
            writer.write(f)

    return temp_pdf