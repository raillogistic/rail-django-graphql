"""
Modèles Django pour les tests.

Ce module définit:
- Modèles de test supplémentaires
- Modèles pour les tests de performance
- Modèles pour les tests de concurrence
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from typing import Dict, Any, Optional, List

from rail_django_graphql.decorators import business_logic as business_method


# Modèles de test pour les opérations de base de données
class TestCustomer(models.Model):
    """Modèle client pour les tests d'opérations de base de données."""

    nom_client = models.CharField(max_length=100, verbose_name="Nom du client")
    prenom_client = models.CharField(max_length=100, verbose_name="Prénom du client")
    email_client = models.EmailField(unique=True, verbose_name="E-mail du client")
    telephone_client = models.CharField(
        max_length=20, blank=True, verbose_name="Téléphone du client"
    )
    date_naissance = models.DateField(
        null=True, blank=True, verbose_name="Date de naissance"
    )
    adresse_client = models.TextField(blank=True, verbose_name="Adresse du client")
    ville_client = models.CharField(
        max_length=100, blank=True, verbose_name="Ville du client"
    )
    code_postal = models.CharField(
        max_length=10, blank=True, verbose_name="Code postal"
    )
    pays_client = models.CharField(
        max_length=50, default="France", verbose_name="Pays du client"
    )
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")
    date_creation = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    date_modification = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )
    solde_compte = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Solde du compte"
    )

    @business_method
    def crediter_compte(self, montant: float) -> bool:
        """Crédite le compte du client."""
        if montant <= 0:
            raise ValueError("Le montant doit être positif")

        self.solde_compte += montant
        self.save()
        return True

    @business_method
    def debiter_compte(self, montant: float) -> bool:
        """Débite le compte du client."""
        if montant <= 0:
            raise ValueError("Le montant doit être positif")

        if self.solde_compte < montant:
            raise ValueError("Solde insuffisant")

        self.solde_compte -= montant
        self.save()
        return True

    @business_method
    def calculer_age(self) -> Optional[int]:
        """Calcule l'âge du client."""
        if not self.date_naissance:
            return None

        from datetime import date

        today = date.today()
        return (
            today.year
            - self.date_naissance.year
            - (
                (today.month, today.day)
                < (self.date_naissance.month, self.date_naissance.day)
            )
        )

    def clean(self):
        """Validation personnalisée du modèle."""
        from django.core.exceptions import ValidationError

        if self.solde_compte < 0:
            raise ValidationError("Le solde ne peut pas être négatif")

    def __str__(self):
        return f"{self.prenom_client} {self.nom_client}"

    class Meta:
        app_label = "tests"
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["nom_client", "prenom_client"]
        indexes = [
            models.Index(fields=["email_client"]),
            models.Index(fields=["nom_client", "prenom_client"]),
            models.Index(fields=["ville_client"]),
        ]


class TestAccount(models.Model):
    """Modèle compte pour les tests d'opérations de base de données."""

    numero_compte = models.CharField(
        max_length=20, unique=True, verbose_name="Numéro de compte"
    )
    client_compte = models.ForeignKey(
        TestCustomer,
        on_delete=models.CASCADE,
        related_name="comptes_client",
        verbose_name="Client du compte",
    )
    type_compte = models.CharField(
        max_length=20,
        choices=[
            ("COURANT", "Compte courant"),
            ("EPARGNE", "Compte épargne"),
            ("PROFESSIONNEL", "Compte professionnel"),
        ],
        default="COURANT",
        verbose_name="Type de compte",
    )
    solde_compte = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, verbose_name="Solde du compte"
    )
    taux_interet = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="Taux d'intérêt"
    )
    date_ouverture = models.DateField(
        auto_now_add=True, verbose_name="Date d'ouverture"
    )
    date_fermeture = models.DateField(
        null=True, blank=True, verbose_name="Date de fermeture"
    )
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")

    @business_method
    def effectuer_virement(
        self, compte_destinataire: "TestAccount", montant: float
    ) -> bool:
        """Effectue un virement vers un autre compte."""
        from django.db import transaction

        if montant <= 0:
            raise ValueError("Le montant doit être positif")

        if self.solde_compte < montant:
            raise ValueError("Solde insuffisant")

        if not self.est_actif or not compte_destinataire.est_actif:
            raise ValueError("Les comptes doivent être actifs")

        with transaction.atomic():
            self.solde_compte -= montant
            compte_destinataire.solde_compte += montant
            self.save()
            compte_destinataire.save()

        return True

    @business_method
    def calculer_interets(self) -> float:
        """Calcule les intérêts du compte."""
        return float(self.solde_compte * self.taux_interet / 100)

    @business_method
    def fermer_compte(self) -> bool:
        """Ferme le compte."""
        if self.solde_compte != 0:
            raise ValueError("Le solde doit être à zéro pour fermer le compte")

        from datetime import date

        self.est_actif = False
        self.date_fermeture = date.today()
        self.save()
        return True

    def clean(self):
        """Validation personnalisée du modèle."""
        from django.core.exceptions import ValidationError

        if self.solde_compte < 0 and self.type_compte != "COURANT":
            raise ValidationError(
                "Seuls les comptes courants peuvent avoir un solde négatif"
            )

    def __str__(self):
        return f"Compte {self.numero_compte} - {self.client_compte}"

    class Meta:
        app_label = "tests"
        verbose_name = "Compte"
        verbose_name_plural = "Comptes"
        ordering = ["numero_compte"]
        indexes = [
            models.Index(fields=["numero_compte"]),
            models.Index(fields=["client_compte", "type_compte"]),
        ]


class TestTransaction(models.Model):
    """Modèle transaction pour les tests d'opérations de base de données."""

    numero_transaction = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro de transaction"
    )
    compte_source = models.ForeignKey(
        TestAccount,
        on_delete=models.CASCADE,
        related_name="transactions_sortantes",
        verbose_name="Compte source",
    )
    compte_destination = models.ForeignKey(
        TestAccount,
        on_delete=models.CASCADE,
        related_name="transactions_entrantes",
        null=True,
        blank=True,
        verbose_name="Compte destination",
    )
    type_transaction = models.CharField(
        max_length=20,
        choices=[
            ("DEPOT", "Dépôt"),
            ("RETRAIT", "Retrait"),
            ("VIREMENT", "Virement"),
            ("PRELEVEMENT", "Prélèvement"),
            ("FRAIS", "Frais"),
        ],
        verbose_name="Type de transaction",
    )
    montant_transaction = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Montant de la transaction"
    )
    description_transaction = models.TextField(
        blank=True, verbose_name="Description de la transaction"
    )
    date_transaction = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de transaction"
    )
    statut_transaction = models.CharField(
        max_length=20,
        choices=[
            ("EN_ATTENTE", "En attente"),
            ("VALIDEE", "Validée"),
            ("REJETEE", "Rejetée"),
            ("ANNULEE", "Annulée"),
        ],
        default="EN_ATTENTE",
        verbose_name="Statut de la transaction",
    )

    @business_method
    def valider_transaction(self) -> bool:
        """Valide la transaction."""
        from django.db import transaction

        if self.statut_transaction != "EN_ATTENTE":
            raise ValueError("Seules les transactions en attente peuvent être validées")

        with transaction.atomic():
            # Vérifier le solde pour les débits
            if self.type_transaction in ["RETRAIT", "VIREMENT", "PRELEVEMENT", "FRAIS"]:
                if self.compte_source.solde_compte < self.montant_transaction:
                    self.statut_transaction = "REJETEE"
                    self.save()
                    raise ValueError("Solde insuffisant")

            # Effectuer la transaction
            if self.type_transaction == "DEPOT":
                self.compte_source.solde_compte += self.montant_transaction
                self.compte_source.save()
            elif self.type_transaction in ["RETRAIT", "PRELEVEMENT", "FRAIS"]:
                self.compte_source.solde_compte -= self.montant_transaction
                self.compte_source.save()
            elif self.type_transaction == "VIREMENT" and self.compte_destination:
                self.compte_source.solde_compte -= self.montant_transaction
                self.compte_destination.solde_compte += self.montant_transaction
                self.compte_source.save()
                self.compte_destination.save()

            self.statut_transaction = "VALIDEE"
            self.save()

        return True

    @business_method
    def annuler_transaction(self) -> bool:
        """Annule la transaction."""
        from django.db import transaction

        if self.statut_transaction not in ["EN_ATTENTE", "VALIDEE"]:
            raise ValueError("Cette transaction ne peut pas être annulée")

        if self.statut_transaction == "VALIDEE":
            # Inverser la transaction
            with transaction.atomic():
                if self.type_transaction == "DEPOT":
                    self.compte_source.solde_compte -= self.montant_transaction
                    self.compte_source.save()
                elif self.type_transaction in ["RETRAIT", "PRELEVEMENT", "FRAIS"]:
                    self.compte_source.solde_compte += self.montant_transaction
                    self.compte_source.save()
                elif self.type_transaction == "VIREMENT" and self.compte_destination:
                    self.compte_source.solde_compte += self.montant_transaction
                    self.compte_destination.solde_compte -= self.montant_transaction
                    self.compte_source.save()
                    self.compte_destination.save()

        self.statut_transaction = "ANNULEE"
        self.save()
        return True

    def clean(self):
        """Validation personnalisée du modèle."""
        from django.core.exceptions import ValidationError

        if self.montant_transaction <= 0:
            raise ValidationError("Le montant doit être positif")

        if self.type_transaction == "VIREMENT" and not self.compte_destination:
            raise ValidationError(
                "Un compte de destination est requis pour les virements"
            )

    def __str__(self):
        return f"Transaction {self.numero_transaction} - {self.montant_transaction}€"

    class Meta:
        app_label = "tests"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-date_transaction"]
        indexes = [
            models.Index(fields=["numero_transaction"]),
            models.Index(fields=["compte_source", "date_transaction"]),
            models.Index(fields=["type_transaction", "statut_transaction"]),
        ]


# Modèles de test pour la génération de mutations
class TestProduct(models.Model):
    """Modèle produit pour les tests de génération de mutations."""

    nom_produit = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Nom du produit",
        help_text="Nom unique du produit",
    )
    description_produit = models.TextField(
        blank=True, verbose_name="Description du produit"
    )
    prix_produit = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prix du produit"
    )
    quantite_stock = models.PositiveIntegerField(
        default=0, verbose_name="Quantité en stock"
    )
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")
    date_creation = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    date_modification = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )
    categorie_produit = models.ForeignKey(
        "TestProductCategory",
        on_delete=models.CASCADE,
        related_name="produits_categorie",
        verbose_name="Catégorie du produit",
    )

    @business_method
    def augmenter_stock(self, quantite: int) -> bool:
        """Augmente le stock du produit."""
        if quantite <= 0:
            raise ValueError("La quantité doit être positive")

        self.quantite_stock += quantite
        self.save()
        return True

    @business_method
    def diminuer_stock(self, quantite: int) -> bool:
        """Diminue le stock du produit."""
        if quantite <= 0:
            raise ValueError("La quantité doit être positive")

        if self.quantite_stock < quantite:
            raise ValueError("Stock insuffisant")

        self.quantite_stock -= quantite
        self.save()
        return True

    @business_method
    def calculer_valeur_stock(self) -> float:
        """Calcule la valeur totale du stock."""
        return float(self.prix_produit * self.quantite_stock)

    def clean(self):
        """Validation personnalisée du modèle."""
        if self.prix_produit and self.prix_produit <= 0:
            raise ValidationError("Le prix doit être positif")

    class Meta:
        app_label = "tests"
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["nom_produit"]


class TestProductCategory(models.Model):
    """Modèle catégorie de produit pour les tests."""

    nom_categorie = models.CharField(
        max_length=100, unique=True, verbose_name="Nom de la catégorie"
    )
    description_categorie = models.TextField(
        blank=True, verbose_name="Description de la catégorie"
    )
    parent_categorie = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="sous_categories",
        verbose_name="Catégorie parente",
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Catégorie de produit"
        verbose_name_plural = "Catégories de produits"


class TestOrder(models.Model):
    """Modèle commande pour les tests."""

    numero_commande = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro de commande"
    )
    client_commande = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="commandes_client",
        verbose_name="Client de la commande",
    )
    produits_commande = models.ManyToManyField(
        TestProduct, through="TestOrderItem", verbose_name="Produits de la commande"
    )
    date_commande = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de commande"
    )
    statut_commande = models.CharField(
        max_length=20,
        choices=[
            ("EN_ATTENTE", "En attente"),
            ("CONFIRMEE", "Confirmée"),
            ("EXPEDIEE", "Expédiée"),
            ("LIVREE", "Livrée"),
            ("ANNULEE", "Annulée"),
        ],
        default="EN_ATTENTE",
        verbose_name="Statut de la commande",
    )

    @business_method
    def confirmer_commande(self) -> bool:
        """Confirme la commande."""
        self.statut_commande = "CONFIRMEE"
        self.save()
        return True

    @business_method
    def calculer_total(self) -> float:
        """Calcule le total de la commande."""
        return sum(
            item.quantite_item * item.prix_unitaire
            for item in self.items_commande.all()
        )

    class Meta:
        app_label = "tests"
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"


class TestOrderItem(models.Model):
    """Modèle item de commande pour les tests."""

    commande_item = models.ForeignKey(
        TestOrder,
        on_delete=models.CASCADE,
        related_name="items_commande",
        verbose_name="Commande de l'item",
    )
    produit_item = models.ForeignKey(
        TestProduct, on_delete=models.CASCADE, verbose_name="Produit de l'item"
    )
    quantite_item = models.PositiveIntegerField(verbose_name="Quantité de l'item")
    prix_unitaire = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prix unitaire"
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Item de commande"
        verbose_name_plural = "Items de commande"
        unique_together = ["commande_item", "produit_item"]


class TestFileModel(models.Model):
    """Modèle de test pour les téléchargements de fichiers."""

    nom_fichier = models.CharField(max_length=255, verbose_name="Nom du fichier")
    fichier_telecharge = models.FileField(
        upload_to="test_uploads/", verbose_name="Fichier téléchargé"
    )
    taille_fichier = models.PositiveIntegerField(verbose_name="Taille du fichier")
    type_mime = models.CharField(max_length=100, verbose_name="Type MIME")
    date_telechargement = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de téléchargement"
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Fichier de test"
        verbose_name_plural = "Fichiers de test"


# Test models for type generation
class TestUser(models.Model):
    """Modèle utilisateur pour les tests de génération de types."""

    nom_utilisateur = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nom d'utilisateur",
        help_text="Nom unique de l'utilisateur",
    )
    adresse_email = models.EmailField(
        verbose_name="Adresse e-mail", help_text="Adresse e-mail de l'utilisateur"
    )
    mot_de_passe = models.CharField(max_length=128, verbose_name="Mot de passe")
    date_inscription = models.DateTimeField(
        auto_now_add=True, verbose_name="Date d'inscription"
    )
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")
    age_utilisateur = models.IntegerField(
        null=True, blank=True, verbose_name="Âge de l'utilisateur"
    )
    score_reputation = models.FloatField(
        default=0.0, verbose_name="Score de réputation"
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"


class TestPost(models.Model):
    """Modèle article pour les tests de génération de types."""

    titre_article = models.CharField(max_length=200, verbose_name="Titre de l'article")
    contenu_article = models.TextField(verbose_name="Contenu de l'article")
    auteur_article = models.ForeignKey(
        "TestUser",
        on_delete=models.CASCADE,
        related_name="articles_publies",
        verbose_name="Auteur de l'article",
    )
    tags_associes = models.ManyToManyField(
        "TestTag",
        blank=True,
        related_name="articles_associes",
        verbose_name="Tags associés",
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    date_modification = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )
    est_publie = models.BooleanField(default=False, verbose_name="Est publié")
    nombre_vues = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")

    class Meta:
        app_label = "tests"
        verbose_name = "Article"
        verbose_name_plural = "Articles"


class TestTag(models.Model):
    """Modèle tag pour les tests de génération de types."""

    nom_tag = models.CharField(max_length=50, unique=True, verbose_name="Nom du tag")
    description_tag = models.TextField(blank=True, verbose_name="Description du tag")
    couleur_tag = models.CharField(
        max_length=7, default="#000000", verbose_name="Couleur du tag"
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


# Test models for memory usage
class TestMemoryModel(models.Model):
    """Modèle pour tester l'utilisation mémoire."""

    nom_modele = models.CharField(max_length=200, verbose_name="Nom du modèle")
    donnees_volumineuses = models.TextField(verbose_name="Données volumineuses")
    nombre_entier = models.IntegerField(default=0, verbose_name="Nombre entier")
    donnees_json = models.TextField(default="{}", verbose_name="Données JSON")
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")

    @business_method
    def traitement_intensif(self) -> str:
        """Méthode qui consomme de la mémoire."""
        # Créer des données temporaires volumineuses
        temp_data = ["x" * 1000 for _ in range(100)]
        result = "".join(temp_data)
        return f"Traitement de {len(result)} caractères"

    def __str__(self):
        return self.nom_modele

    class Meta:
        app_label = "tests"
        verbose_name = "Modèle mémoire"
        verbose_name_plural = "Modèles mémoire"


class TestRelatedModel(models.Model):
    """Modèle lié pour tester les relations."""

    modele_parent = models.ForeignKey(
        "TestMemoryModel",
        on_delete=models.CASCADE,
        related_name="modeles_lies",
        verbose_name="Modèle parent",
    )
    nom_relation = models.CharField(max_length=100, verbose_name="Nom de la relation")
    donnees_relation = models.TextField(verbose_name="Données de la relation")

    def __str__(self):
        return self.nom_relation

    class Meta:
        app_label = "tests"
        verbose_name = "Modèle lié"
        verbose_name_plural = "Modèles liés"


# Test models for query benchmarks
class BenchmarkTestAuthor(models.Model):
    """Modèle auteur pour les tests de performance."""

    nom_auteur = models.CharField(max_length=100, verbose_name="Nom de l'auteur")
    prenom_auteur = models.CharField(max_length=100, verbose_name="Prénom de l'auteur")
    email_auteur = models.EmailField(unique=True, verbose_name="E-mail de l'auteur")
    date_naissance = models.DateField(
        null=True, blank=True, verbose_name="Date de naissance"
    )
    biographie_auteur = models.TextField(
        blank=True, verbose_name="Biographie de l'auteur"
    )
    nombre_livres = models.IntegerField(default=0, verbose_name="Nombre de livres")
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")

    @business_method
    def calculer_age(self) -> Optional[int]:
        """Calcule l'âge de l'auteur."""
        if not self.date_naissance:
            return None

        from datetime import date

        today = date.today()
        return today.year - self.date_naissance.year

    def __str__(self):
        return f"{self.prenom_auteur} {self.nom_auteur}"

    class Meta:
        app_label = "tests"
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
        ordering = ["nom_auteur", "prenom_auteur"]
        indexes = [
            models.Index(fields=["email_auteur"]),
            models.Index(fields=["nom_auteur", "prenom_auteur"]),
        ]


class BenchmarkTestBook(models.Model):
    """Modèle livre pour les tests de performance."""

    titre_livre = models.CharField(max_length=200, verbose_name="Titre du livre")
    auteur_livre = models.ForeignKey(
        "BenchmarkTestAuthor",
        on_delete=models.CASCADE,
        related_name="livres_auteur",
        verbose_name="Auteur du livre",
    )
    isbn_livre = models.CharField(
        max_length=13, unique=True, verbose_name="ISBN du livre"
    )
    date_publication = models.DateField(verbose_name="Date de publication")
    nombre_pages = models.IntegerField(verbose_name="Nombre de pages")
    prix_livre = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Prix du livre"
    )
    description_livre = models.TextField(
        blank=True, verbose_name="Description du livre"
    )
    genre_livre = models.CharField(
        max_length=50,
        choices=[
            ("FICTION", "Fiction"),
            ("NON_FICTION", "Non-fiction"),
            ("SCIENCE_FICTION", "Science-fiction"),
            ("ROMANCE", "Romance"),
            ("THRILLER", "Thriller"),
            ("BIOGRAPHIE", "Biographie"),
        ],
        verbose_name="Genre du livre",
    )
    est_disponible = models.BooleanField(default=True, verbose_name="Est disponible")
    note_moyenne = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00, verbose_name="Note moyenne"
    )

    @business_method
    def calculer_age_livre(self) -> int:
        """Calcule l'âge du livre en années."""
        from datetime import date

        today = date.today()
        return today.year - self.date_publication.year

    def __str__(self):
        return self.titre_livre

    class Meta:
        app_label = "tests"
        verbose_name = "Livre"
        verbose_name_plural = "Livres"
        ordering = ["-date_publication"]
        indexes = [
            models.Index(fields=["isbn_livre"]),
            models.Index(fields=["auteur_livre", "date_publication"]),
            models.Index(fields=["genre_livre"]),
            models.Index(fields=["est_disponible"]),
        ]


class BenchmarkTestReview(models.Model):
    """Modèle avis pour les tests de performance."""

    livre_avis = models.ForeignKey(
        "BenchmarkTestBook",
        on_delete=models.CASCADE,
        related_name="avis_livre",
        verbose_name="Livre de l'avis",
    )
    nom_revieweur = models.CharField(max_length=100, verbose_name="Nom du revieweur")
    email_revieweur = models.EmailField(verbose_name="E-mail du revieweur")
    note_avis = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Note de l'avis"
    )
    commentaire_avis = models.TextField(verbose_name="Commentaire de l'avis")
    date_avis = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'avis")
    est_verifie = models.BooleanField(default=False, verbose_name="Est vérifié")

    def __str__(self):
        return f"Avis de {self.nom_revieweur} sur {self.livre_avis.titre_livre}"

    class Meta:
        app_label = "tests"
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ["-date_avis"]
        indexes = [
            models.Index(fields=["livre_avis", "date_avis"]),
            models.Index(fields=["note_avis"]),
            models.Index(fields=["est_verifie"]),
        ]


class TestMediaModel(models.Model):
    """Modèle de test pour les médias."""

    title = models.CharField(max_length=255, verbose_name="Titre")
    image = models.ImageField(upload_to="test_media/", verbose_name="Image")
    thumbnail = models.ImageField(
        upload_to="test_thumbnails/", verbose_name="Miniature", blank=True
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Propriétaire"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        app_label = "tests"


class TestPerformanceModel(models.Model):
    """Modèle pour les tests de performance."""

    name = models.CharField(max_length=100, verbose_name="Nom du test de performance")
    description = models.TextField(blank=True, verbose_name="Description du test")
    execution_time = models.FloatField(
        null=True, blank=True, verbose_name="Temps d'exécution (ms)"
    )
    memory_usage = models.IntegerField(
        null=True, blank=True, verbose_name="Utilisation mémoire (bytes)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        verbose_name = "Test de performance"
        verbose_name_plural = "Tests de performance"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Performance Test: {self.name}"


class TestConcurrencyModel(models.Model):
    """Modèle pour les tests de concurrence."""

    name = models.CharField(max_length=100, verbose_name="Nom du test de concurrence")
    thread_count = models.IntegerField(default=1, verbose_name="Nombre de threads")
    concurrent_operations = models.IntegerField(
        default=1, verbose_name="Opérations concurrentes"
    )
    success_count = models.IntegerField(default=0, verbose_name="Nombre de succès")
    error_count = models.IntegerField(default=0, verbose_name="Nombre d'erreurs")
    average_response_time = models.FloatField(
        null=True, blank=True, verbose_name="Temps de réponse moyen (ms)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        verbose_name = "Test de concurrence"
        verbose_name_plural = "Tests de concurrence"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Concurrency Test: {self.name} ({self.thread_count} threads)"


class TestCacheModel(models.Model):
    """Modèle pour les tests de cache."""

    key = models.CharField(max_length=255, unique=True, verbose_name="Clé de cache")
    value = models.TextField(verbose_name="Valeur")
    ttl = models.IntegerField(
        null=True, blank=True, verbose_name="Durée de vie (secondes)"
    )
    hit_count = models.IntegerField(default=0, verbose_name="Nombre d'accès")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )

    class Meta:
        verbose_name = "Test de cache"
        verbose_name_plural = "Tests de cache"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Cache Test: {self.key}"


class TestSecurityModel(models.Model):
    """Modèle pour les tests de sécurité."""

    test_type = models.CharField(
        max_length=50,
        choices=[
            ("sql_injection", "Injection SQL"),
            ("xss", "Cross-Site Scripting"),
            ("csrf", "Cross-Site Request Forgery"),
            ("auth", "Authentification"),
            ("authz", "Autorisation"),
        ],
        verbose_name="Type de test de sécurité",
    )
    payload = models.TextField(verbose_name="Charge utile du test")
    expected_result = models.CharField(
        max_length=20,
        choices=[
            ("blocked", "Bloqué"),
            ("allowed", "Autorisé"),
            ("error", "Erreur"),
        ],
        verbose_name="Résultat attendu",
    )
    actual_result = models.CharField(
        max_length=20,
        choices=[
            ("blocked", "Bloqué"),
            ("allowed", "Autorisé"),
            ("error", "Erreur"),
        ],
        null=True,
        blank=True,
        verbose_name="Résultat réel",
    )
    is_vulnerable = models.BooleanField(default=False, verbose_name="Vulnérable")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        verbose_name = "Test de sécurité"
        verbose_name_plural = "Tests de sécurité"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Security Test: {self.test_type}"


class TestUserProfile(models.Model):
    """Profil utilisateur pour les tests."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="Utilisateur"
    )
    test_role = models.CharField(
        max_length=50,
        choices=[
            ("admin", "Administrateur"),
            ("user", "Utilisateur"),
            ("guest", "Invité"),
            ("tester", "Testeur"),
        ],
        default="user",
        verbose_name="Rôle de test",
    )
    permissions = models.TextField(default="{}", verbose_name="Permissions de test")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        verbose_name = "Profil utilisateur de test"
        verbose_name_plural = "Profils utilisateur de test"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Test Profile: {self.user.username} ({self.test_role})"


class TestLogEntry(models.Model):
    """Entrée de log pour les tests."""

    test_name = models.CharField(max_length=200, verbose_name="Nom du test")
    test_type = models.CharField(max_length=50, verbose_name="Type de test")
    status = models.CharField(
        max_length=20,
        choices=[
            ("passed", "Réussi"),
            ("failed", "Échoué"),
            ("skipped", "Ignoré"),
            ("error", "Erreur"),
        ],
        verbose_name="Statut",
    )
    duration = models.FloatField(null=True, blank=True, verbose_name="Durée (secondes)")
    error_message = models.TextField(blank=True, verbose_name="Message d'erreur")
    traceback = models.TextField(blank=True, verbose_name="Trace d'erreur")
    metadata = models.TextField(default="{}", verbose_name="Métadonnées")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        verbose_name = "Entrée de log de test"
        verbose_name_plural = "Entrées de log de test"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["test_name", "status"]),
            models.Index(fields=["test_type", "created_at"]),
        ]

    def __str__(self):
        return f"Test Log: {self.test_name} - {self.status}"


# ============================================================================
# CONCURRENT TEST MODELS
# ============================================================================


class TestConcurrentModel(models.Model):
    """Modèle pour tester la concurrence."""

    nom_concurrent = models.CharField(max_length=100, verbose_name="Nom concurrent")
    valeur_compteur = models.IntegerField(default=0, verbose_name="Valeur du compteur")
    donnees_partagees = models.TextField(default="", verbose_name="Données partagées")
    timestamp_creation = models.DateTimeField(
        auto_now_add=True, verbose_name="Timestamp de création"
    )
    thread_id = models.CharField(max_length=50, blank=True, verbose_name="ID du thread")
    est_verrouille = models.BooleanField(default=False, verbose_name="Est verrouillé")

    @business_method
    def incrementer_compteur(self) -> int:
        """Incrémente le compteur de façon thread-safe."""
        from django.db import transaction

        with transaction.atomic():
            # Recharger l'objet pour éviter les conditions de course
            obj = TestConcurrentModel.objects.select_for_update().get(pk=self.pk)
            obj.valeur_compteur += 1
            obj.save()
            return obj.valeur_compteur

    @business_method
    def traitement_long(self) -> str:
        """Simule un traitement long."""
        import time

        time.sleep(0.1)  # Simuler un traitement
        return f"Traitement terminé pour {self.nom_concurrent}"

    def __str__(self):
        return self.nom_concurrent

    class Meta:
        app_label = "tests"
        verbose_name = "Modèle concurrent"
        verbose_name_plural = "Modèles concurrents"


class TestSharedResource(models.Model):
    """Modèle pour tester les ressources partagées."""

    nom_ressource = models.CharField(
        max_length=100, unique=True, verbose_name="Nom de la ressource"
    )
    valeur_partagee = models.IntegerField(default=0, verbose_name="Valeur partagée")
    nombre_acces = models.IntegerField(default=0, verbose_name="Nombre d'accès")
    derniere_modification = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    @business_method
    def acceder_ressource(self) -> Dict[str, Any]:
        """Accède à la ressource de façon thread-safe."""
        from django.db import transaction
        from typing import Dict, Any

        with transaction.atomic():
            obj = TestSharedResource.objects.select_for_update().get(pk=self.pk)
            obj.nombre_acces += 1
            obj.save()
            return {
                "nom": obj.nom_ressource,
                "valeur": obj.valeur_partagee,
                "acces": obj.nombre_acces,
            }

    def __str__(self):
        return self.nom_ressource

    class Meta:
        app_label = "tests"
        verbose_name = "Ressource partagée"
        verbose_name_plural = "Ressources partagées"


# ============================================================================
# SCHEMA GENERATION TEST MODELS
# ============================================================================


class TestCompany(models.Model):
    """Modèle entreprise pour les tests d'intégration."""

    nom_entreprise = models.CharField(
        max_length=200, unique=True, verbose_name="Nom de l'entreprise"
    )
    secteur_activite = models.CharField(
        max_length=100, verbose_name="Secteur d'activité"
    )
    adresse_entreprise = models.TextField(verbose_name="Adresse de l'entreprise")
    telephone_entreprise = models.CharField(
        max_length=20, blank=True, verbose_name="Téléphone de l'entreprise"
    )
    email_entreprise = models.EmailField(verbose_name="E-mail de l'entreprise")
    site_web = models.URLField(blank=True, verbose_name="Site web")
    date_creation = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    est_active = models.BooleanField(default=True, verbose_name="Est active")
    nombre_employes = models.PositiveIntegerField(
        default=0, verbose_name="Nombre d'employés"
    )

    @business_method
    def ajouter_employe(self, nombre: int = 1) -> bool:
        """Ajoute des employés à l'entreprise."""
        if nombre <= 0:
            raise ValueError("Le nombre d'employés doit être positif")

        self.nombre_employes += nombre
        self.save()
        return True

    @business_method
    def calculer_taille_entreprise(self) -> str:
        """Calcule la taille de l'entreprise."""
        if self.nombre_employes < 10:
            return "TPE"
        elif self.nombre_employes < 50:
            return "PME"
        elif self.nombre_employes < 250:
            return "ETI"
        else:
            return "GE"

    class Meta:
        app_label = "tests"
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        ordering = ["nom_entreprise"]


class TestEmployee(models.Model):
    """Modèle employé pour les tests d'intégration."""

    utilisateur_employe = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profil_employe",
        verbose_name="Utilisateur employé",
    )
    entreprise_employe = models.ForeignKey(
        TestCompany,
        on_delete=models.CASCADE,
        related_name="employes_entreprise",
        verbose_name="Entreprise de l'employé",
    )
    poste_employe = models.CharField(max_length=100, verbose_name="Poste de l'employé")
    salaire_employe = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Salaire de l'employé",
    )
    date_embauche = models.DateField(verbose_name="Date d'embauche")
    est_manager = models.BooleanField(default=False, verbose_name="Est manager")
    manager_employe = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="equipe_manager",
        verbose_name="Manager de l'employé",
    )
    competences_employe = models.ManyToManyField(
        "TestSkill",
        blank=True,
        related_name="employes_competences",
        verbose_name="Compétences de l'employé",
    )

    @business_method
    def promouvoir_manager(self) -> bool:
        """Promeut l'employé au rang de manager."""
        self.est_manager = True
        self.save()
        return True

    @business_method
    def calculer_anciennete(self) -> int:
        """Calcule l'ancienneté en années."""
        from datetime import date

        return (date.today() - self.date_embauche).days // 365

    class Meta:
        app_label = "tests"
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        unique_together = ["utilisateur_employe", "entreprise_employe"]


class TestSkill(models.Model):
    """Modèle compétence pour les tests d'intégration."""

    nom_competence = models.CharField(
        max_length=100, unique=True, verbose_name="Nom de la compétence"
    )
    description_competence = models.TextField(
        blank=True, verbose_name="Description de la compétence"
    )
    niveau_requis = models.CharField(
        max_length=20,
        choices=[
            ("DEBUTANT", "Débutant"),
            ("INTERMEDIAIRE", "Intermédiaire"),
            ("AVANCE", "Avancé"),
            ("EXPERT", "Expert"),
        ],
        default="DEBUTANT",
        verbose_name="Niveau requis",
    )
    categorie_competence = models.ForeignKey(
        "TestSkillCategory",
        on_delete=models.CASCADE,
        related_name="competences_categorie",
        verbose_name="Catégorie de la compétence",
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Compétence"
        verbose_name_plural = "Compétences"
        ordering = ["nom_competence"]


class TestSkillCategory(models.Model):
    """Modèle catégorie de compétence pour les tests d'intégration."""

    nom_categorie = models.CharField(
        max_length=100, unique=True, verbose_name="Nom de la catégorie"
    )
    description_categorie = models.TextField(
        blank=True, verbose_name="Description de la catégorie"
    )
    parent_categorie = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="sous_categories",
        verbose_name="Catégorie parente",
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Catégorie de compétence"
        verbose_name_plural = "Catégories de compétences"


class TestProject(models.Model):
    """Modèle projet pour les tests d'intégration."""

    nom_projet = models.CharField(max_length=200, verbose_name="Nom du projet")
    description_projet = models.TextField(verbose_name="Description du projet")
    entreprise_projet = models.ForeignKey(
        TestCompany,
        on_delete=models.CASCADE,
        related_name="projets_entreprise",
        verbose_name="Entreprise du projet",
    )
    chef_projet = models.ForeignKey(
        TestEmployee,
        on_delete=models.CASCADE,
        related_name="projets_diriges",
        verbose_name="Chef de projet",
    )
    equipe_projet = models.ManyToManyField(
        TestEmployee,
        through="TestProjectAssignment",
        related_name="projets_equipe",
        verbose_name="Équipe du projet",
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin_prevue = models.DateField(verbose_name="Date de fin prévue")
    date_fin_reelle = models.DateField(
        null=True, blank=True, verbose_name="Date de fin réelle"
    )
    budget_projet = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Budget du projet"
    )
    statut_projet = models.CharField(
        max_length=20,
        choices=[
            ("PLANIFIE", "Planifié"),
            ("EN_COURS", "En cours"),
            ("SUSPENDU", "Suspendu"),
            ("TERMINE", "Terminé"),
            ("ANNULE", "Annulé"),
        ],
        default="PLANIFIE",
        verbose_name="Statut du projet",
    )

    @business_method
    def demarrer_projet(self) -> bool:
        """Démarre le projet."""
        if self.statut_projet == "PLANIFIE":
            self.statut_projet = "EN_COURS"
            self.save()
            return True
        return False

    @business_method
    def terminer_projet(self) -> bool:
        """Termine le projet."""
        from datetime import date

        if self.statut_projet == "EN_COURS":
            self.statut_projet = "TERMINE"
            self.date_fin_reelle = date.today()
            self.save()
            return True
        return False

    @business_method
    def calculer_duree_reelle(self) -> Optional[int]:
        """Calcule la durée réelle du projet en jours."""
        from typing import Optional

        if self.date_fin_reelle:
            return (self.date_fin_reelle - self.date_debut).days
        return None

    class Meta:
        app_label = "tests"
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ["-date_debut"]


class TestProjectAssignment(models.Model):
    """Modèle affectation de projet pour les tests d'intégration."""

    projet_affectation = models.ForeignKey(
        TestProject,
        on_delete=models.CASCADE,
        related_name="affectations_projet",
        verbose_name="Projet de l'affectation",
    )
    employe_affectation = models.ForeignKey(
        TestEmployee,
        on_delete=models.CASCADE,
        related_name="affectations_employe",
        verbose_name="Employé de l'affectation",
    )
    role_affectation = models.CharField(
        max_length=100, verbose_name="Rôle dans l'affectation"
    )
    pourcentage_temps = models.PositiveIntegerField(
        default=100, verbose_name="Pourcentage de temps"
    )
    date_debut_affectation = models.DateField(
        verbose_name="Date de début d'affectation"
    )
    date_fin_affectation = models.DateField(
        null=True, blank=True, verbose_name="Date de fin d'affectation"
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Affectation de projet"
        verbose_name_plural = "Affectations de projets"
        unique_together = ["projet_affectation", "employe_affectation"]


# ============================================================================
# PERFORMANCE TEST MODELS
# ============================================================================


class PerformanceTestAuthor(models.Model):
    """Modèle auteur pour les tests de performance."""

    name = models.CharField(max_length=100, verbose_name="Nom de l'auteur")
    email = models.EmailField(verbose_name="Email de l'auteur")

    class Meta:
        app_label = "tests"
        verbose_name = "Auteur de test (performance)"
        verbose_name_plural = "Auteurs de test (performance)"


class PerformanceTestBook(models.Model):
    """Modèle livre pour les tests de performance."""

    title = models.CharField(max_length=200, verbose_name="Titre du livre")
    author = models.ForeignKey(
        PerformanceTestAuthor, on_delete=models.CASCADE, verbose_name="Auteur"
    )
    publication_year = models.IntegerField(verbose_name="Année de publication")

    class Meta:
        app_label = "tests"
        verbose_name = "Livre de test (performance)"
        verbose_name_plural = "Livres de test (performance)"


class PerformanceTestReview(models.Model):
    """Modèle avis pour les tests de performance."""

    book = models.ForeignKey(
        PerformanceTestBook, on_delete=models.CASCADE, verbose_name="Livre"
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Critique"
    )
    rating = models.IntegerField(verbose_name="Note")
    comment = models.TextField(verbose_name="Commentaire")

    class Meta:
        app_label = "tests"
        verbose_name = "Avis de test (performance)"
        verbose_name_plural = "Avis de test (performance)"


# ============================================================================
# FIXTURE TEST MODELS (moved from test_data_fixtures.py)
# ============================================================================


class BaseTestModel(models.Model):
    """Modèle de base pour tous les modèles de test."""

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )

    class Meta:
        abstract = True
        app_label = "tests"


class FixtureTestAuthor(BaseTestModel):
    """Modèle d'auteur pour les tests de fixtures."""

    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom de famille")
    email = models.EmailField(unique=True, verbose_name="Adresse e-mail")
    birth_date = models.DateField(
        null=True, blank=True, verbose_name="Date de naissance"
    )
    bio = models.TextField(blank=True, verbose_name="Biographie")
    website = models.URLField(blank=True, verbose_name="Site web")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    nationality = models.CharField(
        max_length=100, blank=True, verbose_name="Nationalité"
    )
    awards_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de prix")

    class Meta:
        verbose_name = "Auteur de test (fixture)"
        verbose_name_plural = "Auteurs de test (fixtures)"
        ordering = ["last_name", "first_name"]
        app_label = "tests"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """Nom complet de l'auteur."""
        return f"{self.first_name} {self.last_name}"


class FixtureTestCategory(BaseTestModel):
    """Modèle de catégorie pour les tests de fixtures."""

    name = models.CharField(
        max_length=100, unique=True, verbose_name="Nom de la catégorie"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Catégorie parente",
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordre de tri")

    class Meta:
        verbose_name = "Catégorie de test (fixture)"
        verbose_name_plural = "Catégories de test (fixtures)"
        ordering = ["sort_order", "name"]
        app_label = "tests"

    def __str__(self):
        return self.name


class FixtureTestPublisher(BaseTestModel):
    """Modèle d'éditeur pour les tests de fixtures."""

    name = models.CharField(
        max_length=200, unique=True, verbose_name="Nom de l'éditeur"
    )
    address = models.TextField(blank=True, verbose_name="Adresse")
    website = models.URLField(blank=True, verbose_name="Site web")
    email = models.EmailField(blank=True, verbose_name="Adresse e-mail")
    founded_year = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Année de fondation"
    )
    country = models.CharField(max_length=100, blank=True, verbose_name="Pays")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Éditeur de test (fixture)"
        verbose_name_plural = "Éditeurs de test (fixtures)"
        ordering = ["name"]
        app_label = "tests"

    def __str__(self):
        return self.name


class FixtureTestBook(BaseTestModel):
    """Modèle de livre pour les tests de fixtures."""

    title = models.CharField(max_length=200, verbose_name="Titre")
    isbn = models.CharField(max_length=13, unique=True, verbose_name="ISBN")
    author = models.ForeignKey(
        FixtureTestAuthor,
        on_delete=models.CASCADE,
        related_name="books",
        verbose_name="Auteur",
    )
    category = models.ForeignKey(
        FixtureTestCategory,
        on_delete=models.CASCADE,
        related_name="books",
        verbose_name="Catégorie",
    )
    publisher = models.ForeignKey(
        FixtureTestPublisher,
        on_delete=models.CASCADE,
        related_name="books",
        verbose_name="Éditeur",
    )
    publication_date = models.DateField(verbose_name="Date de publication")
    pages = models.PositiveIntegerField(verbose_name="Nombre de pages")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix")
    description = models.TextField(blank=True, verbose_name="Description")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    language = models.CharField(max_length=50, default="fr", verbose_name="Langue")
    rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True, verbose_name="Note"
    )

    class Meta:
        verbose_name = "Livre de test (fixture)"
        verbose_name_plural = "Livres de test (fixtures)"
        ordering = ["-publication_date", "title"]
        app_label = "tests"

    def __str__(self):
        return f"{self.title} - {self.author.full_name}"


class FixtureTestReview(BaseTestModel):
    """Modèle d'avis pour les tests de fixtures."""

    book = models.ForeignKey(
        FixtureTestBook,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Livre",
    )
    reviewer_name = models.CharField(max_length=100, verbose_name="Nom du critique")
    reviewer_email = models.EmailField(verbose_name="E-mail du critique")
    rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Note"
    )
    title = models.CharField(max_length=200, verbose_name="Titre de l'avis")
    content = models.TextField(verbose_name="Contenu de l'avis")
    is_verified = models.BooleanField(default=False, verbose_name="Vérifié")
    is_published = models.BooleanField(default=True, verbose_name="Publié")
    helpful_votes = models.PositiveIntegerField(default=0, verbose_name="Votes utiles")

    class Meta:
        verbose_name = "Avis de test (fixture)"
        verbose_name_plural = "Avis de test (fixtures)"
        ordering = ["-created_at"]
        unique_together = ["book", "reviewer_email"]
        app_label = "tests"

    def __str__(self):
        return f"Avis de {self.reviewer_name} sur {self.book.title}"
