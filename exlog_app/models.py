# models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import RegexValidator


class ExerciseLog(models.Model) :
    """
    Модель журнала упражнений.

    Атрибуты:
        user (User): Пользователь, связанный с журналом.
        date (date): Дата записи журнала.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    def __str__(self) :
        """
        Возвращает строковое представление журнала.
        """
        return str(self.user) + "\t" + str(self.date)

    def get_absolute_url(self) :
        """
        Возвращает абсолютный URL для просмотра журнала.
        """
        return reverse('exlog-detail', kwargs={'pk' : self.pk})


class Exercise(models.Model) :
    """
    Модель упражнения.

    Атрибуты:
        exercise_log (ExerciseLog): Журнал, связанный с упражнением.
        exercise_name (str): Название упражнения.
        num_sets (int): Количество подходов.
        num_reps (int): Количество повторений.
        exercise_weight (int): Вес для упражнения.
    """
    exercise_log = models.ForeignKey(ExerciseLog, on_delete=models.CASCADE)
    alpha_num_dash = RegexValidator(r'^[0-9a-zA-Z\-\s]*$', 'Only alphanumeric characters and dashes are allowed.')
    exercise_name = models.CharField(max_length=32, validators=[alpha_num_dash])
    num_sets = models.PositiveIntegerField()
    num_reps = models.PositiveIntegerField()
    exercise_weight = models.PositiveIntegerField()

    def __str__(self) :
        """
        Возвращает строковое представление упражнения.
        """
        return str(self.exercise_log) + "\t" + str(self.exercise_name) + "\t" + str(self.num_sets) + "x" + str(
            self.num_reps) + "\t" + str(self.exercise_weight)

    def get_absolute_url(self) :
        """
        Возвращает абсолютный URL для просмотра журнала, связанного с упражнением.
        """
        return reverse('exlog-detail', kwargs={'pk' : self.exercise_log.id})