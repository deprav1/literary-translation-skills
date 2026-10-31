"""Describe both stochastic realizations without selecting a winning sample."""
from __future__ import annotations

from run_budget_trial import BASE, read
from repeat_budget_trial import REPEAT


def main():
    first = BASE/'results'; second = REPEAT/'results'
    old = read(first/'scored.json'); new = read(second/'scored.json')
    old_gates = read(first/'economic-gates.json'); new_gates = read(second/'economic-gates.json')
    stability = read(second/'stability.json'); record = read(second/'record.json')
    fbrief = old['comparisons']['terra_brief_vs_plain']; sbrief = new['comparisons']['terra_brief_vs_plain']
    wording = ('Направление предварительного выигрыша Terra+бриф повторилось.' if fbrief['net'] > 0 and sbrief['net'] > 0
               else 'Предварительный выигрыш Terra+бриф не повторился с тем же положительным направлением.')
    text = f'''# Второй прогон Terra/Luna: устойчивость результата

31 октября 2026. **{wording}** Это сравнение двух реализаций на тех же 30 development-отрывках, а не новая подтверждающая выборка.

## Что повторено

Заново получены Sol-бриф, восемь первых переводов Terra/Luna и Sol-ориентир; все аудиты и операционные маршруты выполнены новыми сессиями. Модели, medium reasoning, английский источник/контекст, инструкции, примеры, схемы и пороги сохранены. Старые русские ответы, бриф и замечания не подавались во второй прогон. Порядок кандидатов, источников и A/B у аудиторов изменён заранее зафиксированными seeds.

Во втором прогоне **{record['model_calls']} модельных вызовов**. Сессии не пересекаются ни друг с другом, ни с первым прогоном. Первые полные ответы сохранены, ручного переписывания и best-of нет. Исправления после операционных проверок учитываются как отдельные оплачиваемые этапы.

[План повторения](PLAN.md) · [Предварительная фиксация](preregistration.json) · [Первый прогон](../RESULTS.md) · [Запись второго прогона](results/record.json).

## Навыки против простого запроса той же модели

В ячейках: лучше / хуже / ничья. Каждая строка относится к 30 одним и тем же источникам. Разные роли модельного аудита не являются независимой человеческой панелью.

| Модель и профиль | Первый прогон | Второй прогон | Net: первый → второй |
|---|---|---|---|
'''
    labels = {'guard': 'короткая самопроверка', 'brief': 'самопроверка + бриф', 'memory': 'бриф + микро-примеры'}
    for family in ['terra', 'luna']:
        for arm in ['guard', 'brief', 'memory']:
            key = family+'_'+arm+'_vs_plain'; a = old['comparisons'][key]; b = new['comparisons'][key]
            text += f"| {family.title()} · {labels[arm]} | {a['wins']} / {a['losses']} / {a['ties']} | {b['wins']} / {b['losses']} / {b['ties']} | {a['net']:+d} → {b['net']:+d} |\n"
    text += '''
Это описательные решения модельного проверяющего, не проценты литературного качества. При повторении менялись и генерации, и модельные аудиты, и порядок показа, поэтому нельзя отнести всякую разницу только к переводчику или только к skill.

## Качество и стоимость профилей

Quality signal и cost cap — исходные внутренние критерии пилота. Их повторение не является подтверждением на новых книгах.

| Профиль | Сигнал качества: первый / второй | Ценовой допуск: первый / второй |
|---|---|---|
'''
    yes = lambda value: 'да' if value else 'нет'
    for family in ['terra', 'luna']:
        for arm in ['guard', 'brief', 'memory']:
            a = old['model_results'][family+'_'+arm]['pilot']; b = new['model_results'][family+'_'+arm]['pilot']
            text += f"| {family.title()} · {labels[arm]} | {yes(a['quality_signal'])} / {yes(b['quality_signal'])} | {yes(a['cost_cap_pass'])} / {yes(b['cost_cap_pass'])} |\n"
    text += '''
Каждый прогон оплачивает свой новый planner целиком для своего объёма; цена не делится между конкурирующими профилями. Для стоимости использован один фиксированный официальный снимок Standard API от 30 октября, чтобы сравнение не зависело от смены тарифа. Это API-эквивалент по токенам, не фактический счёт подписки. Реальные cache-adjusted суммы сохранены отдельно.

## Полные маршруты с аудитом и исправлениями

| Маршрут | Выбран в первом / втором | Полная холодная цена: первый / второй | Экономия против своего Sol: первый / второй | Проигрыши своему Sol: первый / второй |
|---|---|---|---|---|
'''
    for family in ['terra', 'luna']:
        a = read(first/('route-'+family+'.json')); b = read(second/('route-'+family+'.json'))
        ac = a['accounting']['cold']['usd_equivalent']; bc = b['accounting']['cold']['usd_equivalent']
        text += (f"| {family.title()} | `{a['selected']}` / `{b['selected']}` | ${ac:.5f} / ${bc:.5f} | "
                 f"{old_gates[family]['cold_saving_fraction']*100:.1f}% / {new_gates[family]['cold_saving_fraction']*100:.1f}% | "
                 f"{old_gates[family]['prose_losses']}/30 / {new_gates[family]['prose_losses']}/30 |\n")
    a = read(first/'route-anchor.json')['accounting']['cold']['usd_equivalent']
    b = read(second/'route-anchor.json')['accounting']['cold']['usd_equivalent']
    text += f'\nОдинаково проверенный Sol-ориентир: **${a:.5f}** в первом прогоне и **${b:.5f}** во втором.\n'
    text += '\n| Маршрут | Экономический gate: первый / второй |\n|---|---|\n'
    for family in ['terra', 'luna']:
        text += f"| {family.title()} | {yes(old_gates[family]['development_economic_gate'])} / {yes(new_gates[family]['development_economic_gate'])} |\n"
    text += '''
Измеренный research-only аудит отделён от эксплуатационной цены. Стоимость каждой конкретной схемы включает её translator, полный planner, если он используется, свой онлайн-аудит, реальные эскалации и повторные проверки. «Принят моделью» означает только прохождение операционных flags; retained-error veto сохраняется и может блокировать положительный вывод.

## Что устойчиво, а что нет

Публикуются обе реализации. Даже положительный второй результат не превращает неудачный первый в доказанную эффективность. Мы не выбираем лучшие переводы, бриф или маршрут из двух запусков. Суммарно прочитано 60 реализаций источников, но независимых исходных отрывков **30**, произведений **3**, авторов **2**.

Сравнение [брифов и глоссариев](results/brief-overlap.json) сделано после генераций только для диагностики. Ни один бриф не отобран для улучшения другого прогона. Отдельные [нормализованные метрики](results/quality-metrics.json) сохраняют ошибки покрытия и критические затронутые фрагменты без двойного подсчёта одной потери.

Модельные суждения могут ошибаться и быть коррелированными; Sol-ориентир не золотой эталон и не человеческая редактура. Источники публичны и могли присутствовать в обучении. Два повторения одной development-выборки не устанавливают качество на неизвестной книге или полезность для всех жанров.

## Внедрение

Новые переводческие defaults и подтверждённые литературные навыки по этим двум прогонам не активируются. Для подтверждения нужны новые произведения, связные главы, проверка амортизации общего брифа и двуязычный редактор на спорных/крупных ошибках. Первый прогон, его выводы и опрос на промосайте сохранены без изменений.

## Воспроизведение по артефактам

- [Параллельная сводка](results/stability.json).
- [Все решения второго прогона](results/scored.json), [экономические gate](results/economic-gates.json), [quality veto](results/quality-cost-verdict.json).
- [Цены и полный список вызовов](results/record.json), [расходы исследования](results/research-cost.json).
- [Права на источники и производные материалы](../LICENSE.md).

```sh
python scripts/verify_budget_repeat.py --published
python scripts/validate.py
python -m unittest discover -s tests -v
```

Проверки воспроизводят учёт и подтверждают файлы/изоляцию сессий; они не заменяют литературную экспертизу. В опубликованных артефактах нет приватных путей, составных промптов, сырых CLI-логов или полных произведений.
'''
    (REPEAT/'RESULTS.md').write_text(text, encoding='utf8', newline='\n')
    print('Wrote side-by-side report; first realization unchanged')


if __name__ == '__main__':
    main()
