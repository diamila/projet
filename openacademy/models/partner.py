from openerp import fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    #heritage
    # Ajoutez une nouvelle colonne au modèle res.partner, par défaut les partenaires ne sont pas
    # instructeurs
    instructor = fields.Boolean("Instructor", default=False)

    session_ids = fields.Many2many('openacademy.session',
        string="Attended Sessions", readonly=True)

