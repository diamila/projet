from datetime import timedelta
from openerp import models, fields, api, exceptions

class Course(models.Model):
    _name = 'openacademy.course'

    #required=True le champ ne peut pas être vide, il doit soit avoir une valeur par défaut, soit toujours recevoir une valeur
    name = fields.Char(string="Title", required=True)
    description = fields.Text()
    
    #Many2one:Un simple lien vers un autre objet:
    #Un cours a un utilisateur responsable
    responsible_id = fields.Many2one('res.users', ondelete='set null', string="Responsible", index=True)
    #l'inverse du Many2one course_id
    session_ids = fields.One2many('openacademy.session', 'course_id', string="Sessions")

#un modèle pour les sessions . Une session a un nom, une date de début, une durée et un nombre de siège
class Session(models.Model):
    _name = 'openacademy.session'

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today) #la valeur par défaut start_date comme aujourd'hui 
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    #bouton actives par défaut
    active = fields.Boolean(default=True)
    #Une session a un instructeur  Many2one
    instructor_id = fields.Many2one('res.partner', string="Instructor")
    #Une session est liée à un cours    
    course_id = fields.Many2one('openacademy.course', ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    #La valeur d'un champ calculé dépend généralement des valeurs des autres champs de l'enregistrement
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats: #si c'est vide
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats


    #Le mécanisme "onchange" permet à l'interface client de mettre à jour un formulaire chaque fois que l'utilisateur a renseigné une valeur dans un champ, sans rien enregistrer dans la base de données.
    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message': "The number of available seats may not be negative",
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': "Too many attendees",
                    'message': "Increase seats or remove excess attendees",
                },
            }

    #contrainte qui vérifie que le formateur n'est pas présent dans les participants de sa propre session.
    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError("L'instructeur d'une session ne peut pas être un participant")

    
   
 
     #champ de l'enregistrement contenant la date / heure de fin=calculé à partir de start_dateet duration
    end_date = fields.Date(string="End Date", store=True,
        compute='_get_end_date', inverse='_set_end_date')

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            start = fields.Datetime.from_string(r.start_date)
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = start + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            start_date = fields.Datetime.from_string(r.start_date)
            end_date = fields.Datetime.from_string(r.end_date)
            r.duration = (end_date - start_date).days + 1

    #Les diagrammes de Gantt
    # champ calculé exprimant la durée de la session en heures
    hours = fields.Float(string="Duration in hours",
                         compute='_get_hours', inverse='_set_hours')

    @api.depends('duration')
    def _get_hours(self):
        for r in self:
            r.hours = r.duration * 24

    def _set_hours(self):
        for r in self:
            r.duration = r.hours / 24

    #Ajoutez une vue Graphique dans l'objet Session qui affiche, pour chaque cours, le nombre de participants sous la forme d'un graphique à barres.
    attendees_count = fields.Integer(
        string="Attendees count", compute='_get_attendees_count', store=True)
   
    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    

    #kanban: qui affiche les sessions regroupées par cours (les colonnes sont donc des cours)
    color = fields.Integer()
    
