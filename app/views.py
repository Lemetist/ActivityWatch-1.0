from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponse
from datetime import date, datetime, timedelta
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from .models import Food_Entry
from exlog_app.models import ExerciseLog, Exercise as Exercise_App
from .forms import FoodForm
from django.db.models import Avg, Count
from .forms import FoodFormTheSecond
from .models import Exercise
from .models import WeightLog
from .forms import WeightLogForm
from . import forms
from django.contrib.auth import login, authenticate
import io
import urllib, base64
import matplotlib.pyplot as plt
import json, os, matplotlib
import numpy as np
from django.contrib.auth.decorators import login_required
import csv
from django.templatetags.static import static

def button_class(active_exercise, button):
    if active_exercise == button:
        return 'btn btn-outline-secondary btn-sm active'
    else:
        return 'btn btn-outline-secondary btn-sm'


# Create your views here.
def home(request):
    context = {
        'title': 'Home'
    }
    return render(request, 'app/home.html', context)


def exercises(request, active_exercises=0):
    """
    Отображает список упражнений и соответствующую диаграмму тела.
    """
    if not request.user.is_authenticated:
        return redirect('app:login')

    button_codes = [102, 106, 103, 110, 111, 112, 113, 114, 117, 118, 120, 121, 119, 101, 104]
    classes = {f'button{i+1}_class': button_class(active_exercises, code) for i, code in enumerate(button_codes)}

    # Путь к диаграмме тела
    if active_exercises in (None, 0, -1):
        body_diagram = static('bodyDiagram/bodyDiagram0.png')
    else:
        body_diagram = static(f'bodyDiagram/bodyDiagram{active_exercises}.png')

    # Загрузка данных упражнений
    exercise_list = []
    exercises_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Exercises.json')
    try:
        with open(exercises_file, encoding='utf-8') as f:
            data = json.load(f)
            search = request.GET.get('search', '').strip().lower()
            difficulty = request.GET.get('difficulty', '').strip().lower()
            equipment = request.GET.get('equipment', '').strip().lower()

            # Если есть поисковый запрос или фильтры, всегда показывать упражнения по всем группам и показывать блок с результатами
            if search or difficulty or equipment:
                filtered = data
                active_exercises = -1  # специальный маркер для шаблона: показать только результаты поиска
            elif active_exercises == 100:
                filtered = data
            elif active_exercises == 0:
                filtered = []
            else:
                filtered = [item for item in data if item.get("group_code") == active_exercises]

            def match(ex):
                ok = True
                if search:
                    ok = search in ex.get('name', '').lower() or search in ex.get('description', '').lower()
                if ok and difficulty:
                    ok = ex.get('difficulty', '').lower() == difficulty
                if ok and equipment:
                    ok = ex.get('equipment', '').lower() == equipment
                return ok
            exercise_list = [ex for ex in filtered if match(ex)]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        messages.error(request, f"Ошибка загрузки данных упражнений: {e}", extra_tags='danger')
        exercise_list = []
        data = []

    # Формируем список уникальных групп мышц для фильтрации
    all_groups = set()
    all_group_codes = dict()
    for item in data:
        all_groups.add((item.get("group"), item.get("group_code")))
        all_group_codes[item.get("group")] = item.get("group_code")
    muscle_groups = sorted(list(all_groups), key=lambda x: x[1])
    context = {
        'exercises': exercise_list,
        'title': 'Каталог упражнений',
        'active_exercise': active_exercises,
        'classes': classes,
        'body_diagram': body_diagram,
        'muscle_groups': muscle_groups,
    }
    return render(request, 'app/exercises.html', context)

def foodtracker(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    else:
        # Обработка отправки форм
        if request.method == 'POST' and 'sub_btn_1' in request.POST:
            form_sub = FoodForm(request.POST)
            if form_sub.is_valid():
                # Ensuring calories match description if already in database
                val = True
                if Food_Entry.objects.filter(user=request.user, description=form_sub.cleaned_data['description']).exists():
                    old_entry = Food_Entry.objects.filter(user=request.user, description=form_sub.cleaned_data['description']).first()
                    if old_entry.calories != form_sub.cleaned_data['calories']:
                        messages.error(request, "Ошибка: для одинаковых описаний калорийность должна совпадать!", extra_tags='danger')
                        val = False
                    else:
                        f = Food_Entry(date=form_sub.cleaned_data['date'], description=form_sub.cleaned_data['description'], calories=form_sub.cleaned_data['calories'], user=request.user)
                        f.save()
                # Ensuring calories are 0 or greater
                if form_sub.cleaned_data['calories'] < 0:
                    messages.error(request, "Ошибка: калорий должно быть не меньше 0!", extra_tags='danger')
                    val = False
                if val == True:
                    f = Food_Entry(date=form_sub.cleaned_data['date'], description=form_sub.cleaned_data['description'], calories=form_sub.cleaned_data['calories'], user=request.user)
                    f.save()
                    messages.success(request, "Успешно добавлено: " + form_sub.cleaned_data['description'] + ".", extra_tags='success')
            else:
                messages.error(request, "Ошибка: описание может содержать только буквы, цифры, точки, запятые и скобки!", extra_tags='danger')
        elif request.method == 'POST' and 'sub_btn_2' in request.POST:
            form_sub = FoodFormTheSecond(request.POST, request=request)
            if form_sub.is_valid():
                f = Food_Entry.objects.filter(user=request.user, description=form_sub.cleaned_data['description']).first()
                f.pk = None
                f.date = form_sub.cleaned_data["date"]
                f.save()
                messages.success(request, "Успешно добавлено: " + form_sub.cleaned_data['description'] + ".", extra_tags='success')
        elif request.method == 'POST':
            f = Food_Entry.objects.filter(user=request.user, pk=request.POST['pk']).first()
            Food_Entry.objects.filter(user=request.user, pk=request.POST['pk']).delete()
            if f:
                messages.success(request, "Успешно удалено: " + f.description + ".", extra_tags='success')
            else:
                messages.success(request, "Запись уже удалена.", extra_tags='success')
        # Создание форм
        form = FoodForm()
        form_2 = FoodFormTheSecond(request=request)

        # Получение данных
        entries = Food_Entry.objects.filter(user=request.user).order_by('-date')
        data = {}
        for e in entries:
            if e.date in data:
                data[e.date].append(e)
            else:
                data[e.date] = [e]
        total_calories = {}
        for date in data:
            sum = 0
            for foods in data[date]:
                sum = sum + foods.calories
            total_calories[date] = sum

        # Передача информации
        context = {
            'title': 'Трекер питания',
            'data': data,
            'form': form,
            'form_2': form_2,
            'total_calories': total_calories,
            'today_date': timezone.now().date(),
            'yesterday_date': timezone.now().date() - timedelta(days=1)
        }
        return render(request, 'app/foodtracker.html', context)


def weightlog(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    else:
        form = WeightLogForm()
        context = {
            'title': 'Весовой журнал',
            'weight_logs': WeightLog.objects.filter(user=request.user).order_by('-timestamp'),
            'form': form,
            'savedWeight': False
        }
        if request.method == 'POST':
            form = WeightLogForm(request.POST)
            if form.is_valid():
                w = WeightLog(weight=form.cleaned_data['weight'], user=request.user)
                w.save()
                context['savedWeight'] = True
                return render(request, 'app/weightlog.html', context)
        else:
            return render(request, 'app/weightlog.html', context)

def login_view(request):
    context = {
        'title': 'Вход'
    }
    return render(request, 'app/login.html', context)

def results(request):

    if not request.user.is_authenticated:
        return redirect('app:login')
    else:
        # График веса
        matplotlib.use('Agg')
        plt.close()
        plt.plot([i.timestamp.date().__format__('%-0m-%-d') for i in WeightLog.objects.filter(user=request.user).order_by('timestamp')], [int(i.weight) for i in WeightLog.objects.filter(user=request.user).order_by('timestamp')], marker='o', markersize=5, color='blue')
        plt.xlabel('Дата')
        plt.ylabel('Вес (кг)')

        for i in range(0, len(WeightLog.objects.filter(user=request.user))):
            plt.annotate(int(WeightLog.objects.filter(user=request.user)[i].weight), (WeightLog.objects.filter(user=request.user)[i].timestamp.date().__format__('%-0m-%-d'), int(WeightLog.objects.filter(user=request.user)[i].weight)+2), ha="center")


        fig1 = plt.gcf()
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format='png')
        buf1.seek(0)
        string = base64.b64encode(buf1.read())
        img1 = urllib.parse.quote(string)
        plt.close()

        list = Food_Entry.objects.filter(user=request.user).order_by('date').extra({'_date': 'Date(date)'}).values(
             '_date').annotate(val=Avg('calories'), count=Count('calories'))

        dates = []
        cals = []
        counts = []
        avgCals = 0
        for item in list:
            date = item.get('_date')
            if isinstance(date, str):
                # старый формат (на всякий случай)
                parts = date.split('-')
                dates.append(f"{parts[2]}.{parts[1]}")
            elif hasattr(date, 'strftime'):
                dates.append(date.strftime('%d.%m'))
            else:
                dates.append(str(date))
            cals.append(item.get('val'))
            counts.append(item.get('count'))
            avgCals = avgCals + item.get('val') * item.get('count')
        if len(dates) > 0:
            avgCals = avgCals / len(dates)

        # График калорий
        plt.plot([i for i in dates],
                 [int(j * counts[i]) for i,j in enumerate(cals)],
                 marker='o', markersize=5, color='blue')
        plt.xlabel('Дата')
        plt.ylabel('Потреблено калорий')
        fig2 = plt.gcf()

        for i in range(0, len(dates)):
            plt.annotate(int(cals[i] * counts[i]), (dates[i], cals[i] * counts[i] +2), ha="center")

        buf2 = io.BytesIO()
        fig2.savefig(buf2, format='png')
        buf2.seek(0)
        string = base64.b64encode(buf2.read())
        img2 = urllib.parse.quote(string)
        plt.close()

        ex_names = []
        for i in ExerciseLog.objects.filter(user=request.user):
            for j in Exercise_App.objects.filter(exercise_log=i):
                ex_names.append(j.exercise_name)

        weights = []
        reps = []
        dates = []
        rep_max = []
        for i in ExerciseLog.objects.filter(user=request.user).order_by('date'):
            for j in Exercise_App.objects.filter(exercise_log=i):
                if j.exercise_name == request.GET.get('ex', ''):
                    weights.append(j.exercise_weight)
                    reps.append(j.num_reps)
                    dates.append(i.date)

                    # Epley formula for 1RM calculation
                    rep_max.append(int(j.exercise_weight * (1 + j.num_reps / 30)))

        # График силы
        plt.plot([i.__format__('%-0m-%-d') for i in dates], [i for i in rep_max], marker='o', markersize=5, color='blue')
        plt.title(request.GET.get('ex', 'Выберите упражнение'))
        plt.xlabel('Дата')
        plt.ylabel(request.GET.get('ex', '') + ' (1ПМ)')

        if len(rep_max) > 0:
            plt.ylim(min(rep_max) - 10, max(rep_max) + 10)

        for i in range(0, len(dates)):
            plt.annotate(int(rep_max[i]), (dates[i].__format__('%-0m-%-d'), rep_max[i]+2), ha="center")

        fig3 = plt.gcf()
        buf3 = io.BytesIO()
        fig3.savefig(buf3, format='png')
        buf3.seek(0)
        string = base64.b64encode(buf3.read())
        img3 = urllib.parse.quote(string)
        plt.close()

        weightSum = 0
        for i in WeightLog.objects.filter(user=request.user):
            weightSum += int(i.weight)

        if len(WeightLog.objects.filter(user=request.user)) > 0:
            average = weightSum / (len(WeightLog.objects.filter(user=request.user)))
            average = '%.2f' % average
            change = int(WeightLog.objects.filter(user=request.user)[len(WeightLog.objects.filter(user=request.user)) - 1].weight) - int(WeightLog.objects.filter(user=request.user)[0].weight)
        else:
            average = '--'
            change = '--'

        if len(rep_max) > 0:
            if (rep_max[0] != 0):
                str_change = ((rep_max[len(rep_max) - 1] - rep_max[0]) / rep_max[0]) * 100
                str_change = '%.2f' % str_change
            else:
                str_change = "Inf"
        else:
            str_change = '--'

        context = {
            'title': 'Результаты',
            'img1': img1,
            'img2': img2,
            'img3': img3,
            'change': change,
            'average': average,
            'ex_names': np.unique(np.array(ex_names)),
            'str_change': str_change,
            'avg_cals': avgCals,
            'min_weight': min([int(i.weight) for i in WeightLog.objects.filter(user=request.user)]) if WeightLog.objects.filter(user=request.user).exists() else '--',
            'max_weight': max([int(i.weight) for i in WeightLog.objects.filter(user=request.user)]) if WeightLog.objects.filter(user=request.user).exists() else '--',
            'min_cals': min([int(j*counts[i]) for i,j in enumerate(cals)]) if len(cals) > 0 else '--',
            'max_cals': max([int(j*counts[i]) for i,j in enumerate(cals)]) if len(cals) > 0 else '--',
        }
        return render(request, 'app/results.html', context)


def signup(request):
    if request.user.is_authenticated:
        return redirect('app:home')
    else:
        if request.method == "POST":
            form = forms.UserRegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('app:login')
        else:
            form = forms.UserRegistrationForm()

        context = {
            'title': 'Регистрация',
            'form': form
        }
        return render(request, 'app/signup.html', context)


def logout_user(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect('app:home')

@login_required
def export_data_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fittrack_data.csv"'
    writer = csv.writer(response)
    writer.writerow(['Тип', 'Дата/Время', 'Описание', 'Значение', 'Калории'])
    # Вес
    for w in WeightLog.objects.filter(user=request.user):
        writer.writerow(['Вес', w.timestamp, '', w.weight, ''])
    # Питание
    for f in Food_Entry.objects.filter(user=request.user):
        writer.writerow(['Питание', f.date, f.description, '', f.calories])
    # Упражнения
    for log in ExerciseLog.objects.filter(user=request.user):
        for ex in Exercise_App.objects.filter(exercise_log=log):
            writer.writerow(['Упражнение', log.date, ex.exercise_name, ex.exercise_weight, ''])
    return response

@login_required
def export_data_json(request):
    data = {
        'weight': list(WeightLog.objects.filter(user=request.user).values()),
        'food': list(Food_Entry.objects.filter(user=request.user).values()),
        'exercises': [
            {
                'date': log.date,
                'exercises': list(Exercise_App.objects.filter(exercise_log=log).values())
            } for log in ExerciseLog.objects.filter(user=request.user)
        ]
    }
    response = HttpResponse(json.dumps(data, ensure_ascii=False, default=str), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="fittrack_data.json"'
    return response
