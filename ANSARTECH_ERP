#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   ANSARTECH ERP PRO V2.2 - VERSION CORRIGÉE                  ║
║           Gestion Intégrée: Stock, Ventes, Factures, Comptabilité            ║
║     Solution Professionnelle avec PDF Factures & Stock Professionnel          ║
║                         VERSION OPTIMISÉE 2025                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

Corrections apportées :
  - Treeview : suppression de l'option invalide `heading=` dans tree.column()
    (provoquait un TclError au démarrage)
  - clear_form : réinitialise aussi TVA, Stock Min et Stock Max
  - Fenêtre de modification : tous les champs sont modifiables et enregistrés
    (référence, nom, catégorie, fournisseur, quantité, prix, TVA, min, max,
    description), avec validation des valeurs
  - Double-clic sur une zone vide du tableau : plus d'IndexError
  - Rapport de stock : gestion des quantités/prix/catégories vides (NULL)
  - Suppression d'un produit : ses mouvements de stock sont aussi supprimés
  - Doublon du shebang supprimé

Nouveautés :
  - Onglet Factures complet : client, articles depuis le stock, calcul HT/TVA/TTC,
    numérotation automatique (F-AAAAMM-0001), sortie de stock automatique,
    export PDF, statut payé, annulation avec remise en stock
  - Historique des mouvements de stock (bouton MOUVEMENTS STOCK)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from typing import Dict

# ════════════════════════════════════════════════════════════════════════════
# THÈME MODERNE PROFESSIONNEL
# ════════════════════════════════════════════════════════════════════════════

class ModernTheme:
    PRIMARY_DARK = "#0D47A1"
    PRIMARY = "#1976D2"
    PRIMARY_LIGHT = "#42A5F5"
    ACCENT = "#FF6B35"
    SUCCESS = "#28A745"
    WARNING = "#FFC107"
    DANGER = "#DC3545"
    INFO = "#17A2B8"

    BG_DARK = "#0F1419"
    BG_LIGHT = "#F8F9FA"
    CARD_BG = "#FFFFFF"
    BORDER = "#E0E0E0"
    TEXT_DARK = "#212121"
    TEXT_LIGHT = "#6C757D"
    TEXT_WHITE = "#FFFFFF"
    HOVER_BG = "#F5F5F5"

# ════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ════════════════════════════════════════════════════════════════════════════

class Database:
    """Gestionnaire de base de données SQLite"""

    def __init__(self, db_path: str = "ansartech_erp_v2.db"):
        self.db_path = db_path
        self.init_db()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_conn()
        cursor = conn.cursor()

        # Table des entreprises
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                country TEXT,
                phone TEXT,
                email TEXT,
                siret TEXT,
                vat_number TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table des utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'admin',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table des produits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                reference TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                unit_price REAL NOT NULL DEFAULT 0,
                vat_rate REAL DEFAULT 18,
                stock_quantity INTEGER DEFAULT 0,
                stock_min INTEGER DEFAULT 5,
                stock_max INTEGER DEFAULT 100,
                category TEXT,
                supplier TEXT,
                last_restock_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table des mouvements de stock
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                movement_type TEXT,
                quantity INTEGER,
                reason TEXT,
                reference_doc TEXT,
                created_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

        # Table des clients
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                country TEXT,
                tax_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table des factures
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_address TEXT,
                customer_email TEXT,
                customer_phone TEXT,
                total_ht REAL DEFAULT 0,
                total_vat REAL DEFAULT 0,
                total_ttc REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'pending',
                invoice_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_date DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        """)

        # Table des lignes de facture
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_lines (
                id INTEGER PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price_ht REAL NOT NULL,
                vat_rate REAL NOT NULL,
                line_total_ht REAL NOT NULL,
                line_vat REAL NOT NULL,
                line_total_ttc REAL NOT NULL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

        conn.commit()
        conn.close()

# ════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR PDF
# ════════════════════════════════════════════════════════════════════════════

class InvoicePDFGenerator:
    """Générateur de factures PDF professionnel avec gestion d'erreurs robuste"""

    @staticmethod
    def generate_invoice_pdf(filename: str, invoice_data: Dict, company_info: Dict):
        """
        Génère une facture PDF complète.

        Args:
            filename: Chemin du fichier PDF à créer
            invoice_data: Dict contenant les données de facture
            company_info: Dict contenant les infos entreprise

        Returns:
            True si succès

        Raises:
            Exception avec message d'erreur détaillé
        """
        try:
            # Validation des données
            if not filename:
                raise ValueError("Le nom du fichier est requis")
            if not invoice_data or not invoice_data.get('invoice_number'):
                raise ValueError("Les données de facture sont incomplètes")
            if not invoice_data.get('customer_name'):
                raise ValueError("Le nom du client est requis")

            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            story = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor("#1976D2"),
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=11,
                textColor=colors.HexColor("#0D47A1"),
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )

            normal_style = styles['Normal']

            # ===== EN-TÊTE =====
            story.append(Paragraph("FACTURE", title_style))
            story.append(Spacer(1, 0.2*inch))

            company_text = f"""
<b>{company_info.get('name', 'ANSARTECH')}</b><br/>
{company_info.get('address', '')}<br/>
{company_info.get('city', '')}<br/>
Tél: {company_info.get('phone', '')}<br/>
Email: {company_info.get('email', '')}
            """

            client_text = f"""
<b>CLIENT:</b><br/>
<b>{invoice_data.get('customer_name', 'Client')}</b><br/>
{invoice_data.get('customer_address', '')}<br/>
{invoice_data.get('customer_email', '')}<br/>
{invoice_data.get('customer_phone', '')}
            """

            info_data = [
                [Paragraph(company_text, normal_style), Paragraph(client_text, normal_style)]
            ]
            info_table = Table(info_data, colWidths=[3*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                ('INNERGRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.3*inch))

            # Détails facture
            story.append(Paragraph("DÉTAILS FACTURE", heading_style))

            details_data = [
                ['Numéro:', str(invoice_data.get('invoice_number', 'N/A')), 'Date:', str(invoice_data.get('invoice_date', '') or '')],
                ['Statut:', str(invoice_data.get('payment_status', 'pending')).upper(), 'Échéance:', str(invoice_data.get('due_date', '') or '')]
            ]

            details_table = Table(details_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
            ]))
            story.append(details_table)
            story.append(Spacer(1, 0.2*inch))

            # ===== LIGNES DE FACTURE =====
            story.append(Paragraph("ARTICLES", heading_style))

            lines_data = [['Description', 'Qté', 'P.U. HT', 'TVA', 'Total HT']]

            for line in invoice_data.get('lines', []):
                try:
                    qty = float(line.get('quantity', 0) or 0)
                    price = float(line.get('unit_price_ht', 0) or 0)
                    vat = float(line.get('vat_rate', 0) or 0)
                    total = float(line.get('line_total_ht', 0) or 0)

                    lines_data.append([
                        str(line.get('description', '')),
                        f"{qty:.2f}",
                        f"{price:,.0f}",
                        f"{vat:.0f}%",
                        f"{total:,.0f}"
                    ])
                except (ValueError, TypeError):
                    continue

            if len(lines_data) == 1:
                lines_data.append(['', '0', '0', '0%', '0'])

            lines_table = Table(lines_data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 0.7*inch, 1.2*inch])
            lines_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1976D2")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")])
            ]))
            story.append(lines_table)
            story.append(Spacer(1, 0.2*inch))

            # ===== RÉSUMÉ FINANCIER =====
            ht = float(invoice_data.get('total_ht', 0) or 0)
            tva = float(invoice_data.get('total_vat', 0) or 0)
            ttc = float(invoice_data.get('total_ttc', 0) or 0)

            summary_data = [
                ['Total HT:', f"{ht:,.0f} GNF"],
                ['TVA:', f"{tva:,.0f} GNF"],
                ['TOTAL TTC:', f"{ttc:,.0f} GNF"]
            ]

            summary_table = Table(summary_data, colWidths=[3.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 2), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 1), 10),
                ('FONTSIZE', (0, 2), (-1, 2), 12),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#E3F2FD")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.2*inch))

            # Notes
            if invoice_data.get('notes'):
                story.append(Paragraph("NOTES", heading_style))
                notes = str(invoice_data['notes']).replace('\n', '<br/>')
                story.append(Paragraph(notes, normal_style))

            # Pied de page
            story.append(Spacer(1, 0.3*inch))
            footer_text = "Merci pour votre confiance | Facture générée le " + datetime.now().strftime("%d/%m/%Y %H:%M")
            story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

            doc.build(story)
            return True

        except FileNotFoundError as e:
            raise Exception(f"Erreur d'accès fichier: {str(e)}")
        except PermissionError as e:
            raise Exception(f"Permissions insuffisantes: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur génération PDF: {str(e)}")

# ════════════════════════════════════════════════════════════════════════════
# BOUTON MODERNE
# ════════════════════════════════════════════════════════════════════════════

class ModernButton(tk.Button):
    def __init__(self, parent, text, command=None, style_type="primary", **kwargs):
        colors_map = {
            "primary": (ModernTheme.PRIMARY, ModernTheme.TEXT_WHITE),
            "accent": (ModernTheme.ACCENT, ModernTheme.TEXT_WHITE),
            "success": (ModernTheme.SUCCESS, ModernTheme.TEXT_WHITE),
            "danger": (ModernTheme.DANGER, ModernTheme.TEXT_WHITE),
            "info": (ModernTheme.INFO, ModernTheme.TEXT_WHITE),
        }
        bg_color, fg_color = colors_map.get(style_type, colors_map["primary"])

        super().__init__(
            parent, text=text, command=command,
            bg=bg_color, fg=fg_color,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, padx=15, pady=8,
            cursor="hand2", **kwargs
        )

        self.bind("<Enter>", lambda e: self.config(relief=tk.RAISED))
        self.bind("<Leave>", lambda e: self.config(relief=tk.FLAT))

# ════════════════════════════════════════════════════════════════════════════
# MODULE GESTION DU STOCK
# ════════════════════════════════════════════════════════════════════════════

class StockManagementModule:
    """Module de gestion du stock professionnel"""

    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.selected_product_id = None
        self.build_ui()

    def build_ui(self):
        """Construit l'interface de gestion du stock"""
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== SECTION AJOUT PRODUIT =====
        add_product_frame = ttk.LabelFrame(main_frame, text="➕ AJOUTER UN PRODUIT", padding=10)
        add_product_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(add_product_frame, text="Référence:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ref_entry = ttk.Entry(add_product_frame, width=25)
        self.ref_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_product_frame, text="Nom du Produit:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.name_entry = ttk.Entry(add_product_frame, width=25)
        self.name_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(add_product_frame, text="Catégorie:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.category_entry = ttk.Entry(add_product_frame, width=25)
        self.category_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(add_product_frame, text="Fournisseur:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.supplier_entry = ttk.Entry(add_product_frame, width=25)
        self.supplier_entry.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(add_product_frame, text="Quantité Stock:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.quantity_entry = ttk.Entry(add_product_frame, width=15)
        self.quantity_entry.insert(0, "0")
        self.quantity_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(add_product_frame, text="Prix Unitaire (GNF):").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.price_entry = ttk.Entry(add_product_frame, width=15)
        self.price_entry.insert(0, "0")
        self.price_entry.grid(row=2, column=3, padx=5, pady=5)

        ttk.Label(add_product_frame, text="TVA (%):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.vat_entry = ttk.Entry(add_product_frame, width=15)
        self.vat_entry.insert(0, "18")
        self.vat_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(add_product_frame, text="Stock Min:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        self.stock_min_entry = ttk.Entry(add_product_frame, width=15)
        self.stock_min_entry.insert(0, "5")
        self.stock_min_entry.grid(row=3, column=3, padx=5, pady=5)

        ttk.Label(add_product_frame, text="Stock Max:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.stock_max_entry = ttk.Entry(add_product_frame, width=15)
        self.stock_max_entry.insert(0, "100")
        self.stock_max_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(add_product_frame, text="Description:").grid(row=4, column=2, sticky=tk.W, padx=5, pady=5)
        self.desc_entry = ttk.Entry(add_product_frame, width=25)
        self.desc_entry.grid(row=4, column=3, padx=5, pady=5)

        button_frame = ttk.Frame(add_product_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=15)
        ModernButton(button_frame, "✓ AJOUTER PRODUIT", command=self.add_product, style_type="success").pack()

        # ===== SECTION TABLEAU DES PRODUITS =====
        table_frame = ttk.LabelFrame(main_frame, text="📊 INVENTAIRE DES PRODUITS", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            table_frame,
            columns=('ref', 'nom', 'categorie', 'quantite', 'prix_unitaire', 'prix_total', 'stock_min', 'stock_max', 'fournisseur'),
            height=12,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        # Configuration des colonnes (CORRIGÉ : plus d'option "heading" ici)
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.column('ref', anchor=tk.W, width=80)
        self.tree.column('nom', anchor=tk.W, width=120)
        self.tree.column('categorie', anchor=tk.W, width=90)
        self.tree.column('quantite', anchor=tk.CENTER, width=80)
        self.tree.column('prix_unitaire', anchor=tk.E, width=100)
        self.tree.column('prix_total', anchor=tk.E, width=110)
        self.tree.column('stock_min', anchor=tk.CENTER, width=70)
        self.tree.column('stock_max', anchor=tk.CENTER, width=70)
        self.tree.column('fournisseur', anchor=tk.W, width=100)

        # En-têtes
        self.tree.heading('#0', text='', anchor=tk.W)
        self.tree.heading('ref', text='Référence', anchor=tk.W)
        self.tree.heading('nom', text='Nom Produit', anchor=tk.W)
        self.tree.heading('categorie', text='Catégorie', anchor=tk.W)
        self.tree.heading('quantite', text='Quantité', anchor=tk.CENTER)
        self.tree.heading('prix_unitaire', text='P.U. (GNF)', anchor=tk.E)
        self.tree.heading('prix_total', text='Valeur Total', anchor=tk.E)
        self.tree.heading('stock_min', text='Min', anchor=tk.CENTER)
        self.tree.heading('stock_max', text='Max', anchor=tk.CENTER)
        self.tree.heading('fournisseur', text='Fournisseur', anchor=tk.W)

        self.tree.tag_configure('oddrow', background='#F0F0F0')
        self.tree.tag_configure('evenrow', background='white')

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self.on_double_click)

        # ===== SECTION ACTIONS =====
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        ModernButton(action_frame, "✏️ MODIFIER", command=self.edit_selected_product, style_type="info").pack(side=tk.LEFT, padx=5)
        ModernButton(action_frame, "❌ SUPPRIMER", command=self.delete_selected_product, style_type="danger").pack(side=tk.LEFT, padx=5)
        ModernButton(action_frame, "🔄 MOUVEMENTS STOCK", command=self.show_stock_movements, style_type="primary").pack(side=tk.LEFT, padx=5)
        ModernButton(action_frame, "📄 RAPPORT STOCK", command=self.export_stock_report, style_type="accent").pack(side=tk.LEFT, padx=5)

        self.refresh_product_list()

    # ------------------------------------------------------------------
    # Validation commune (ajout + modification)
    # ------------------------------------------------------------------
    @staticmethod
    def parse_numbers(qty_s, price_s, vat_s, min_s, max_s):
        """Convertit et valide les champs numériques. Retourne un tuple ou lève ValueError."""
        try:
            quantity = int(qty_s or 0)
            price = float(price_s or 0)
            vat = float(vat_s or 18)
            stock_min = int(min_s or 5)
            stock_max = int(max_s or 100)
        except ValueError:
            raise ValueError("Format numérique invalide (quantités et stocks : nombres entiers)")

        if price < 0:
            raise ValueError("Le prix ne peut pas être négatif")
        if quantity < 0:
            raise ValueError("La quantité ne peut pas être négative")
        if vat < 0 or vat > 100:
            raise ValueError("La TVA doit être comprise entre 0 et 100 %")
        if stock_min < 0 or stock_max < 0:
            raise ValueError("Les stocks min/max ne peuvent pas être négatifs")
        if stock_min > stock_max:
            raise ValueError("Le stock minimum ne peut pas dépasser le stock maximum")

        return quantity, price, vat, stock_min, stock_max

    def add_product(self):
        """Ajoute un nouveau produit"""
        ref = self.ref_entry.get().strip()
        name = self.name_entry.get().strip()

        if not ref or not name:
            messagebox.showerror("Erreur", "Référence et nom du produit sont obligatoires")
            return

        try:
            quantity, price, vat, stock_min, stock_max = self.parse_numbers(
                self.quantity_entry.get().strip(),
                self.price_entry.get().strip(),
                self.vat_entry.get().strip(),
                self.stock_min_entry.get().strip(),
                self.stock_max_entry.get().strip(),
            )
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))
            return

        conn = None
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products
                (reference, name, description, unit_price, vat_rate, stock_quantity,
                 stock_min, stock_max, category, supplier, last_restock_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ref, name, self.desc_entry.get().strip() or None,
                price, vat, quantity,
                stock_min, stock_max,
                self.category_entry.get().strip() or None,
                self.supplier_entry.get().strip() or None,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

            messagebox.showinfo("✓ Succès", f"Produit '{name}' ajouté avec succès!")
            self.clear_form()
            self.refresh_product_list()

        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", "Cette référence existe déjà!\nChoisissez une autre référence.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout: {str(e)}")
        finally:
            if conn:
                conn.close()

    def clear_form(self):
        """Réinitialise le formulaire (CORRIGÉ : tous les champs)"""
        for entry in (self.ref_entry, self.name_entry, self.category_entry,
                      self.supplier_entry, self.desc_entry):
            entry.delete(0, tk.END)

        defaults = (
            (self.quantity_entry, "0"),
            (self.price_entry, "0"),
            (self.vat_entry, "18"),
            (self.stock_min_entry, "5"),
            (self.stock_max_entry, "100"),
        )
        for entry, value in defaults:
            entry.delete(0, tk.END)
            entry.insert(0, value)

    def refresh_product_list(self):
        """Actualise la liste des produits"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = None
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, reference, name, category, stock_quantity, unit_price,
                       stock_min, stock_max, supplier
                FROM products
                ORDER BY category, name
            """)

            for idx, row in enumerate(cursor.fetchall()):
                try:
                    product_id, ref, name, category, qty, price, min_stock, max_stock, supplier = row

                    qty = int(qty or 0)
                    price = float(price or 0)
                    total_value = qty * price

                    tag = 'oddrow' if idx % 2 == 0 else 'evenrow'

                    self.tree.insert('', tk.END, iid=str(product_id), values=(
                        ref or '',
                        name or '',
                        category or '',
                        qty,
                        f"{price:,.0f}",
                        f"{total_value:,.0f}",
                        min_stock or 0,
                        max_stock or 0,
                        supplier or ''
                    ), tags=(tag,))
                except (ValueError, TypeError) as e:
                    print(f"Erreur ligne {idx}: {e}")
                    continue
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des produits: {str(e)}")
        finally:
            if conn:
                conn.close()

    def on_double_click(self, event):
        """Double-clic : ouvre la modification seulement si une ligne est visée (CORRIGÉ)"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.edit_product(item)

    def edit_selected_product(self):
        """Édite le produit sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un produit")
            return
        self.edit_product(selection[0])

    def edit_product(self, product_id):
        """Édite un produit spécifique (CORRIGÉ : tous les champs modifiables)"""
        conn = None
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            return
        finally:
            if conn:
                conn.close()

        if not product:
            messagebox.showerror("Erreur", "Produit introuvable")
            return

        edit_window = tk.Toplevel(self.parent)
        edit_window.title(f"Éditer: {product['name']}")
        edit_window.geometry("520x520")
        edit_window.transient(self.parent.winfo_toplevel())
        edit_window.grab_set()

        frame = ttk.Frame(edit_window, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Référence:", 'reference'),
            ("Nom:", 'name'),
            ("Catégorie:", 'category'),
            ("Fournisseur:", 'supplier'),
            ("Quantité Stock:", 'stock_quantity'),
            ("Prix Unitaire (GNF):", 'unit_price'),
            ("TVA (%):", 'vat_rate'),
            ("Stock Min:", 'stock_min'),
            ("Stock Max:", 'stock_max'),
            ("Description:", 'description'),
        ]
        entries = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(frame, width=35)
            value = product[key]
            entry.insert(0, "" if value is None else str(value))
            entry.grid(row=row, column=1, pady=5, padx=5)
            entries[key] = entry

        def save_changes():
            ref = entries['reference'].get().strip()
            name = entries['name'].get().strip()
            if not ref or not name:
                messagebox.showerror("Erreur", "Référence et nom sont obligatoires", parent=edit_window)
                return

            try:
                # float() d'abord pour accepter "5.0" venant de la base
                qty_s = entries['stock_quantity'].get().strip()
                min_s = entries['stock_min'].get().strip()
                max_s = entries['stock_max'].get().strip()
                qty_s = str(int(float(qty_s))) if qty_s else qty_s
                min_s = str(int(float(min_s))) if min_s else min_s
                max_s = str(int(float(max_s))) if max_s else max_s

                quantity, price, vat, stock_min, stock_max = self.parse_numbers(
                    qty_s,
                    entries['unit_price'].get().strip(),
                    entries['vat_rate'].get().strip(),
                    min_s,
                    max_s,
                )
            except ValueError as e:
                messagebox.showerror("Erreur", str(e) or "Format numérique invalide", parent=edit_window)
                return

            conn = None
            try:
                conn = self.db.get_conn()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products
                    SET reference=?, name=?, category=?, supplier=?, stock_quantity=?,
                        unit_price=?, vat_rate=?, stock_min=?, stock_max=?, description=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (
                    ref, name,
                    entries['category'].get().strip() or None,
                    entries['supplier'].get().strip() or None,
                    quantity, price, vat, stock_min, stock_max,
                    entries['description'].get().strip() or None,
                    product_id
                ))
                conn.commit()

                messagebox.showinfo("✓ Succès", "Produit mis à jour!", parent=edit_window)
                edit_window.destroy()
                self.refresh_product_list()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erreur", "Cette référence est déjà utilisée par un autre produit.", parent=edit_window)
            except Exception as e:
                messagebox.showerror("Erreur", str(e), parent=edit_window)
            finally:
                if conn:
                    conn.close()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        ModernButton(btn_frame, "✓ ENREGISTRER", command=save_changes, style_type="success").pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, "ANNULER", command=edit_window.destroy, style_type="danger").pack(side=tk.LEFT, padx=5)

    def delete_selected_product(self):
        """Supprime le produit sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un produit")
            return

        product_id = selection[0]
        name = self.tree.item(product_id, 'values')[1]
        if not messagebox.askyesno("Confirmation", f"Supprimer le produit « {name} » ?"):
            return

        conn = None
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            # Supprimer aussi les mouvements liés pour ne pas laisser d'orphelins
            cursor.execute("DELETE FROM stock_movements WHERE product_id=?", (product_id,))
            cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
            conn.commit()

            messagebox.showinfo("✓ Succès", "Produit supprimé!")
            self.refresh_product_list()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
        finally:
            if conn:
                conn.close()

    def show_stock_movements(self):
        """Affiche l'historique des mouvements de stock"""
        win = tk.Toplevel(self.parent)
        win.title("Mouvements de stock")
        win.geometry("900x450")

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        cols = ('date', 'ref', 'produit', 'type', 'qte', 'motif', 'doc')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=15)
        titles = ('Date', 'Référence', 'Produit', 'Type', 'Quantité', 'Motif', 'Document')
        widths = (140, 90, 180, 80, 80, 180, 110)
        for c, t, w in zip(cols, titles, widths):
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=tk.CENTER if c in ('type', 'qte') else tk.W)

        sb = ttk.Scrollbar(frame, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        conn = None
        try:
            conn = self.db.get_conn()
            rows = conn.execute("""
                SELECT m.created_at, p.reference, p.name, m.movement_type, m.quantity,
                       m.reason, m.reference_doc
                FROM stock_movements m
                LEFT JOIN products p ON p.id = m.product_id
                ORDER BY m.created_at DESC, m.id DESC
            """).fetchall()
            for r in rows:
                tree.insert('', tk.END, values=tuple('' if v is None else v for v in r))
            if not rows:
                tree.insert('', tk.END, values=('', '', 'Aucun mouvement enregistré', '', '', '', ''))
        except Exception as e:
            messagebox.showerror("Erreur", str(e), parent=win)
        finally:
            if conn:
                conn.close()

    def export_stock_report(self):
        """Exporte un rapport de stock (CORRIGÉ : gestion des valeurs vides)"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt")],
            initialfile=f"Rapport_Stock_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        if not filename:
            return

        conn = None
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT reference, name, stock_quantity, unit_price, category FROM products ORDER BY category, name")
            rows = cursor.fetchall()

            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 100 + "\n")
                f.write(f"RAPPORT D'INVENTAIRE - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write("=" * 100 + "\n\n")

                total_value = 0
                for row in rows:
                    ref, name, qty, price, category = row
                    qty = int(qty or 0)
                    price = float(price or 0)
                    value = qty * price
                    total_value += value
                    f.write(
                        f"{(ref or ''):15} | {(name or ''):30} | Qté: {qty:5} | "
                        f"P.U: {price:12,.0f} GNF | Valeur: {value:15,.0f} GNF | "
                        f"Catégorie: {category or '-'}\n"
                    )

                f.write("\n" + "=" * 100 + "\n")
                f.write(f"NOMBRE DE PRODUITS: {len(rows)}\n")
                f.write(f"VALEUR TOTALE DE L'INVENTAIRE: {total_value:,.0f} GNF\n")
                f.write("=" * 100 + "\n")

            messagebox.showinfo("✓ Succès", f"Rapport exporté: {filename}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
        finally:
            if conn:
                conn.close()

# ════════════════════════════════════════════════════════════════════════════
# MODULE FACTURES
# ════════════════════════════════════════════════════════════════════════════

class InvoiceModule:
    """Création de factures, sortie de stock automatique et export PDF"""

    STATUSES = {'pending': 'En attente', 'paid': 'Payée', 'cancelled': 'Annulée'}

    def __init__(self, parent, db, on_stock_change=None):
        self.parent = parent
        self.db = db
        self.on_stock_change = on_stock_change  # rafraîchit l'onglet Stock
        self.lines = []      # lignes de la facture en cours
        self.products = {}   # "REF - Nom" -> ligne produit
        self.build_ui()

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def build_ui(self):
        main = ttk.Frame(self.parent)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== CLIENT =====
        client = ttk.LabelFrame(main, text="👤 CLIENT", padding=10)
        client.pack(fill=tk.X, pady=(0, 10))

        self.c_name = self._field(client, "Nom du client *:", 0, 0, 30)
        self.c_phone = self._field(client, "Téléphone:", 0, 2, 20)
        self.c_email = self._field(client, "Email:", 1, 0, 30)
        self.c_address = self._field(client, "Adresse:", 1, 2, 30)

        ttk.Label(client, text="Échéance (jours):").grid(row=0, column=4, sticky=tk.W, padx=5, pady=4)
        self.due_days = ttk.Entry(client, width=8)
        self.due_days.insert(0, "30")
        self.due_days.grid(row=0, column=5, padx=5, pady=4)

        ttk.Label(client, text="Notes:").grid(row=1, column=4, sticky=tk.W, padx=5, pady=4)
        self.notes_entry = ttk.Entry(client, width=25)
        self.notes_entry.grid(row=1, column=5, padx=5, pady=4)

        # ===== LIGNES =====
        lines_frame = ttk.LabelFrame(main, text="🛒 ARTICLES DE LA FACTURE", padding=10)
        lines_frame.pack(fill=tk.X, pady=(0, 10))

        bar = ttk.Frame(lines_frame)
        bar.pack(fill=tk.X)
        ttk.Label(bar, text="Produit:").pack(side=tk.LEFT, padx=5)
        self.product_combo = ttk.Combobox(bar, width=45, state="readonly")
        self.product_combo.pack(side=tk.LEFT, padx=5)
        self.product_combo.bind("<<ComboboxSelected>>", self._on_product_selected)
        ttk.Label(bar, text="Qté:").pack(side=tk.LEFT, padx=5)
        self.qty_entry = ttk.Entry(bar, width=8)
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(side=tk.LEFT, padx=5)
        self.stock_info = ttk.Label(bar, text="", foreground=ModernTheme.TEXT_LIGHT)
        self.stock_info.pack(side=tk.LEFT, padx=10)
        ModernButton(bar, "➕ AJOUTER", command=self.add_line, style_type="success").pack(side=tk.LEFT, padx=5)
        ModernButton(bar, "➖ RETIRER", command=self.remove_line, style_type="danger").pack(side=tk.LEFT, padx=5)

        cols = ('ref', 'desc', 'qte', 'pu', 'tva', 'ht', 'ttc')
        self.lines_tree = ttk.Treeview(lines_frame, columns=cols, show='headings', height=5)
        for c, t, w in zip(cols, ('Réf.', 'Désignation', 'Qté', 'P.U. HT', 'TVA', 'Total HT', 'Total TTC'),
                           (80, 260, 60, 110, 60, 120, 120)):
            self.lines_tree.heading(c, text=t)
            self.lines_tree.column(c, width=w, anchor=tk.W if c in ('ref', 'desc') else tk.E)
        self.lines_tree.pack(fill=tk.X, pady=(8, 4))

        footer = ttk.Frame(lines_frame)
        footer.pack(fill=tk.X)
        self.totals_label = ttk.Label(footer, text="", font=("Segoe UI", 11, "bold"))
        self.totals_label.pack(side=tk.LEFT, padx=5)
        ModernButton(footer, "💾 ENREGISTRER LA FACTURE", command=self.save_invoice, style_type="primary").pack(side=tk.RIGHT, padx=5)
        ModernButton(footer, "🧹 VIDER", command=self.reset_form, style_type="accent").pack(side=tk.RIGHT, padx=5)

        # ===== HISTORIQUE =====
        hist = ttk.LabelFrame(main, text="📄 FACTURES ENREGISTRÉES", padding=10)
        hist.pack(fill=tk.BOTH, expand=True)

        cols = ('num', 'date', 'client', 'ht', 'tva', 'ttc', 'statut')
        self.inv_tree = ttk.Treeview(hist, columns=cols, show='headings', height=6)
        for c, t, w in zip(cols, ('Numéro', 'Date', 'Client', 'Total HT', 'TVA', 'Total TTC', 'Statut'),
                           (120, 130, 220, 120, 100, 130, 100)):
            self.inv_tree.heading(c, text=t)
            self.inv_tree.column(c, width=w, anchor=tk.E if c in ('ht', 'tva', 'ttc') else tk.W)
        sb = ttk.Scrollbar(hist, command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.inv_tree.pack(fill=tk.BOTH, expand=True)
        self.inv_tree.bind('<Double-1>', lambda e: self.export_pdf())

        actions = ttk.Frame(main)
        actions.pack(fill=tk.X, pady=8)
        ModernButton(actions, "📑 EXPORTER EN PDF", command=self.export_pdf, style_type="info").pack(side=tk.LEFT, padx=5)
        ModernButton(actions, "✓ MARQUER PAYÉE", command=lambda: self.set_status('paid'), style_type="success").pack(side=tk.LEFT, padx=5)
        ModernButton(actions, "✖ ANNULER LA FACTURE", command=self.cancel_invoice, style_type="danger").pack(side=tk.LEFT, padx=5)
        ModernButton(actions, "🔄 ACTUALISER", command=self.refresh_all, style_type="primary").pack(side=tk.LEFT, padx=5)

        self.refresh_all()

    @staticmethod
    def _field(parent, label, row, col, width):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
        e = ttk.Entry(parent, width=width)
        e.grid(row=row, column=col + 1, padx=5, pady=4)
        return e

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------
    def refresh_all(self):
        self.load_products()
        self.refresh_invoices()
        self._render_lines()

    def load_products(self):
        conn = None
        try:
            conn = self.db.get_conn()
            rows = conn.execute("""
                SELECT id, reference, name, unit_price, vat_rate, stock_quantity
                FROM products ORDER BY name
            """).fetchall()
            self.products = {f"{r['reference']} - {r['name']}": r for r in rows}
            self.product_combo['values'] = list(self.products.keys())
        except Exception as e:
            messagebox.showerror("Erreur", f"Chargement des produits: {e}")
        finally:
            if conn:
                conn.close()

    def _on_product_selected(self, _event=None):
        p = self.products.get(self.product_combo.get())
        if p:
            self.stock_info.config(
                text=f"Stock: {p['stock_quantity']} | P.U.: {float(p['unit_price'] or 0):,.0f} GNF")

    def _qty_already_in_lines(self, product_id):
        return sum(l['quantity'] for l in self.lines if l['product_id'] == product_id)

    def add_line(self):
        p = self.products.get(self.product_combo.get())
        if not p:
            messagebox.showwarning("Attention", "Choisissez un produit")
            return
        try:
            qty = int(self.qty_entry.get().strip())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "La quantité doit être un nombre entier positif")
            return

        available = int(p['stock_quantity'] or 0) - self._qty_already_in_lines(p['id'])
        if qty > available:
            messagebox.showerror("Stock insuffisant",
                                 f"Stock disponible pour « {p['name']} » : {available}")
            return

        # Fusionner avec une ligne existante du même produit
        for l in self.lines:
            if l['product_id'] == p['id']:
                l['quantity'] += qty
                break
        else:
            self.lines.append({
                'product_id': p['id'],
                'reference': p['reference'],
                'description': p['name'],
                'quantity': qty,
                'unit_price_ht': float(p['unit_price'] or 0),
                'vat_rate': float(p['vat_rate'] or 0),
            })

        self.qty_entry.delete(0, tk.END)
        self.qty_entry.insert(0, "1")
        self._render_lines()

    def remove_line(self):
        sel = self.lines_tree.selection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez une ligne à retirer")
            return
        del self.lines[int(sel[0])]
        self._render_lines()

    @staticmethod
    def compute_line(l):
        ht = round(l['quantity'] * l['unit_price_ht'])
        vat = round(ht * l['vat_rate'] / 100)
        return ht, vat, ht + vat

    def compute_totals(self):
        ht = vat = 0
        for l in self.lines:
            lh, lv, _ = self.compute_line(l)
            ht += lh
            vat += lv
        return ht, vat, ht + vat

    def _render_lines(self):
        for i in self.lines_tree.get_children():
            self.lines_tree.delete(i)
        for idx, l in enumerate(self.lines):
            ht, vat, ttc = self.compute_line(l)
            self.lines_tree.insert('', tk.END, iid=str(idx), values=(
                l['reference'], l['description'], l['quantity'],
                f"{l['unit_price_ht']:,.0f}", f"{l['vat_rate']:.0f}%",
                f"{ht:,.0f}", f"{ttc:,.0f}"))
        ht, vat, ttc = self.compute_totals()
        self.totals_label.config(
            text=f"Total HT: {ht:,.0f} GNF    TVA: {vat:,.0f} GNF    TOTAL TTC: {ttc:,.0f} GNF")

    def reset_form(self):
        for e in (self.c_name, self.c_phone, self.c_email, self.c_address, self.notes_entry):
            e.delete(0, tk.END)
        self.due_days.delete(0, tk.END)
        self.due_days.insert(0, "30")
        self.product_combo.set('')
        self.stock_info.config(text='')
        self.lines = []
        self._render_lines()

    @staticmethod
    def next_invoice_number(conn):
        prefix = f"F-{datetime.now().strftime('%Y%m')}-"
        row = conn.execute(
            "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ? "
            "ORDER BY invoice_number DESC LIMIT 1", (prefix + '%',)).fetchone()
        n = int(row[0].rsplit('-', 1)[1]) + 1 if row else 1
        return f"{prefix}{n:04d}"

    def save_invoice(self):
        name = self.c_name.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom du client est obligatoire")
            return
        if not self.lines:
            messagebox.showerror("Erreur", "Ajoutez au moins un article")
            return
        try:
            days = int(self.due_days.get().strip() or 0)
            if days < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "L'échéance doit être un nombre de jours positif")
            return

        from datetime import timedelta
        now = datetime.now()
        due = now + timedelta(days=days)
        ht, vat, ttc = self.compute_totals()

        conn = None
        try:
            conn = self.db.get_conn()
            cur = conn.cursor()

            # Revérifier le stock au moment de l'enregistrement
            for l in self.lines:
                stock = cur.execute("SELECT stock_quantity, name FROM products WHERE id=?",
                                    (l['product_id'],)).fetchone()
                if not stock:
                    raise ValueError(f"Produit « {l['description']} » introuvable")
                if int(stock[0] or 0) < l['quantity']:
                    raise ValueError(f"Stock insuffisant pour « {stock[1]} » (disponible : {stock[0]})")

            number = self.next_invoice_number(conn)
            phone = self.c_phone.get().strip() or None
            email = self.c_email.get().strip() or None
            address = self.c_address.get().strip() or None

            # Client : réutiliser s'il existe déjà (même nom + téléphone), sinon le créer
            row = cur.execute("SELECT id FROM customers WHERE name=? AND IFNULL(phone,'')=IFNULL(?,'')",
                              (name, phone)).fetchone()
            if row:
                customer_id = row[0]
            else:
                cur.execute("INSERT INTO customers (name, phone, email, address) VALUES (?,?,?,?)",
                            (name, phone, email, address))
                customer_id = cur.lastrowid

            cur.execute("""
                INSERT INTO invoices (invoice_number, customer_id, customer_name, customer_address,
                    customer_email, customer_phone, total_ht, total_vat, total_ttc,
                    payment_status, invoice_date, due_date, notes)
                VALUES (?,?,?,?,?,?,?,?,?,'pending',?,?,?)
            """, (number, customer_id, name, address, email, phone, ht, vat, ttc,
                  now.strftime("%Y-%m-%d %H:%M:%S"), due.strftime("%Y-%m-%d"),
                  self.notes_entry.get().strip() or None))
            invoice_id = cur.lastrowid

            for l in self.lines:
                lh, lv, lt = self.compute_line(l)
                cur.execute("""
                    INSERT INTO invoice_lines (invoice_id, product_id, description, quantity,
                        unit_price_ht, vat_rate, line_total_ht, line_vat, line_total_ttc)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (invoice_id, l['product_id'], l['description'], l['quantity'],
                      l['unit_price_ht'], l['vat_rate'], lh, lv, lt))
                cur.execute("""
                    UPDATE products SET stock_quantity = stock_quantity - ?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (l['quantity'], l['product_id']))
                cur.execute("""
                    INSERT INTO stock_movements (product_id, movement_type, quantity, reason, reference_doc)
                    VALUES (?, 'SORTIE', ?, 'Vente', ?)
                """, (l['product_id'], l['quantity'], number))

            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Erreur", f"Facture non enregistrée : {e}")
            return
        finally:
            if conn:
                conn.close()

        self.reset_form()
        self.refresh_all()
        if self.on_stock_change:
            self.on_stock_change()

        if messagebox.askyesno("✓ Facture enregistrée",
                               f"Facture {number} enregistrée ({ttc:,.0f} GNF TTC).\n\n"
                               "Voulez-vous l'exporter en PDF maintenant ?"):
            self.export_pdf(invoice_id)

    def refresh_invoices(self):
        for i in self.inv_tree.get_children():
            self.inv_tree.delete(i)
        conn = None
        try:
            conn = self.db.get_conn()
            rows = conn.execute("""
                SELECT id, invoice_number, invoice_date, customer_name, total_ht, total_vat,
                       total_ttc, payment_status
                FROM invoices ORDER BY id DESC
            """).fetchall()
            for r in rows:
                self.inv_tree.insert('', tk.END, iid=str(r['id']), values=(
                    r['invoice_number'], str(r['invoice_date'] or '')[:16], r['customer_name'],
                    f"{float(r['total_ht'] or 0):,.0f}", f"{float(r['total_vat'] or 0):,.0f}",
                    f"{float(r['total_ttc'] or 0):,.0f}",
                    self.STATUSES.get(r['payment_status'], r['payment_status'])))
        except Exception as e:
            messagebox.showerror("Erreur", f"Chargement des factures: {e}")
        finally:
            if conn:
                conn.close()

    def _selected_invoice_id(self):
        sel = self.inv_tree.selection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez une facture")
            return None
        return int(sel[0])

    def set_status(self, status):
        invoice_id = self._selected_invoice_id()
        if invoice_id is None:
            return
        conn = None
        try:
            conn = self.db.get_conn()
            current = conn.execute("SELECT payment_status FROM invoices WHERE id=?", (invoice_id,)).fetchone()[0]
            if current == 'cancelled':
                messagebox.showwarning("Attention", "Cette facture est annulée")
                return
            conn.execute("UPDATE invoices SET payment_status=? WHERE id=?", (status, invoice_id))
            conn.commit()
        finally:
            if conn:
                conn.close()
        self.refresh_invoices()

    def cancel_invoice(self):
        """Annule la facture et remet les articles en stock"""
        invoice_id = self._selected_invoice_id()
        if invoice_id is None:
            return
        conn = None
        try:
            conn = self.db.get_conn()
            inv = conn.execute("SELECT invoice_number, payment_status FROM invoices WHERE id=?",
                               (invoice_id,)).fetchone()
            if inv['payment_status'] == 'cancelled':
                messagebox.showinfo("Info", "Cette facture est déjà annulée")
                return
            if inv['payment_status'] == 'paid' and not messagebox.askyesno(
                    "Attention", "Cette facture est marquée PAYÉE. L'annuler quand même ?"):
                return
            if not messagebox.askyesno("Confirmation",
                                       f"Annuler la facture {inv['invoice_number']} ?\n"
                                       "Les articles seront remis en stock."):
                return

            cur = conn.cursor()
            for l in cur.execute("SELECT product_id, quantity FROM invoice_lines WHERE invoice_id=?",
                                 (invoice_id,)).fetchall():
                if l['product_id'] is None:
                    continue
                cur.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id=?",
                            (int(l['quantity']), l['product_id']))
                cur.execute("""
                    INSERT INTO stock_movements (product_id, movement_type, quantity, reason, reference_doc)
                    VALUES (?, 'ENTRÉE', ?, 'Annulation facture', ?)
                """, (l['product_id'], int(l['quantity']), inv['invoice_number']))
            cur.execute("UPDATE invoices SET payment_status='cancelled' WHERE id=?", (invoice_id,))
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Erreur", str(e))
            return
        finally:
            if conn:
                conn.close()

        self.refresh_all()
        if self.on_stock_change:
            self.on_stock_change()

    def get_company_info(self, conn):
        row = conn.execute("SELECT * FROM companies ORDER BY id LIMIT 1").fetchone()
        if row:
            return {k: (row[k] or '') for k in ('name', 'address', 'city', 'phone', 'email')}
        return {'name': 'ANSARTECH', 'address': '', 'city': 'Conakry, Guinée',
                'phone': '', 'email': 'support@ansartech.com'}

    def export_pdf(self, invoice_id=None):
        if invoice_id is None:
            invoice_id = self._selected_invoice_id()
            if invoice_id is None:
                return

        conn = None
        try:
            conn = self.db.get_conn()
            inv = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
            if not inv:
                messagebox.showerror("Erreur", "Facture introuvable")
                return
            lines = [dict(r) for r in conn.execute(
                "SELECT * FROM invoice_lines WHERE invoice_id=? ORDER BY id", (invoice_id,)).fetchall()]
            company = self.get_company_info(conn)
        finally:
            if conn:
                conn.close()

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Fichiers PDF", "*.pdf")],
            initialfile=f"Facture_{inv['invoice_number']}.pdf")
        if not filename:
            return

        def fmt_date(value, with_time=False):
            if not value:
                return ''
            for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
                try:
                    return datetime.strptime(str(value), f).strftime("%d/%m/%Y" + (" %H:%M" if with_time else ""))
                except ValueError:
                    continue
            return str(value)

        data = dict(inv)
        data['invoice_date'] = fmt_date(inv['invoice_date'])
        data['due_date'] = fmt_date(inv['due_date'])
        data['payment_status'] = self.STATUSES.get(inv['payment_status'], inv['payment_status'])
        data['lines'] = lines
        for k in ('customer_address', 'customer_email', 'customer_phone'):
            data[k] = data.get(k) or ''

        try:
            InvoicePDFGenerator.generate_invoice_pdf(filename, data, company)
            messagebox.showinfo("✓ PDF créé", f"Facture exportée :\n{filename}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

# ════════════════════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE
# ════════════════════════════════════════════════════════════════════════════

class ANSARTECHERP:
    """Application ERP principale"""

    def __init__(self, root):
        self.root = root
        self.root.title("ANSARTECH ERP V2.2 - Gestion Professionnelle")
        self.root.geometry("1400x800")
        self.root.configure(bg=ModernTheme.BG_LIGHT)

        self.db = Database()
        self.init_sample_data()
        self.create_main_interface()

    def init_sample_data(self):
        """Initialise les données d'exemple si nécessaire"""
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            conn.close()

            if count == 0:
                self.add_sample_products()
        except Exception as e:
            print(f"Erreur vérification données: {e}")

    def add_sample_products(self):
        """Ajoute des produits d'exemple"""
        products = [
            ('REF-001', 'Ordinateur Portable HP', 'Ordinateur portable 15" HP', 850000, 18, 5, 2, 20, 'Informatique', 'HP Distribution'),
            ('REF-002', 'Souris Logitech', 'Souris sans fil ergonomique', 35000, 18, 50, 10, 100, 'Accessoires', 'Logitech'),
            ('REF-003', 'Clavier Mécanique', 'Clavier RGB avec touches mécaniques', 150000, 18, 12, 5, 50, 'Accessoires', 'Corsair'),
            ('REF-004', 'Écran 27 pouces 4K', 'Moniteur IPS 27" 4K', 450000, 18, 8, 3, 30, 'Écrans', 'Dell'),
            ('REF-005', 'Disque Dur 2TB', 'Stockage externe USB 3.0', 120000, 18, 25, 5, 100, 'Stockage', 'Western Digital'),
        ]

        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for ref, name, desc, price, vat, qty, min_stk, max_stk, cat, supplier in products:
                cursor.execute("""
                    INSERT OR IGNORE INTO products
                    (reference, name, description, unit_price, vat_rate, stock_quantity,
                     stock_min, stock_max, category, supplier, last_restock_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ref, name, desc, price, vat, qty, min_stk, max_stk, cat, supplier, now))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erreur initialisation données: {e}")

    def create_main_interface(self):
        """Crée l'interface principale"""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = tk.Label(
            header_frame,
            text="🚀 ANSARTECH ERP V2.2 - Gestion Professionnelle",
            font=("Segoe UI", 16, "bold"),
            fg=ModernTheme.PRIMARY,
            bg=ModernTheme.BG_LIGHT
        )
        title_label.pack(anchor=tk.W)

        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Quitter", command=self.root.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self.show_about)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        stock_frame = ttk.Frame(self.notebook)
        self.notebook.add(stock_frame, text="📦 GESTION DU STOCK")
        self.stock_module = StockManagementModule(stock_frame, self.db)

        invoice_frame = ttk.Frame(self.notebook)
        self.notebook.add(invoice_frame, text="📄 FACTURES")
        self.invoice_module = InvoiceModule(invoice_frame, self.db,
                                            on_stock_change=self.stock_module.refresh_product_list)

        # Quand on revient sur un onglet, recharger ses données
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, _event=None):
        idx = self.notebook.index(self.notebook.select())
        if idx == 0:
            self.stock_module.refresh_product_list()
        elif idx == 1:
            self.invoice_module.load_products()

    def show_about(self):
        """Affiche la fenêtre À propos"""
        messagebox.showinfo(
            "À propos",
            "ANSARTECH ERP V2.2\n\n"
            "Solution professionnelle de gestion\n"
            "Stock • Factures • Comptabilité\n\n"
            "Développé par: ANSARTECH Solutions\n"
            "Contact: support@ansartech.com"
        )

    def show_stock_management(self):
        self.notebook.select(0)

    def show_invoices(self):
        self.notebook.select(1)

# ════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = ANSARTECHERP(root)
    root.mainloop()
