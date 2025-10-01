"""
Test models for integration tests.
"""

from django.db import models
from django.contrib.auth.models import User
from rail_django_graphql.decorators import business_logic, mutation


class TestCompany(models.Model):
    """Test company model for integration tests."""
    name = models.CharField(max_length=200, verbose_name="Nom de l'entreprise")
    description = models.TextField(blank=True, verbose_name="Description")
    founded_date = models.DateField(null=True, blank=True, verbose_name="Date de fondation")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    employee_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'employés")
    
    class Meta:
        verbose_name = "Entreprise de test"
        verbose_name_plural = "Entreprises de test"
    
    def __str__(self):
        return self.name
    
    @business_logic(category="company_management")
    def activate_company(self, reason="Manual activation"):
        """Activate the company."""
        self.is_active = True
        self.save()
        return {"status": "activated", "reason": reason}
    
    @mutation(description="Deactivate company")
    def deactivate_company(self, reason="Manual deactivation"):
        """Deactivate the company."""
        self.is_active = False
        self.save()
        return {"status": "deactivated", "reason": reason}


class TestSkillCategory(models.Model):
    """Test skill category model."""
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    
    class Meta:
        verbose_name = "Catégorie de compétence"
        verbose_name_plural = "Catégories de compétences"
    
    def __str__(self):
        return self.name


class TestSkill(models.Model):
    """Test skill model."""
    name = models.CharField(max_length=100, verbose_name="Nom de la compétence")
    category = models.ForeignKey(TestSkillCategory, on_delete=models.CASCADE, verbose_name="Catégorie")
    level_required = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Débutant'),
            ('intermediate', 'Intermédiaire'),
            ('advanced', 'Avancé'),
            ('expert', 'Expert')
        ],
        default='beginner',
        verbose_name="Niveau requis"
    )
    
    class Meta:
        verbose_name = "Compétence"
        verbose_name_plural = "Compétences"
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


class TestEmployee(models.Model):
    """Test employee model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    company = models.ForeignKey(TestCompany, on_delete=models.CASCADE, verbose_name="Entreprise")
    skills = models.ManyToManyField(TestSkill, blank=True, verbose_name="Compétences")
    hire_date = models.DateField(verbose_name="Date d'embauche")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire")
    is_manager = models.BooleanField(default=False, verbose_name="Manager")
    
    class Meta:
        verbose_name = "Employé de test"
        verbose_name_plural = "Employés de test"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name}"
    
    @business_logic(category="employee_management", requires_permission="can_promote_employee")
    def promote_to_manager(self, effective_date=None):
        """Promote employee to manager."""
        self.is_manager = True
        self.save()
        return {"status": "promoted", "effective_date": effective_date}


class TestProject(models.Model):
    """Test project model."""
    name = models.CharField(max_length=200, verbose_name="Nom du projet")
    description = models.TextField(verbose_name="Description")
    company = models.ForeignKey(TestCompany, on_delete=models.CASCADE, verbose_name="Entreprise")
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Budget")
    status = models.CharField(
        max_length=20,
        choices=[
            ('planning', 'Planification'),
            ('active', 'Actif'),
            ('on_hold', 'En attente'),
            ('completed', 'Terminé'),
            ('cancelled', 'Annulé')
        ],
        default='planning',
        verbose_name="Statut"
    )
    
    class Meta:
        verbose_name = "Projet de test"
        verbose_name_plural = "Projets de test"
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"
    
    @business_logic(category="project_management")
    def start_project(self, start_date=None):
        """Start the project."""
        self.status = 'active'
        if start_date:
            self.start_date = start_date
        self.save()
        return {"status": "started", "start_date": self.start_date}
    
    @business_logic(category="project_management")
    def complete_project(self, end_date=None):
        """Complete the project."""
        self.status = 'completed'
        if end_date:
            self.end_date = end_date
        self.save()
        return {"status": "completed", "end_date": self.end_date}


class TestProjectAssignment(models.Model):
    """Test project assignment model."""
    project = models.ForeignKey(TestProject, on_delete=models.CASCADE, verbose_name="Projet")
    employee = models.ForeignKey(TestEmployee, on_delete=models.CASCADE, verbose_name="Employé")
    role = models.CharField(max_length=100, verbose_name="Rôle")
    assigned_date = models.DateField(verbose_name="Date d'assignation")
    hours_allocated = models.PositiveIntegerField(verbose_name="Heures allouées")
    
    class Meta:
        verbose_name = "Assignation de projet"
        verbose_name_plural = "Assignations de projets"
        unique_together = ['project', 'employee']
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.project.name} ({self.role})"