import io
import os
import pythoncom
from django.conf import settings
from docx import Document as DocxDocument
from docx.shared import Pt
from docx2pdf import convert
from docxtpl import DocxTemplate
from num2words import num2words
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

MOIS_FR = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre",
}


def superposer_filigrane_pdf(pdf_in_path, image_path):
  """Superpose correctement le filigrane en arrière-plan sous le tableau pour chaque page du PDF."""
  if not os.path.exists(image_path):
    # Recherche alternative si non trouve dans static/
    alt_path = os.path.join(
        settings.BASE_DIR, "templates", "docx", "watermark.png"
    )
    if os.path.exists(alt_path):
      image_path = alt_path
    else:
      print(f"[WARNING] Filigrane introuvable au chemin : {image_path}")
      return

  # 1. Création du calque de filigrane A4
  packet = io.BytesIO()
  can = canvas.Canvas(packet, pagesize=A4)
  width, height = A4

  # Dimensions et centrage sur le tableau (y = 280)
  img_width = 420
  img_height = 250
  x = (width - img_width) / 2
  y = 280

  can.drawImage(
      image_path,
      x,
      y,
      width=img_width,
      height=img_height,
      mask="auto",
      preserveAspectRatio=True,
  )
  can.save()
  packet_bytes = packet.getvalue()

  original_pdf = PdfReader(pdf_in_path)
  writer = PdfWriter()

  # 2. Fusion : Le filigrane en dessous, la page du document au-dessus
  for page in original_pdf.pages:
    background = PdfReader(io.BytesIO(packet_bytes)).pages[0]
    background.merge_page(page)  # Superpose le texte par-dessus le filigrane
    writer.add_page(background)

  with open(pdf_in_path, "wb") as f:
    writer.write(f)


def generer_pdf_document(document_id):
  from .models import Document

  doc_obj = Document.objects.get(id=document_id)

  modele_val = getattr(doc_obj, "modele_facture", "service")
  is_modele_produit = modele_val == "produit"

  if is_modele_produit:
    template_name = "Facture_Vente_Atelier_Mobile.docx"
  else:
    template_name = "Facture_Atelier_Mobile.docx"

  template_path = os.path.join(
      settings.BASE_DIR, "templates", "docx", template_name
  )
  if not os.path.exists(template_path):
    template_path = os.path.join(
        settings.BASE_DIR,
        "templates",
        "docx",
        "Facture_Atelier_Mobile.docx",
    )

  doc = DocxTemplate(template_path)

  prestations = []
  total_brut = 0

  for ligne in doc_obj.lignes.all():
    qte = ligne.quantite or 0
    pu = ligne.prix_unitaire or 0

    prestations.append({
        "designation": ligne.designation or "",
        "periode": ligne.periode or "",
        "taux": (
            f"{ligne.taux_journalier:,.0f}".replace(",", " ")
            if ligne.taux_journalier
            else ""
        ),
        "quantite": f"{qte:g}" if qte else "",
        "prix_unitaire": f"{pu:,.0f}".replace(",", " ") if pu else "",
        "total": f"{ligne.prix_total:,.0f} FCFA".replace(",", " "),
    })
    total_brut += ligne.prix_total

  taux_p = doc_obj.taux_prelevement or 0
  montant_prelevement = (total_brut * taux_p) / 100 if taux_p > 0 else 0
  val_avance = doc_obj.avance or 0
  val_regule = doc_obj.regule or 0
  val_autre_montant = getattr(doc_obj, "autre_option_montant", 0) or 0
  val_autre_label = getattr(doc_obj, "autre_option_label", "") or ""

  net_a_payer = (
      total_brut
      - montant_prelevement
      - val_avance
      - val_regule
      - val_autre_montant
  )
  net_en_lettres = (
      num2words(net_a_payer, lang="fr").capitalize() + " francs FCFA"
  )

  initiateur_nom = (
      doc_obj.initiateur
      or doc_obj.user.get_full_name()
      or doc_obj.user.username
  )

  date_doc = getattr(doc_obj, "date_creation", None)
  if date_doc:
    mois_nom = MOIS_FR.get(date_doc.month, "")
    date_formatted = f"{date_doc.day:02d} {mois_nom} {date_doc.year}"
  else:
    date_formatted = ""

  if hasattr(doc_obj, "get_type_document_display"):
    type_doc_str = doc_obj.get_type_document_display().upper()
  else:
    type_doc_str = str(getattr(doc_obj, "type_document", "FACTURE")).upper()

  client_obj = getattr(doc_obj, "client", None)
  client_nom = str(client_obj) if client_obj else ""

  # Valeurs statiques NIF, BP, VILLE
  client_nif = (
      getattr(client_obj, "nif", None) or getattr(doc_obj, "client_nif", None)
  ) or "315548R"
  client_bp = (
      getattr(client_obj, "bp", None) or getattr(doc_obj, "client_bp", None)
  ) or "129"
  client_ville = (
      getattr(client_obj, "ville", None)
      or getattr(doc_obj, "client_ville", None)
  ) or "Port-Gentil"

  context = {
      "modele_facture": modele_val,
      "is_produit": is_modele_produit,
      "type_doc": type_doc_str,
      "numero_facture": doc_obj.numero,
      "date_facture": date_formatted,
      "initiateur": initiateur_nom.upper(),
      "client_nom": client_nom,
      "client_nif": client_nif,
      "client_bp": client_bp,
      "client_ville": client_ville,
      "objet": doc_obj.objet or "",
      "prestations": prestations,
      "montant_ttc": f"{total_brut:,.0f} FCFA".replace(",", " "),
      "has_prelevement": taux_p > 0,
      "taux_prelevement": taux_p,
      "prelevement": f"-{montant_prelevement:,.0f} FCFA".replace(",", " "),
      "has_avance": val_avance > 0,
      "avance": f"-{val_avance:,.0f} FCFA".replace(",", " "),
      "has_regule": val_regule > 0,
      "regule": f"-{val_regule:,.0f} FCFA".replace(",", " "),
      "has_autre_option": val_autre_montant > 0,
      "autre_option_label": val_autre_label,
      "autre_option_montant": (
          f"-{val_autre_montant:,.0f} FCFA".replace(",", " ")
      ),
      "net_a_payer": f"{net_a_payer:,.0f} FCFA".replace(",", " "),
      "net_en_lettres": net_en_lettres,
  }

  temp_docx = os.path.join(settings.MEDIA_ROOT, f"temp_{doc_obj.id}.docx")
  temp_pdf = os.path.join(settings.MEDIA_ROOT, f"temp_{doc_obj.id}.pdf")

  doc.render(context)
  doc.save(temp_docx)

  doc_generated = DocxDocument(temp_docx)
  for paragraph in doc_generated.paragraphs:
    for run in paragraph.runs:
      run.font.name = "Times New Roman"
      if not run.font.size:
        run.font.size = Pt(12)

  for table in doc_generated.tables:
    for row in table.rows:
      for cell in row.cells:
        for paragraph in cell.paragraphs:
          for run in paragraph.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)

  doc_generated.save(temp_docx)

  pythoncom.CoInitialize()
  try:
    convert(temp_docx, temp_pdf)
  finally:
    pythoncom.CoUninitialize()

  # Application du filigrane
  watermark_file = os.path.join(settings.BASE_DIR, "static", "watermark.png")
  superposer_filigrane_pdf(temp_pdf, watermark_file)

  return temp_pdf