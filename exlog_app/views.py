from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django import forms
from django.contrib import messages
from django.http import *
from .models import ExerciseLog, Exercise

def home(request):
    """
    Отображает главную страницу с журналами упражнений пользователя.

    Если пользователь не авторизован, перенаправляет на страницу входа.
    Если у пользователя нет журналов, отображает страницу с предложением начать.
    В противном случае отображает список всех журналов упражнений.

    Аргументы:
        request: HTTP-запрос.

    Возвращает:
        HTTP-ответ с соответствующим шаблоном.
    """
    if not request.user.is_authenticated:
        return redirect('app:login')
    else:
        context = {
            'exercise_logs': ExerciseLog.objects.filter(user=request.user.id).order_by('-date', '-id'),
            'exercises': Exercise.objects.all(),
            'title': 'Exercise Log',
            'user_id': request.user.id,
        }

        if not context['exercise_logs'].count():
            return render(request, 'exlog_app/get_started.html')

        return render(request, 'exlog_app/home.html', context)

def add_from_recommender(request, exercise_name):
    """
    Добавляет упражнение в журнал за текущий день.

    Если журнала за текущий день нет, создаёт его. Затем добавляет упражнение
    с нулевыми значениями подходов, повторений и веса.

    Аргументы:
        request: HTTP-запрос.
        exercise_name: Название упражнения.

    Возвращает:
        Перенаправление на предыдущую страницу.
    """
    today_log = None
    try:
        exlog_count = ExerciseLog.objects.filter(user=request.user.id, date=datetime.date.today()).count()
        if exlog_count == 0:
            today_log = ExerciseLog.objects.create(
                user=request.user,
                date=datetime.date.today(),
            )
        else:
            today_log = ExerciseLog.objects.filter(user=request.user.id, date=datetime.date.today())[exlog_count - 1]
    except Exception as e:
        print('ERROR', e)

    Exercise.objects.create(
        exercise_log=today_log,
        exercise_name=exercise_name,
        num_sets=0,
        num_reps=0,
        exercise_weight=0,
    )

    messages.success(request, "Упражнение успешно добавлено в сегодняшний журнал тренировок!!", extra_tags='success')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

class ExlogDetailView(DetailView):
    """
    Отображает детальную информацию о журнале упражнений.

    Атрибуты:
        model: Модель, связанная с представлением.
        context_object_name: Имя объекта в контексте.
    """
    model = ExerciseLog
    context_object_name = "exlog"

    def get_context_data(self, **kwargs):
        """
        Добавляет список упражнений, связанных с журналом, в контекст.

        Возвращает:
            Обновлённый контекст.
        """
        context = super().get_context_data(**kwargs)
        context['exercises'] = Exercise.objects.filter(exercise_log=self.object).iterator()
        return context

class DateInput(forms.DateInput):
    """
    Виджет для выбора даты.
    """
    input_type = 'date'

class ExlogCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания нового журнала упражнений.

    Атрибуты:
        model: Модель, связанная с представлением.
        fields: Поля, отображаемые в форме.
    """
    model = ExerciseLog
    fields = ['date']

    def get_form(self):
        """
        Настраивает форму для выбора даты.

        Возвращает:
            Настроенная форма.
        """
        form = super(ExlogCreateView, self).get_form()
        initial_base = self.get_initial()
        initial_base['date'] = timezone.now()
        form.initial = initial_base
        form.fields['date'].widget = DateInput()
        return form

    def form_valid(self, form):
        """
        Устанавливает текущего пользователя как владельца журнала.

        Возвращает:
            Результат вызова родительского метода.
        """
        form.instance.user = self.request.user
        messages.success(self.request, "Журнал тренировок успешно добавлен!", extra_tags='success')
        return super().form_valid(form)

class ExlogUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Представление для обновления существующего журнала упражнений.

    Атрибуты:
        model: Модель, связанная с представлением.
        fields: Поля, отображаемые в форме.
    """
    model = ExerciseLog
    fields = ['date']

    def get_form(self):
        """
        Настраивает форму для выбора даты.

        Возвращает:
            Настроенная форма.
        """
        form = super(ExlogUpdateView, self).get_form()
        initial_base = self.get_initial()
        initial_base['date'] = timezone.now()
        form.initial = initial_base
        form.fields['date'].widget = DateInput()
        return form

    def form_valid(self, form):
        """
        Устанавливает текущего пользователя как владельца журнала.

        Возвращает:
            Результат вызова родительского метода.
        """
        form.instance.user = self.request.user
        messages.success(self.request, "Журнал тренировок успешно обновлён!", extra_tags='success')
        return super().form_valid(form)

    def test_func(self):
        """
        Проверяет, является ли текущий пользователь владельцем журнала.

        Возвращает:
            True, если пользователь является владельцем, иначе False.
        """
        exlog = self.get_object()
        if self.request.user == exlog.user:
            return True
        return False

class ExlogDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Представление для удаления журнала упражнений.

    Атрибуты:
        model: Модель, связанная с представлением.
        context_object_name: Имя объекта в контексте.
        success_url: URL для перенаправления после успешного удаления.
    """
    model = ExerciseLog
    context_object_name = "exlog"
    success_url = '/exlog/'

    def test_func(self):
        """
        Проверяет, является ли текущий пользователь владельцем журнала.

        Возвращает:
            True, если пользователь является владельцем, иначе False.
        """
        exlog = self.get_object()
        if self.request.user == exlog.user:
            if self.request.method == 'POST':
                messages.success(self.request, "Журнал тренировок успешно удалён!", extra_tags='success')
            return True
        return False

class ExerciseCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для добавления нового упражнения в журнал.

    Атрибуты:
        model: Модель, связанная с представлением.
        fields: Поля, отображаемые в форме.
    """
    model = Exercise
    fields = ['exercise_name', 'num_sets', 'num_reps', 'exercise_weight']

    def form_valid(self, form):
        """
        Устанавливает текущий журнал для упражнения.

        Возвращает:
            Результат вызова родительского метода.
        """
        form.instance.exercise_log = ExerciseLog.objects.get(id=self.kwargs['pk'])
        messages.success(self.request, "Упражнение успешно добавлено!", extra_tags='success')
        return super().form_valid(form)

class ExerciseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Представление для обновления существующего упражнения.

    Атрибуты:
        model: Модель, связанная с представлением.
        fields: Поля, отображаемые в форме.
    """
    model = Exercise
    fields = ['num_sets', 'num_reps', 'exercise_weight']

    def form_valid(self, form):
        """
        Устанавливает текущего пользователя как владельца упражнения.

        Возвращает:
            Результат вызова родительского метода.
        """
        form.instance.user = self.request.user
        messages.success(self.request, "Упражнение успешно обновлено!", extra_tags='success')
        return super().form_valid(form)

    def test_func(self):
        """
        Проверяет, является ли текущий пользователь владельцем журнала упражнения.

        Возвращает:
            True, если пользователь является владельцем, иначе False.
        """
        exlog = self.get_object()
        if self.request.user == exlog.exercise_log.user:
            return True
        return False

class ExerciseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Представление для удаления упражнения.

    Атрибуты:
        model: Модель, связанная с представлением.
    """
    model = Exercise

    def test_func(self):
        """
        Проверяет, является ли текущий пользователь владельцем журнала упражнения.

        Возвращает:
            True, если пользователь является владельцем, иначе False.
        """
        exlog = self.get_object()
        if self.request.user == exlog.exercise_log.user:
            if self.request.method == 'POST':
                messages.success(self.request, "Упражнение успешно удалено!", extra_tags='success')
            return True
        return False

    def get_success_url(self):
        """
        Возвращает URL для перенаправления после успешного удаления.

        Возвращает:
            URL для перенаправления.
        """
        return '/exlog/log/' + str(self.get_object().exercise_log.id)